import React, { useState, useEffect, useRef } from 'react';
import { Globe } from 'lucide-react';
import PreferencesPanel from './PreferencesPanel';

export default function LanguageWidget() {
  const [open, setOpen] = useState(false);
  const panelRef = useRef(null);
  const triggerRef = useRef(null);

  // Close on Escape
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

  // Close on outside click
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

  return (
    <div className="hidden lg:block">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(v => !v)}
        aria-label="Settings"
        aria-expanded={open}
        className="fixed bottom-6 right-6 w-14 h-14 bg-secondary text-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl hover:-translate-y-1 hover:bg-[#2563EB] transition-all z-[100]"
      >
        <Globe size={24} />
      </button>

      {open && (
        <div
          ref={panelRef}
          className="fixed bottom-24 right-6 w-72 clay-card p-4 z-[100] animate-in slide-in-from-bottom-4 fade-in duration-300"
        >
          <PreferencesPanel onLanguageChange={() => setOpen(false)} />
        </div>
      )}
    </div>
  );
}
