import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, AlertCircle, ShieldCheck } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import timelineData from '../data/timelineData.json';

const TimelineItem = ({ item, isOpen, onClick }) => {
  return (
    <div className="mb-4 last:mb-0">
      <button
        onClick={onClick}
        className={`w-full text-left p-4 sm:p-5 rounded-2xl transition-all duration-300 flex justify-between items-center ${
          isOpen 
            ? 'bg-blue-50 border border-blue-200 shadow-sm backdrop-blur-md' 
            : 'bg-white border border-border hover:bg-slate-50 hover:border-slate-300 backdrop-blur-sm shadow-sm'
        }`}
      >
        <span className={`font-bold text-lg ${isOpen ? 'text-primary' : 'text-slate-700'}`}>{item.title}</span>
        {isOpen ? <ChevronUp size={20} className="text-secondary" /> : <ChevronDown size={20} className="text-muted" />}
      </button>
      
      <div 
        className={`overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,0.8,0.25,1)] ${
          isOpen ? 'max-h-[800px] opacity-100 mt-3' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="bg-slate-50 backdrop-blur-xl p-6 sm:p-8 space-y-6 shadow-inner ml-2 md:ml-6 border-l-[3px] border-l-secondary rounded-r-2xl border-y border-r border-border">
          <div>
            <h5 className="text-xs font-bold text-secondary uppercase tracking-wider mb-2">Simple Explanation</h5>
            <p className="text-slate-800 leading-relaxed font-light">{item.simpleExplanation}</p>
          </div>
          
          <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
            <h5 className="text-sm font-bold text-secondary mb-1">Beginner Note</h5>
            <p className="text-sm text-slate-700 italic font-light">{item.beginnerExplanation}</p>
          </div>
          
          <div className="flex items-start space-x-4 text-sm">
            <div className="bg-warning/20 p-1.5 rounded-lg flex-shrink-0 mt-0.5">
              <AlertCircle size={18} className="text-warning" />
            </div>
            <div>
              <span className="font-bold text-warning block mb-1">Common Confusion:</span>
              <span className="text-muted font-light">{item.commonConfusion}</span>
            </div>
          </div>
          
          <div className="flex items-start space-x-4 text-sm pt-4 border-t border-border">
            <div className="bg-success/20 p-1.5 rounded-lg flex-shrink-0 mt-0.5">
              <ShieldCheck size={18} className="text-success" />
            </div>
            <div>
              <span className="font-bold text-success block mb-1">Official Reminder:</span>
              <span className="text-muted font-light">{item.officialReminder}</span>
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
        <div className="md:hidden absolute left-[11px] top-8 bottom-[-2rem] w-0.5 bg-slate-200 z-0"></div>
      )}
      
      <div className="md:grid md:grid-cols-12 md:gap-8 relative z-10 mb-16">
        {/* Phase Header (Left side on desktop) */}
        <div className="md:col-span-4 lg:col-span-3 mb-6 md:mb-0 md:text-right relative">
          {/* Stepped Timeline Dot */}
          <div className="absolute left-[-2rem] md:left-auto md:-right-[2.5rem] top-1 w-6 h-6 rounded-full bg-secondary border-4 border-white shadow-sm z-20 flex items-center justify-center"></div>
          
          {/* Desktop vertical line */}
          {!isLast && (
            <div className="hidden md:block absolute -right-[1.8rem] top-7 bottom-[-4rem] w-0.5 bg-slate-200 z-0"></div>
          )}
          
          <div className="inline-flex items-center text-xs font-bold uppercase tracking-widest text-secondary bg-blue-50 border border-blue-200 px-3 py-1 rounded-full mb-3 shadow-sm">
            Phase {index + 1}
          </div>
          <h3 className="text-3xl font-extrabold text-primary tracking-tight">{phase.phase}</h3>
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
