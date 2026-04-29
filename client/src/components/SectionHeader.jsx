import React from 'react';

const SectionHeader = ({ title, subtitle, centered = false }) => {
  return (
    <div className={`mb-12 ${centered ? 'text-center flex flex-col items-center' : ''}`}>
      <h2 className="text-4xl md:text-5xl font-extrabold text-primary mb-4 tracking-tight">{title}</h2>
      {subtitle && <p className="text-muted text-lg md:text-xl max-w-2xl">{subtitle}</p>}
      <div className={`h-1.5 w-24 bg-gradient-to-r from-secondary to-primary rounded-full mt-6`}></div>
    </div>
  );
};

export default SectionHeader;
