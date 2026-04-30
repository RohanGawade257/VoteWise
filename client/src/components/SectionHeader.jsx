import React from 'react';

const SectionHeader = ({ title, subtitle, centered = false }) => {
  return (
    <div className={`mb-12 ${centered ? 'text-center flex flex-col items-center' : ''}`}>
      <h2 className="text-4xl md:text-5xl font-extrabold text-primary mb-4 tracking-tight leading-tight">{title}</h2>
      {subtitle && <p className="text-muted font-light text-lg md:text-xl max-w-2xl leading-relaxed">{subtitle}</p>}
      <div className={`h-1 w-24 bg-gradient-to-r from-secondary to-[#4F46E5] rounded-full mt-6 shadow-[0_0_10px_rgba(59,130,246,0.3)]`}></div>
    </div>
  );
};

export default SectionHeader;
