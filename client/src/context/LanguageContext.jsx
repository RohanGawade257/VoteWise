import React, { createContext, useState, useEffect, useContext } from 'react';

const LanguageContext = createContext();

export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi (हिंदी)' },
  { code: 'bn', name: 'Bengali (বাংলা)' },
  { code: 'mr', name: 'Marathi (मराठी)' },
  { code: 'te', name: 'Telugu (తెలుగు)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'gu', name: 'Gujarati (ગુજરાતી)' },
  { code: 'ur', name: 'Urdu (اردو)' },
  { code: 'kn', name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'or', name: 'Odia (ଓଡ଼ିଆ)' },
  { code: 'ml', name: 'Malayalam (മലയാളം)' },
];

export const LanguageProvider = ({ children }) => {
  const [currentLang, setCurrentLang] = useState('en');

  useEffect(() => {
    // 1. Check local storage
    const savedLang = localStorage.getItem('votewise_language');
    // 2. Check google translate cookie
    const match = document.cookie.match(/googtrans=\/en\/([a-z]{2})/);
    
    if (savedLang) {
      setCurrentLang(savedLang);
    } else if (match && match[1]) {
      const found = LANGUAGES.find(l => l.code === match[1]);
      if (found) {
        setCurrentLang(found.code);
      }
    }
    
    // Add Google Translate script
    const addScript = document.createElement('script');
    addScript.setAttribute('src', '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit');
    document.body.appendChild(addScript);
    
    window.googleTranslateElementInit = () => {
      new window.google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,hi,bn,mr,te,ta,gu,ur,kn,or,ml',
        autoDisplay: false
      }, 'google_translate_element');
    };
  }, []);

  const changeLanguage = (langCode) => {
    setCurrentLang(langCode);
    
    // Save to preferences
    localStorage.setItem('votewise_language', langCode);
    window.dispatchEvent(new Event('votewise-preferences-updated'));
    
    // Set google translate cookie
    document.cookie = `googtrans=/en/${langCode}; path=/`;
    document.cookie = `googtrans=/en/${langCode}; domain=.${window.location.hostname}; path=/`;
    
    // Reload to apply translation
    window.location.reload();
  };

  return (
    <LanguageContext.Provider value={{ currentLang, changeLanguage, languages: LANGUAGES }}>
      <div id="google_translate_element" style={{ display: 'none' }}></div>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
