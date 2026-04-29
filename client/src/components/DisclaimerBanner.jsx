import React from 'react';
import { Info } from 'lucide-react';

const DisclaimerBanner = () => {
  return (
    <div className="bg-warning/10 text-warning px-4 py-3 text-sm flex items-start sm:items-center space-x-3">
      <Info className="flex-shrink-0 mt-0.5 sm:mt-0" size={18} />
      <p>
        <strong>Disclaimer:</strong> VoteWise is a non-partisan, educational platform. We do not endorse any political party, candidate, or ideology. Information provided is for civic education purposes only.
      </p>
    </div>
  );
};

export default DisclaimerBanner;
