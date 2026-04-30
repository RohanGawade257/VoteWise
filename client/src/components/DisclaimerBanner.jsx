import React from 'react';
import { Info } from 'lucide-react';

const DisclaimerBanner = () => {
  return (
    <div className="bg-slate-100 border-b border-border text-muted px-4 py-2.5 text-xs sm:text-sm flex justify-center items-center space-x-3 w-full">
      <div className="flex items-center justify-center max-w-5xl">
        <Info className="flex-shrink-0 mr-2 text-secondary" size={16} />
        <p className="font-light tracking-wide">
          <strong className="text-primary font-medium">VoteWise</strong> is a non-partisan educational platform. We do not endorse any political party.
        </p>
      </div>
    </div>
  );
};

export default DisclaimerBanner;
