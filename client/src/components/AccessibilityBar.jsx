import React from 'react';
import { Settings2, Type, Contrast } from 'lucide-react';

const AccessibilityBar = () => {
  return (
    <div className="bg-primary text-surface py-2 px-4 text-sm flex justify-between items-center z-50 relative">
      <div className="flex items-center space-x-2">
        <Settings2 size={16} />
        <span className="font-medium hidden sm:inline">Accessibility Options</span>
      </div>
      <div className="flex items-center space-x-4">
        <button className="flex items-center space-x-1 hover:text-secondary transition-colors">
          <Type size={16} />
          <span className="hidden sm:inline">Text Size</span>
        </button>
        <button className="flex items-center space-x-1 hover:text-secondary transition-colors">
          <Contrast size={16} />
          <span className="hidden sm:inline">High Contrast</span>
        </button>
      </div>
    </div>
  );
};

export default AccessibilityBar;
