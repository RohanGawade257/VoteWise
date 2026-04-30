"""
RAG Service — Lightweight local markdown-based retrieval.
No vector DB required for MVP.
"""
import os
import re
from typing import List, Tuple
from app.utils.logging import get_logger

logger = get_logger("rag_service")

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'knowledge')

# Official source URLs for each knowledge file
FILE_METADATA = {
    "election_process.md":      {"title": "Indian Election Process",    "url": "https://eci.gov.in",                          "type": "official"},
    "first_time_voter.md":      {"title": "First-Time Voter Guide",    "url": "https://voters.eci.gov.in",                  "type": "official"},
    "timeline.md":              {"title": "Election Timeline",          "url": "https://eci.gov.in",                          "type": "official"},
    "politics_basics.md":       {"title": "Politics Basics",            "url": "https://eci.gov.in",                          "type": "rag"},
    "party_directory_notes.md": {"title": "Party Directory Notes",     "url": "https://eci.gov.in/political-parties/",       "type": "official"},
    "official_sources.md":      {"title": "Official Sources Reference", "url": "https://eci.gov.in",                          "type": "official"},
}

# Confidence thresholds (sum of content_overlap + heading_bonus)
_CONFIDENCE_HIGH   = 1.0   # Strong heading + keyword match
_CONFIDENCE_MEDIUM = 0.4   # Relevant match
_CONFIDENCE_LOW    = 0.15  # Weak match (still injected, but flagged)
_CONFIDENCE_NONE   = 0.0   # Below this → no context injected

# Hard minimum: chunks below this score are discarded entirely
_MIN_SCORE = 0.12

# Max chunks injected into prompt (keeps context window tight)
_MAX_TOP_K = 3

# Civic domain keywords — used to detect out-of-scope queries
_CIVIC_SCOPE_WORDS = {
    "vote", "voter", "election", "evm", "vvpat", "nota", "ballot", "eci",
    "polling", "constituency", "electoral", "registration", "register",
    "party", "parliament", "democracy", "constitution", "manifesto",
    "candidate", "booth", "counting", "result", "coalition", "mcc",
    "lok sabha", "vidhan sabha", "rajya sabha", "form 6", "epic",
    "chief minister", "prime minister", "governor", "opposition",
}

# Loaded at startup — list of (chunk_text, filename, heading)
_chunks: List[Tuple[str, str, str]] = []


def _chunk_markdown(text: str, filename: str) -> List[Tuple[str, str, str]]:
    """Split markdown by headings into chunks."""
    chunks = []
    current_heading = "Introduction"
    current_lines: List[str] = []

    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                chunks.append((" ".join(current_lines).strip(), filename, current_heading))
                current_lines = []
            current_heading = line.lstrip("#").strip()
        else:
            stripped = line.strip()
            if stripped:
                current_lines.append(stripped)

    if current_lines:
        chunks.append((" ".join(current_lines).strip(), filename, current_heading))
    return chunks


