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
    "election_process.md":      {"title": "Indian Election Process", "url": "https://eci.gov.in", "type": "official"},
    "first_time_voter.md":      {"title": "First-Time Voter Guide", "url": "https://voters.eci.gov.in", "type": "official"},
    "timeline.md":              {"title": "Election Timeline", "url": "https://eci.gov.in", "type": "official"},
    "politics_basics.md":       {"title": "Politics Basics", "url": "https://eci.gov.in", "type": "rag"},
    "party_directory_notes.md": {"title": "Party Directory Notes", "url": "https://eci.gov.in/political-parties/", "type": "official"},
    "official_sources.md":      {"title": "Official Sources Reference", "url": "https://eci.gov.in", "type": "official"},
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
    """Simple keyword overlap scoring."""
    query_words = set(re.findall(r'\w+', query.lower()))
    chunk_words = set(re.findall(r'\w+', chunk_text.lower()))
    heading_words = set(re.findall(r'\w+', heading.lower()))

    # Stop words to exclude from scoring
    stop_words = {"i", "am", "is", "are", "the", "a", "an", "and", "or", "to", "do", "how", "what", "in", "for", "of", "my", "me", "can", "you", "your", "this", "that"}
    query_words -= stop_words

    if not query_words:
        return 0.0

    # Keyword overlap with chunk content
    content_overlap = len(query_words & chunk_words) / len(query_words)
    # Extra weight for heading matches
    heading_overlap = len(query_words & heading_words) / max(len(query_words), 1)

    return content_overlap + (heading_overlap * 0.5)

def retrieve(query: str, top_k: int = 4) -> List[dict]:
    """Retrieve top_k most relevant chunks for the query."""
    if not _chunks:
        logger.warning("RAG retrieve called but no chunks loaded.")
        return []

    scored = []
    for chunk_text, filename, heading in _chunks:
        score = _score_chunk(chunk_text, heading, query)
        if score > 0:
            scored.append((score, chunk_text, filename, heading))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    results = []
    seen_files = set()
    for score, chunk_text, filename, heading in top:
        meta = FILE_METADATA.get(filename, {"title": filename, "url": "https://eci.gov.in", "type": "rag"})
        results.append({
            "heading": heading,
            "content": chunk_text,
            "filename": filename,
            "score": round(score, 3),
            "source_title": meta["title"],
            "source_url": meta["url"],
            "source_type": meta["type"],
        })
        seen_files.add(filename)

    logger.info(f"RAG retrieved {len(results)} chunks for query (score range: {top[0][0]:.2f}-{top[-1][0]:.2f})" if results else "RAG: no relevant chunks found")
    return results

def format_for_prompt(chunks: List[dict]) -> str:
    """Format retrieved chunks into a prompt injection block."""
    if not chunks:
        return ""
    lines = ["--- TRUSTED VOTEWISE KNOWLEDGE BASE CONTEXT ---"]
    for c in chunks:
        lines.append(f"\n[Source: {c['source_title']}]\n## {c['heading']}\n{c['content']}")
    lines.append("\n--- END OF CONTEXT ---")
    return "\n".join(lines)
