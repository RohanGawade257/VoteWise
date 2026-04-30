// Utility to manage user preferences

export const PREF_KEYS = {
  COMPLETED: 'votewise_preferences_completed',
  TEXT_SIZE: 'a11y-font', // Reusing existing key from LanguageWidget
  LANGUAGE: 'votewise_language',
  TONE: 'votewise_assistant_tone',
};

// Check if setup is completed
export const isPreferencesCompleted = () => {
  return localStorage.getItem(PREF_KEYS.COMPLETED) === 'true';
};

// Mark setup as completed
export const markPreferencesCompleted = () => {
  localStorage.setItem(PREF_KEYS.COMPLETED, 'true');
};

// Text Size (0: Small, 1: Normal, 2: Large, 3: XL)
export const getTextSize = () => {
  const saved = localStorage.getItem(PREF_KEYS.TEXT_SIZE);
  if (saved !== null) {
    try {
      const parsed = JSON.parse(saved);
      if (typeof parsed === 'number') return parsed;
    } catch (e) {
      // ignore
    }
  }
  return 1; // Normal by default
};

export const setTextSize = (index) => {
  localStorage.setItem(PREF_KEYS.TEXT_SIZE, JSON.stringify(index));
  // Apply immediately to document
  const FONT_SIZES = ['14px', '16px', '18px', '20px'];
  if (index >= 0 && index < FONT_SIZES.length) {
    document.documentElement.style.fontSize = FONT_SIZES[index];
  }
  window.dispatchEvent(new Event('votewise-preferences-updated'));
};

// Language code
export const getLanguage = () => {
  return localStorage.getItem(PREF_KEYS.LANGUAGE) || 'en';
};

export const setLanguage = (code) => {
  localStorage.setItem(PREF_KEYS.LANGUAGE, code);
  window.dispatchEvent(new Event('votewise-preferences-updated'));
};

// Assistant Tone
export const getAssistantTone = () => {
  return localStorage.getItem(PREF_KEYS.TONE) || 'general';
};

export const setAssistantTone = (tone) => {
  localStorage.setItem(PREF_KEYS.TONE, tone);
  window.dispatchEvent(new Event('votewise-preferences-updated'));
};
