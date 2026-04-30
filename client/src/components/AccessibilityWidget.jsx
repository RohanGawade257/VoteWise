import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Accessibility, Type, Contrast, RotateCcw, X, Plus, Minus } from 'lucide-react';

/**
 * AccessibilityWidget — floating bottom-right button that opens
 * a glassmorphism popover with Text Size and High Contrast controls.
 *
 * - Text size: scales <html> font-size via a CSS class
 * - High contrast: adds 'high-contrast' class to <html>
 * - Settings persist in localStorage
 * - Fully keyboard accessible (Escape to close, aria-* attributes)
 */

const FONT_SIZES = [
  { label: 'Small',  value: 'text-sm',  scale: '14px' },
  { label: 'Normal', value: 'text-base', scale: '16px' },
  { label: 'Large',  value: 'text-lg',  scale: '18px' },
  { label: 'XL',     value: 'text-xl',  scale: '20px' },
];

export default function AccessibilityWidget() {
  const [open, setOpen] = useState(false);
  const [fontIdx, setFontIdx] = useState(1); // default: Normal
  const [highContrast, setHighContrast] = useState(false);
  const panelRef = useRef(null);
  const triggerRef = useRef(null);

  // --- Hydrate from localStorage ---
  useEffect(() => {
    const saved = localStorage.getItem('a11y');
    if (saved) {
      try {
        const { fontIdx: fi, highContrast: hc } = JSON.parse(saved);
        if (typeof fi === 'number') setFontIdx(fi);
        if (typeof hc === 'boolean') setHighContrast(hc);
      } catch { /* ignore */ }
    }
  }, []);

  // --- Apply font size ---
  useEffect(() => {
    const el = document.documentElement;
    el.style.fontSize = FONT_SIZES[fontIdx].scale;
    localStorage.setItem('a11y', JSON.stringify({ fontIdx, highContrast }));
  }, [fontIdx, highContrast]);

  // --- Apply high contrast ---
  useEffect(() => {
    const el = document.documentElement;
    el.classList.toggle('high-contrast', highContrast);
    localStorage.setItem('a11y', JSON.stringify({ fontIdx, highContrast }));
  }, [highContrast, fontIdx]);

  // --- Close on Escape ---
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  // --- Close on outside click ---
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target) &&
          triggerRef.current && !triggerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const reset = useCallback(() => {
    setFontIdx(1);
    setHighContrast(false);
  }, []);

  return (
    <>
      {/* Floating trigger button */}
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(v => !v)}
        aria-label="Accessibility options"
        aria-expanded={open}
        aria-controls="a11y-panel"
        className="a11y-trigger"
      >
        <Accessibility size={20} />
      </button>

      {/* Popover panel */}
      {open && (
        <div
          ref={panelRef}
          id="a11y-panel"
          role="dialog"
          aria-label="Accessibility settings"
          className="a11y-panel"
        >
          {/* Header */}
          <div className="a11y-header">
            <span className="a11y-title">Accessibility</span>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close accessibility panel"
              className="a11y-close"
            >
              <X size={14} />
            </button>
          </div>

          {/* Text size */}
          <div className="a11y-section">
            <label className="a11y-label">
              <Type size={13} /> Text Size
            </label>
            <div className="a11y-size-row">
              <button
                type="button"
                onClick={() => setFontIdx(i => Math.max(0, i - 1))}
                disabled={fontIdx === 0}
                aria-label="Decrease text size"
                className="a11y-size-btn"
              >
                <Minus size={14} />
              </button>
              <span className="a11y-size-label">{FONT_SIZES[fontIdx].label}</span>
              <button
                type="button"
                onClick={() => setFontIdx(i => Math.min(FONT_SIZES.length - 1, i + 1))}
                disabled={fontIdx === FONT_SIZES.length - 1}
                aria-label="Increase text size"
                className="a11y-size-btn"
              >
                <Plus size={14} />
              </button>
            </div>
          </div>

          {/* High contrast */}
          <div className="a11y-section">
            <label className="a11y-label">
              <Contrast size={13} /> High Contrast
            </label>
            <button
              type="button"
              onClick={() => setHighContrast(v => !v)}
              role="switch"
              aria-checked={highContrast}
              className={`a11y-toggle ${highContrast ? 'a11y-toggle-on' : ''}`}
            >
              <span className="a11y-toggle-knob" />
            </button>
          </div>

          {/* Reset */}
          <button
            type="button"
            onClick={reset}
            className="a11y-reset"
          >
            <RotateCcw size={12} /> Reset to defaults
          </button>
        </div>
      )}
    </>
  );
}
