import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, AlertCircle, Info } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import politicsBasics from '../data/politicsBasics.json';

const BasicsCard = ({ item, isOpen, onClick }) => {
  return (
    <div className="bg-surface border border-border rounded-xl shadow-sm overflow-hidden mb-6 transition-all hover:border-secondary/50">
      <button
        onClick={onClick}
        aria-expanded={isOpen}
        aria-controls={`basics-content-${item.id}`}
        id={`basics-header-${item.id}`}
        className="w-full text-left p-6 flex justify-between items-center focus:outline-none focus:ring-2 focus:ring-primary focus:bg-background/50 hover:bg-background/50 transition-colors"
      >
        <div className="flex items-center">
          <div className="bg-primary/10 p-3 rounded-lg mr-4">
            <BookOpen className="text-primary" size={24} />
          </div>
          <h3 className="font-bold text-xl text-primary">{item.title}</h3>
        </div>
        {isOpen ? (
          <ChevronUp className="text-secondary flex-shrink-0" size={24} />
        ) : (
          <ChevronDown className="text-muted flex-shrink-0" size={24} />
        )}
      </button>
      
      <div 
        id={`basics-content-${item.id}`}
        role="region"
        aria-labelledby={`basics-header-${item.id}`}
        className={`px-6 border-t border-border overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-96 py-6 opacity-100' : 'max-h-0 py-0 opacity-0 border-transparent'}`}
      >
        <div className="space-y-6">
          <div>
            <h4 className="flex items-center text-sm font-bold text-muted uppercase tracking-wider mb-2">
              <Info size={16} className="mr-2" /> What is it?
            </h4>
            <p className="text-text leading-relaxed">{item.simpleExplanation}</p>
          </div>
          
          <div className="bg-background p-4 rounded-lg border border-border">
            <h4 className="text-sm font-bold text-secondary mb-1">Example:</h4>
            <p className="text-text italic">{item.example}</p>
          </div>
          
          <div>
            <h4 className="flex items-center text-sm font-bold text-muted uppercase tracking-wider mb-2">
              <AlertCircle size={16} className="mr-2" /> Why it matters
            </h4>
            <p className="text-text leading-relaxed">{item.whyItMatters}</p>
          </div>
          
          <div className="text-xs text-muted text-right mt-4 pt-4 border-t border-border">
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
