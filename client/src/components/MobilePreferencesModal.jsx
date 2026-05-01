import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import PreferencesPanel from './PreferencesPanel';

export default function MobilePreferencesModal({ isOpen, onClose }) {
  const modalRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    
    document.addEventListener('keydown', handleKeyDown);
    // Prevent scrolling on body when modal is open
    document.body.style.overflow = 'hidden';
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-preferences-title"
        className="w-full max-w-sm clay-card overflow-hidden flex flex-col animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-white/40 bg-white/30">
          <h2 id="mobile-preferences-title" className="text-lg font-bold text-primary">
            Language & Text Size
          </h2>
          <button
            onClick={onClose}
            aria-label="Close preferences"
            className="p-2 rounded-full text-muted hover:text-primary hover:bg-white/50 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-secondary"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-5 overflow-y-auto max-h-[70vh]">
          <PreferencesPanel onLanguageChange={onClose} />
        </div>
      </div>
    </div>
  );
}