def load_knowledge():
    """Called at startup. Loads and chunks all markdown files."""
    global _chunks
    _chunks = []
    if not os.path.isdir(KNOWLEDGE_DIR):
        logger.warning(f"Knowledge directory not found: {KNOWLEDGE_DIR}")
        return
    for fname in os.listdir(KNOWLEDGE_DIR):
        if fname.endswith(".md"):
            path = os.path.join(KNOWLEDGE_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                file_chunks = _chunk_markdown(text, fname)
                _chunks.extend(file_chunks)
                logger.info(f"Loaded {len(file_chunks)} chunks from {fname}")
            except Exception as e:
                logger.error(f"Failed to load {fname}: {e}")
    logger.info(f"RAG ready: {len(_chunks)} total chunks from {KNOWLEDGE_DIR}")


def _score_chunk(chunk_text: str, heading: str, query: str) -> float:
    """
    Keyword overlap scoring with heading bonus.
    Returns a float score where higher = better match.
    """
    stop_words = {
        "i", "am", "is", "are", "the", "a", "an", "and", "or", "to",
        "do", "how", "what", "in", "for", "of", "my", "me", "can",
        "you", "your", "this", "that", "it", "be", "was", "at", "as",
        "with", "on", "by", "from", "like", "about",
    }
    query_words = set(re.findall(r'\w+', query.lower())) - stop_words
    if not query_words:
        return 0.0

    chunk_words  = set(re.findall(r'\w+', chunk_text.lower()))
    heading_words = set(re.findall(r'\w+', heading.lower()))

    content_overlap = len(query_words & chunk_words)  / len(query_words)
    heading_overlap = len(query_words & heading_words) / max(len(query_words), 1)

    # Extra bonus for exact multi-word heading match in query
    heading_lower = heading.lower()
    query_lower   = query.lower()
    exact_bonus   = 0.3 if heading_lower in query_lower or query_lower in heading_lower else 0.0

    return content_overlap + (heading_overlap * 0.5) + exact_bonus


def get_confidence(top_score: float) -> str:
    """
    Map a numeric RAG score to a confidence tier.

    high   (>= 1.0): Strong heading + keyword match — answer with confidence.
    medium (>= 0.4): Relevant but partial match — answer with mild caveat.
    low    (>= 0.15): Weak match — ask for clarification or caveat heavily.
    none   (< 0.15): No useful match — do not attempt a RAG answer.
    """
    if top_score >= _CONFIDENCE_HIGH:
        return "high"
    if top_score >= _CONFIDENCE_MEDIUM:
        return "medium"
    if top_score >= _CONFIDENCE_LOW:
        return "low"
    return "none"


def is_in_civic_scope(query: str) -> bool:
    """
    Quick heuristic: does the query contain at least one civic/election keyword?
    Used to detect clearly out-of-scope queries before RAG retrieval.
    """
    lower = query.lower()
    return any(kw in lower for kw in _CIVIC_SCOPE_WORDS)


def retrieve(query: str, top_k: int = _MAX_TOP_K) -> List[dict]:
    """
    Retrieve top-k most relevant chunks for the query.

    - Caps at _MAX_TOP_K (3) regardless of caller argument.
    - Discards chunks below _MIN_SCORE.
    - Attaches a confidence tier to each result.
    """
    effective_k = min(top_k, _MAX_TOP_K)

    if not _chunks:
        logger.warning("RAG retrieve called but no chunks loaded.")
        return []

    scored = []
    for chunk_text, filename, heading in _chunks:
        score = _score_chunk(chunk_text, heading, query)
        if score >= _MIN_SCORE:          # discard noise
            scored.append((score, chunk_text, filename, heading))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:effective_k]

    if not top:
        logger.info("RAG: no chunks above minimum threshold for this query.")
        return []

    top_score  = top[0][0]
    confidence = get_confidence(top_score)

    results = []
    for score, chunk_text, filename, heading in top:
        meta = FILE_METADATA.get(filename, {"title": filename, "url": "https://eci.gov.in", "type": "rag"})
        results.append({
            "heading":         heading,
            "content":         chunk_text,
            "filename":        filename,
            "source_file":     filename,                # explicit alias for meta reporting
            "section_heading": heading,                 # explicit alias for meta reporting
            "score":           round(score, 3),
            "confidence":      confidence,              # tier for the whole batch
            "source_title":    meta["title"],
            "source_url":      meta["url"],
            "official_url":    meta["url"],             # explicit alias
            "source_type":     meta["type"],
        })

    score_range = f"{top[0][0]:.2f}-{top[-1][0]:.2f}" if len(top) > 1 else f"{top[0][0]:.2f}"
    logger.info(
        f"RAG retrieved {len(results)} chunks | confidence={confidence} "
        f"| top_score={top_score:.3f} | score_range={score_range}"
    )
    return results


def format_for_prompt(chunks: List[dict]) -> str:
    """Format retrieved chunks into a prompt injection block with full metadata."""
    if not chunks:
        return ""
    lines = ["--- TRUSTED VOTEWISE KNOWLEDGE BASE ---"]
    for c in chunks:
        lines.append(
            f"\n[Source: {c['source_title']} | File: {c['source_file']} | Section: {c['section_heading']}]\n"
            f"## {c['heading']}\n{c['content']}"
        )
    lines.append("\n--- END KNOWLEDGE BASE ---")
    return "\n".join(lines)
