import React, { useState, useEffect, useRef } from 'react';
import { Globe, Check, Type, Minus, Plus } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { getTextSize, setTextSize } from '../utils/preferences';

const FONT_SIZES = [
  { label: 'Small', scale: '14px' },
  { label: 'Normal', scale: '16px' },
  { label: 'Large', scale: '18px' },
  { label: 'XL', scale: '20px' },
];

export default function LanguageWidget() {
  const [open, setOpen] = useState(false);
  const [fontIdx, setFontIdx] = useState(getTextSize());
  const { currentLang, changeLanguage, languages } = useLanguage();
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

  // --- Hydrate Text Size ---
  useEffect(() => {
    // Listen for custom event from preferences modal
    const handleStorageChange = () => {
      setFontIdx(getTextSize());
    };
    window.addEventListener('votewise-preferences-updated', handleStorageChange);
    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('votewise-preferences-updated', handleStorageChange);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  // --- Apply Text Size ---
  useEffect(() => {
    setTextSize(fontIdx);
  }, [fontIdx]);

  return (
    <>
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
          className="fixed bottom-24 right-6 w-72 bg-white/95 backdrop-blur-3xl rounded-2xl border border-border shadow-2xl p-4 z-[100] animate-in slide-in-from-bottom-4 fade-in duration-300"
        >
          {/* Text Size Section */}
          <div className="mb-4 pb-4 border-b border-border">
            <h3 className="font-bold text-primary flex items-center gap-2 mb-3">
              <Type size={18} className="text-secondary" />
              Text Size
            </h3>
            <div className="flex items-center justify-between bg-slate-50 p-1 rounded-xl border border-border">
              <button
                onClick={() => setFontIdx(Math.max(0, fontIdx - 1))}
                disabled={fontIdx === 0}
                className="p-2 rounded-lg hover:bg-white disabled:opacity-50 transition-all text-slate-700"
              >
                <Minus size={18} />
              </button>
              <span className="font-bold text-sm text-primary w-16 text-center">
                {FONT_SIZES[fontIdx].label}
              </span>
              <button
                onClick={() => setFontIdx(Math.min(FONT_SIZES.length - 1, fontIdx + 1))}
                disabled={fontIdx === FONT_SIZES.length - 1}
                className="p-2 rounded-lg hover:bg-white disabled:opacity-50 transition-all text-slate-700"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>

          {/* Language Section */}
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-bold text-primary flex items-center gap-2">
              <Globe size={18} className="text-secondary" />
              Select Language
            </h3>
          </div>

          <div className="flex flex-col gap-1 max-h-[60vh] overflow-y-auto pr-1">
            {languages.map(lang => {
              const isActive = currentLang === lang.code;
              return (
                <button
                  key={lang.code}
                  onClick={() => {
                    changeLanguage(lang.code);
                    setOpen(false);
                  }}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition-all ${
                    isActive 
                      ? 'bg-blue-50 text-secondary font-bold border border-blue-100' 
                      : 'text-slate-700 hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  <span className="text-sm">{lang.name}</span>
                  {isActive && <Check size={16} />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
