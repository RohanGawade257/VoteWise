import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, AlertCircle, ShieldCheck } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import timelineData from '../data/timelineData.json';

const TimelineItem = ({ item, isOpen, onClick }) => {
  return (
    <div className="mb-4 last:mb-0">
      <button
        onClick={onClick}
        className={`w-full text-left p-4 rounded-xl transition-all duration-300 flex justify-between items-center ${
          isOpen 
            ? 'clay-card border-secondary' 
            : 'bg-background border border-border hover:border-secondary/50'
        }`}
      >
        <span className="font-bold text-primary">{item.title}</span>
        {isOpen ? <ChevronUp size={20} className="text-secondary" /> : <ChevronDown size={20} className="text-muted" />}
      </button>
      
      <div 
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isOpen ? 'max-h-[500px] opacity-100 mt-2' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="clay-card p-5 space-y-4 shadow-sm ml-2 md:ml-6 border-l-4 border-l-secondary border-t-0 border-r-0 border-b-0 rounded-l-none">
          <div>
            <h5 className="text-sm font-bold text-muted uppercase tracking-wider mb-1">Simple Explanation</h5>
            <p className="text-text">{item.simpleExplanation}</p>
          </div>
          
          <div className="bg-primary/5 p-3 rounded-lg">
            <h5 className="text-sm font-bold text-primary mb-1">Beginner Note</h5>
            <p className="text-sm text-text/80 italic">{item.beginnerExplanation}</p>
          </div>
          
          <div className="flex items-start space-x-3 text-sm">
            <AlertCircle size={18} className="text-warning flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-warning block mb-1">Common Confusion:</span>
              <span className="text-muted">{item.commonConfusion}</span>
            </div>
          </div>
          
          <div className="flex items-start space-x-3 text-sm pt-3 border-t border-border">
            <ShieldCheck size={18} className="text-success flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-success block mb-1">Official Reminder:</span>
              <span className="text-muted">{item.officialReminder}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const TimelinePhase = ({ phase, index, isLast }) => {
  const [openItemId, setOpenItemId] = useState(phase.items[0]?.id);

  return (
    <div className="relative pl-8 md:pl-0">
      {/* Vertical line for mobile */}
      {!isLast && (
        <div className="md:hidden absolute left-[11px] top-8 bottom-[-2rem] w-0.5 bg-border z-0"></div>
      )}
      
      <div className="md:grid md:grid-cols-12 md:gap-8 relative z-10 mb-12">
        {/* Phase Header (Left side on desktop) */}
        <div className="md:col-span-4 lg:col-span-3 mb-4 md:mb-0 md:text-right relative">
          {/* Stepped Timeline Dot */}
          <div className="absolute left-[-2rem] md:left-auto md:-right-[2.5rem] top-1 w-6 h-6 rounded-full bg-secondary border-4 border-surface shadow-sm z-20 flex items-center justify-center"></div>
          
          {/* Desktop vertical line */}
          {!isLast && (
            <div className="hidden md:block absolute -right-[1.8rem] top-7 bottom-[-4rem] w-0.5 bg-border z-0"></div>
          )}
          
          <div className="inline-flex items-center text-xs font-bold uppercase tracking-widest text-secondary bg-secondary/10 px-3 py-1 rounded-full mb-2">
            Phase {index + 1}
          </div>
          <h3 className="text-2xl font-bold text-primary">{phase.phase}</h3>
        </div>
        
        {/* Phase Items (Right side on desktop) */}
        <div className="md:col-span-8 lg:col-span-9">
          {phase.items.map((item) => (
            <TimelineItem 
              key={item.id} 
              item={item} 
              isOpen={openItemId === item.id}
              onClick={() => setOpenItemId(openItemId === item.id ? null : item.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

const TimelinePage = () => {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <SectionHeader 
        title="Election Timeline" 
        subtitle="Understand the sequential phases of the Indian electoral cycle."
        centered={true}
      />
      
      <div className="mt-16 max-w-4xl mx-auto relative">
        {timelineData.map((phase, index) => (
          <TimelinePhase 
            key={phase.id} 
            phase={phase} 
            index={index} 
            isLast={index === timelineData.length - 1} 
          />
        ))}
      </div>
    </div>
  );
};

export default TimelinePage;
