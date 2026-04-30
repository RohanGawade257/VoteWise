import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, AlertCircle, Info } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import politicsBasics from '../data/politicsBasics.json';

const BasicsCard = ({ item, isOpen, onClick }) => {
  return (
    <div className="bg-white backdrop-blur-xl border border-border shadow-sm rounded-[2rem] overflow-hidden mb-6 transition-all duration-300 hover:border-secondary/50 hover:shadow-lg">
      <button
        onClick={onClick}
        aria-expanded={isOpen}
        aria-controls={`basics-content-${item.id}`}
        id={`basics-header-${item.id}`}
        className="w-full text-left p-6 sm:p-8 flex justify-between items-center focus:outline-none focus:ring-2 focus:ring-secondary focus:bg-slate-50 hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center">
          <div className="bg-blue-50 p-4 rounded-2xl mr-5 shadow-sm border border-blue-100">
            <BookOpen className="text-secondary drop-shadow-sm" size={26} />
          </div>
          <h3 className="font-extrabold text-2xl text-primary tracking-tight">{item.title}</h3>
        </div>
        {isOpen ? (
          <ChevronUp className="text-secondary flex-shrink-0" size={28} />
        ) : (
          <ChevronDown className="text-slate-400 flex-shrink-0" size={28} />
        )}
      </button>
      
      <div 
        id={`basics-content-${item.id}`}
        role="region"
        aria-labelledby={`basics-header-${item.id}`}
        className={`px-6 sm:px-8 border-t border-border overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,0.8,0.25,1)] ${isOpen ? 'max-h-[800px] py-8 opacity-100' : 'max-h-0 py-0 opacity-0 border-transparent'}`}
      >
        <div className="space-y-8">
          <div>
            <h4 className="flex items-center text-sm font-bold text-secondary uppercase tracking-wider mb-3">
              <Info size={18} className="mr-2" /> What is it?
            </h4>
            <p className="text-slate-800 font-light leading-relaxed text-lg">{item.simpleExplanation}</p>
          </div>
          
          <div className="bg-slate-50 p-5 rounded-2xl border border-border shadow-inner">
            <h4 className="text-sm font-bold text-secondary mb-2">Example:</h4>
            <p className="text-slate-700 font-light italic text-lg">{item.example}</p>
          </div>
          
          <div>
            <h4 className="flex items-center text-sm font-bold text-secondary uppercase tracking-wider mb-3">
              <AlertCircle size={18} className="mr-2" /> Why it matters
            </h4>
            <p className="text-slate-800 font-light leading-relaxed text-lg">{item.whyItMatters}</p>
          </div>
          
          <div className="text-xs text-slate-500 text-right mt-6 pt-5 border-t border-border font-light">
            Source: {item.source} | Last Verified: {item.lastVerified}
          </div>
        </div>
      </div>
    </div>
  );
};

const BasicsPage = () => {
  const [openId, setOpenId] = useState(politicsBasics[0]?.id || null);

  const toggleAccordion = (id) => {
    setOpenId(openId === id ? null : id);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <SectionHeader 
        title="Politics Basics" 
        subtitle="Understand the foundation of Indian democracy and governance."
      />
      
      <div className="mt-8">
        {politicsBasics.map((item) => (
          <BasicsCard 
            key={item.id} 
            item={item} 
            isOpen={openId === item.id} 
            onClick={() => toggleAccordion(item.id)} 
          />
        ))}
      </div>
    </div>
  );
};

export default BasicsPage;
