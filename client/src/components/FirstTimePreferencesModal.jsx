import React, { useState, useEffect, useRef } from 'react';
import { Type, Globe, Bot, X } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { 
  isPreferencesCompleted, 
  markPreferencesCompleted, 
  getTextSize, 
  setTextSize, 
  getLanguage, 
  setLanguage,
  getAssistantTone,
  setAssistantTone,
  getUserState,
  setUserState
} from '../utils/preferences';
import { statesData } from '../data/stateElectionResources';
import { MapPin } from 'lucide-react';

const TONES = [
  { id: 'general', label: 'General' },
  { id: 'first-time-voter', label: 'First-Time Voter' },
  { id: 'student', label: 'School Student' },
  { id: 'elderly', label: 'Elderly' }
];

const TEXT_SIZES = [
  { id: 0, label: 'Small' },
  { id: 1, label: 'Normal' },
  { id: 2, label: 'Large' },
];

export default function FirstTimePreferencesModal() {
  const [isOpen, setIsOpen] = useState(false);
  
  const { languages, changeLanguage, currentLang } = useLanguage();
  
  // Local state for modal choices
  const [selectedSize, setSelectedSize] = useState(1);
  const [selectedLang, setSelectedLang] = useState('en');
  const [selectedTone, setSelectedTone] = useState('general');
  const [selectedState, setSelectedState] = useState('');
  
  const modalRef = useRef(null);

  useEffect(() => {
    // Check if we should show the modal
    if (!isPreferencesCompleted()) {
      // Init local state with what might be in localStorage, just in case
      setSelectedSize(getTextSize() > 2 ? 1 : getTextSize()); // max large for simple UI
      setSelectedLang(getLanguage() || currentLang || 'en');
      setSelectedTone(getAssistantTone() || 'general');
      setSelectedState(getUserState() || '');
      
      // Small delay for smooth entrance
      const timer = setTimeout(() => setIsOpen(true), 500);
      return () => clearTimeout(timer);
    }
  }, [currentLang]);

  // Trap focus and handle escape
  useEffect(() => {
    if (!isOpen) return;
    
    // Prevent background scrolling
    document.body.style.overflow = 'hidden';
    
    // Focus trap setup could go here, but for now just auto-focus modal
    modalRef.current?.focus();
    
    const handleKeyDown = (e) => {
      // ESC intentionally does NOT close this modal because it's a first-time setup
      // unless we want it to be dismissable. User explicitly requested: "ESC close only if safe"
      // Since it's a preference popup, they can close it, but we should mark it as completed 
      // with defaults if they force close it.
      if (e.key === 'Escape') {
        handleSaveDefaults();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSave = () => {
    setTextSize(selectedSize);
    setLanguage(selectedLang);
    setAssistantTone(selectedTone);
    setUserState(selectedState);
    markPreferencesCompleted();
    
    setIsOpen(false);
    
    // If language changed, apply it. (This will trigger a reload in current implementation)
    if (selectedLang !== currentLang) {
      changeLanguage(selectedLang);
    }
  };

  const handleSaveDefaults = () => {
    setTextSize(1);
    setLanguage('en');
    setAssistantTone('general');
    setUserState('');
    markPreferencesCompleted();
    
    setIsOpen(false);
    
    if ('en' !== currentLang) {
      changeLanguage('en');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div 
        ref={modalRef}
        tabIndex="-1"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        aria-describedby="modal-subtitle"
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto outline-none animate-in zoom-in-95 duration-300 border border-slate-100"
      >
        <div className="p-6 sm:p-8">
          <div className="text-center mb-8">
            <h2 id="modal-title" className="text-2xl font-extrabold text-primary mb-2">Set up your VoteWise experience</h2>
            <p id="modal-subtitle" className="text-slate-600">Choose your preferred reading size, language, and assistant tone.</p>
          </div>

          <div className="space-y-8">
            {/* 1. Text Size */}
            <section aria-labelledby="section-text-size">
              <h3 id="section-text-size" className="font-bold text-slate-800 flex items-center gap-2 mb-3">
                <Type size={18} className="text-secondary" />
                Text Size
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {TEXT_SIZES.map((size) => (
                  <button
                    key={size.id}
                    onClick={() => setSelectedSize(size.id)}
                    className={`py-2 px-3 rounded-xl border-2 transition-all font-medium ${
                      selectedSize === size.id 
                        ? 'border-secondary bg-blue-50 text-secondary' 
                        : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    {size.label}
                  </button>
                ))}
              </div>
            </section>

            {/* 2. Language */}
            <section aria-labelledby="section-language">
              <h3 id="section-language" className="font-bold text-slate-800 flex items-center gap-2 mb-3">
                <Globe size={18} className="text-secondary" />
                Preferred Language
              </h3>
              <div className="relative">
                <select
                  value={selectedLang}
                  onChange={(e) => setSelectedLang(e.target.value)}
                  className="w-full appearance-none bg-slate-50 border-2 border-slate-200 text-slate-800 py-3 px-4 rounded-xl font-medium focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary cursor-pointer"
                  aria-label="Select Preferred Language"
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>
            </section>

            {/* 3. Assistant Tone */}
            <section aria-labelledby="section-tone">
              <h3 id="section-tone" className="font-bold text-slate-800 flex items-center gap-2 mb-3">
                <Bot size={18} className="text-secondary" />
                Assistant Tone
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {TONES.map((tone) => (
                  <button
                    key={tone.id}
                    onClick={() => setSelectedTone(tone.id)}
                    className={`py-2 px-3 rounded-xl border-2 transition-all font-medium text-sm sm:text-base ${
                      selectedTone === tone.id 
                        ? 'border-secondary bg-blue-50 text-secondary' 
                        : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    {tone.label}
                  </button>
                ))}
              </div>
            </section>
            {/* 4. State Selection */}
            <section aria-labelledby="section-state">
              <h3 id="section-state" className="font-bold text-slate-800 flex items-center gap-2 mb-3">
                <MapPin size={18} className="text-secondary" />
                Select Your State
              </h3>
              <div className="relative">
                <input 
                  list="indian-states"
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  placeholder="Type to search your state (Optional)"
                  className="w-full appearance-none bg-slate-50 border-2 border-slate-200 text-slate-800 py-3 px-4 rounded-xl font-medium focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary"
                  aria-label="Select Your State"
                />
                <datalist id="indian-states">
                  {statesData.map(state => (
                    <option key={state.name} value={state.name} />
                  ))}
                </datalist>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-500">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-10 flex flex-col gap-3">
            <button
              onClick={handleSave}
              className="w-full bg-secondary hover:bg-[#2563EB] text-white font-bold py-3.5 px-4 rounded-xl transition-colors shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary"
            >
              Save Preferences
            </button>
            <button
              onClick={handleSaveDefaults}
              className="w-full bg-white hover:bg-slate-50 text-slate-600 font-bold py-3.5 px-4 rounded-xl border border-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-300"
            >
              Continue with Defaults
            </button>
          </div>
          
          <p className="text-center text-xs text-slate-400 mt-4">
            You can change these anytime from the language and accessibility controls.
          </p>
        </div>
      </div>
    </div>
  );
}
