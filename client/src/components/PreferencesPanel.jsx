import React, { useState, useEffect } from 'react';
import { Globe, Check, Type, Minus, Plus } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { getTextSize, setTextSize } from '../utils/preferences';

const FONT_SIZES = [
  { label: 'Small', scale: '14px' },
  { label: 'Normal', scale: '16px' },
  { label: 'Large', scale: '18px' },
  { label: 'XL', scale: '20px' },
];

export default function PreferencesPanel({ onLanguageChange }) {
  const [fontIdx, setFontIdx] = useState(getTextSize());
  const { currentLang, changeLanguage, languages } = useLanguage();

  // --- Hydrate Text Size ---
  useEffect(() => {
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
    <div className="flex flex-col">
      {/* Text Size Section */}
      <div className="mb-4 pb-4 border-b border-white/30">
        <h3 className="font-bold text-primary flex items-center gap-2 mb-3">
          <Type size={18} className="text-secondary" />
          Text Size
        </h3>
        <div className="flex items-center justify-between bg-white/40 backdrop-blur-sm p-1 rounded-xl border border-white/50 shadow-inner">
          <button
            onClick={() => setFontIdx(Math.max(0, fontIdx - 1))}
            disabled={fontIdx === 0}
            className="p-2 rounded-lg hover:bg-white/70 disabled:opacity-50 transition-all text-slate-700 shadow-sm border border-transparent hover:border-white/60"
            aria-label="Decrease text size"
          >
            <Minus size={18} />
          </button>
          <span className="font-bold text-sm text-primary w-16 text-center">
            {FONT_SIZES[fontIdx].label}
          </span>
          <button
            onClick={() => setFontIdx(Math.min(FONT_SIZES.length - 1, fontIdx + 1))}
            disabled={fontIdx === FONT_SIZES.length - 1}
            className="p-2 rounded-lg hover:bg-white/70 disabled:opacity-50 transition-all text-slate-700 shadow-sm border border-transparent hover:border-white/60"
            aria-label="Increase text size"
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

      <div className="flex flex-col gap-1 max-h-[40vh] overflow-y-auto pr-1">
        {languages.map(lang => {
          const isActive = currentLang === lang.code;
          return (
            <button
              key={lang.code}
              onClick={() => {
                changeLanguage(lang.code);
                if (onLanguageChange) onLanguageChange(lang.code);
              }}
              className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition-all ${
                isActive 
                  ? 'bg-secondary/10 text-secondary font-bold border border-secondary/20 shadow-sm' 
                  : 'text-slate-700 hover:bg-white/60 border border-transparent'
              }`}
            >
              <span className="text-sm">{lang.name}</span>
              {isActive && <Check size={16} />}
            </button>
          );
        })}
      </div>
    </div>
  );
}
