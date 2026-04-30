/**
 * MessageMeta — renders answer-provenance badges, RAG confidence label,
 * and an expandable "Knowledge sources used" section under bot messages.
 *
 * Props:
 *   meta           — the meta object from the API response
 *   sources        — the sources array from the API response
 *   safetyBlocked  — boolean: was this message blocked by safety?
 */
import React, { useState } from 'react';
import {
  ShieldOff,
  BookOpen,
  Cpu,
  Zap,
  AlertCircle,
  WifiOff,
  ChevronDown,
  ChevronUp,
  FileText,
  ExternalLink,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Friendly file-name → display-name mapping
// ---------------------------------------------------------------------------
const FILE_LABELS = {
  'first_time_voter.md':      'First-Time Voter Guide',
  'election_process.md':      'Election Process Guide',
  'politics_basics.md':       'Politics Basics',
  'timeline.md':              'Election Timeline',
  'official_sources.md':      'Official Sources',
  'party_directory_notes.md': 'Political Parties Directory',
};

function friendlyFile(filename) {
  return FILE_LABELS[filename] || filename.replace('.md', '').replace(/_/g, ' ');
}

// ---------------------------------------------------------------------------
// Badge config — maps logical answer-type to visual badge
// ---------------------------------------------------------------------------
function resolveBadge(meta, safetyBlocked) {
  if (safetyBlocked) {
    return {
      icon: <ShieldOff size={11} />,
      label: 'Safety blocked',
      colorClass: 'badge-safety',
    };
  }
  if (!meta) return null;

  const { model, used_direct_answer, used_rag, used_model, sourceType } = meta;

  // Live-source redirect or official-grounding
  if (sourceType === 'official_grounding') {
    return {
      icon: <Zap size={11} />,
      label: 'Verified with official sources',
      colorClass: 'badge-live',
    };
  }
  if (sourceType === 'unverified_fallback') {
    return {
      icon: <WifiOff size={11} />,
      label: 'Live verification unavailable',
      colorClass: 'badge-fallback',
    };
  }

  // Scope guard (out-of-topic)
  if (model === 'scope-guard') {
    return {
      icon: <AlertCircle size={11} />,
      label: 'Outside VoteWise scope',
      colorClass: 'badge-scope',
    };
  }

  // Direct answer (no RAG, no model)
  if (used_direct_answer && !used_model) {
    return {
      icon: <BookOpen size={11} />,
      label: 'Direct answer',
      colorClass: 'badge-direct',
    };
  }

  // RAG + model
  if (used_rag && used_model) {
    return {
      icon: <Cpu size={11} />,
      label: 'AI-assisted answer',
      colorClass: 'badge-ai',
    };
  }

  // Model only (no RAG — e.g. live intent with grounding)
  if (!used_rag && used_model) {
    return {
      icon: <Cpu size={11} />,
      label: 'AI-assisted answer',
      colorClass: 'badge-ai',
    };
  }

  // Knowledge base only (shouldn't normally happen, but defensive)
  if (used_rag && !used_model) {
    return {
      icon: <BookOpen size={11} />,
      label: 'VoteWise knowledge base',
      colorClass: 'badge-kb',
    };
  }

  return null;
}

// Confidence label text
const CONFIDENCE_LABELS = {
  high:   { text: 'Strong source match',    dot: 'conf-high' },
  medium: { text: 'Moderate source match',  dot: 'conf-medium' },
  low:    { text: 'Low source match',       dot: 'conf-low' },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function MessageMeta({ meta, sources, safetyBlocked }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const badge = resolveBadge(meta, safetyBlocked);

  const confidence     = meta?.rag_confidence;
  const confLabel      = CONFIDENCE_LABELS[confidence];
  const sourceFiles    = meta?.source_files_used ?? [];
  const checkedAt      = meta?.checkedAt;
  const sourceType     = meta?.sourceType;

  // External links (from the sources array)
  const externalLinks  = (sources ?? []).filter(s => s?.url);

  // Expandable sources section shows when there are internal KB files referenced
  const hasKBFiles     = sourceFiles.length > 0;
  // External links always shown (if present)
  const hasExternal    = externalLinks.length > 0;

  const showFooter = badge || confLabel || hasKBFiles || hasExternal || checkedAt || sourceType;

  if (!showFooter) return null;

  return (
    <div className="msg-meta-root">

      {/* ── Row 1: badge + confidence dot ─────────────────────────────── */}
      <div className="msg-meta-row">
        {badge && (
          <span className={`msg-badge ${badge.colorClass}`}>
            {badge.icon}
            {badge.label}
          </span>
        )}

        {confLabel && (
          <span className="conf-label">
            <span className={`conf-dot ${confLabel.dot}`} />
            {confLabel.text}
          </span>
        )}

        {/* Live-check timestamp */}
        {checkedAt && (
          <span className="conf-label">
            Checked: {new Date(checkedAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      {/* ── Row 2: expandable KB sources ──────────────────────────────── */}
      {hasKBFiles && (
        <div className="kb-sources">
          <button
            type="button"
            className="kb-toggle"
            onClick={() => setSourcesOpen(v => !v)}
            aria-expanded={sourcesOpen}
          >
            <FileText size={11} />
            Knowledge sources used ({sourceFiles.length})
            {sourcesOpen ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
          </button>

          {sourcesOpen && (
            <ul className="kb-file-list">
              {sourceFiles.map(f => (
                <li key={f} className="kb-file-item">
                  <span className="kb-file-dot" />
                  {friendlyFile(f)}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* ── Row 3: external source links ──────────────────────────────── */}
      {hasExternal && (
        <div className="ext-sources">
          <span className="ext-sources-label">Sources</span>
          <div className="ext-links">
            {externalLinks.map((src, i) => (
              <a
                key={i}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ext-link"
              >
                <ExternalLink size={10} />
                {src.title}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
