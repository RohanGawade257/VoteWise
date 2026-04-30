import React, { useState } from 'react';
import { CheckCircle, Circle, ExternalLink, MessageSquare, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import SectionHeader from '../components/SectionHeader';
import guideSteps from '../data/guideSteps.json';

const GuideStep = ({ step, isComplete, onToggleComplete }) => {
  const [showSimple, setShowSimple] = useState(false);

  return (
    <div className={`relative flex gap-6 p-6 rounded-3xl border transition-all duration-500 shadow-sm ${
      isComplete 
        ? 'border-success/50 bg-success/10 shadow-[0_0_15px_rgba(16,185,129,0.1)]' 
        : 'border-border bg-white shadow-md hover:border-secondary/50'
    }`}>
      {/* Progress Line & Circle */}
      <div className="flex flex-col items-center">
        <button 
          onClick={() => onToggleComplete(step.step)}
          className={`relative z-10 flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-success rounded-full ${isComplete ? 'bg-transparent' : 'bg-white'}`}
          aria-label={isComplete ? "Mark as incomplete" : "Mark as complete"}
        >
          {isComplete ? (
            <CheckCircle className="text-success w-8 h-8 drop-shadow-sm" />
          ) : (
            <Circle className="text-slate-300 hover:text-secondary transition-colors w-8 h-8" />
          )}
        </button>
        {step.step !== 7 && (
          <div className={`w-[2px] h-full mt-2 -mb-8 ${isComplete ? 'bg-success/40 shadow-sm' : 'bg-slate-200'}`}></div>
        )}
      </div>

      {/* Content */}
      <div className="flex-grow pb-4">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-xs font-bold text-secondary uppercase tracking-widest bg-secondary/10 px-3 py-1 rounded-full border border-secondary/20">Step {step.step}</span>
        </div>
        <h3 className={`text-2xl font-extrabold mb-3 tracking-tight ${isComplete ? 'text-success' : 'text-primary'}`}>
          {step.title}
        </h3>
        
        <p className="text-slate-700 font-light leading-relaxed mb-6">{step.explanation}</p>
        
        {showSimple && (
          <div className="bg-blue-50 border border-blue-100 p-5 rounded-2xl mb-6 animate-in fade-in slide-in-from-top-2">
            <h4 className="text-sm font-bold text-secondary mb-2">Explain it Simply:</h4>
            <p className="text-sm text-slate-800 font-light leading-relaxed">{step.beginnerNote}</p>
          </div>
        )}
        
        <div className="flex flex-wrap gap-3 mt-4">
          <button 
            onClick={() => onToggleComplete(step.step)}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
              isComplete 
                ? 'bg-success/20 text-success border border-success/30 hover:bg-success/30' 
                : 'bg-primary text-white hover:bg-primary/90 shadow-sm'
            }`}
          >
            {isComplete ? '✓ Completed' : 'Mark Complete'}
          </button>
          
          <button 
            onClick={() => setShowSimple(!showSimple)}
            className="flex items-center px-4 py-2.5 rounded-xl text-sm font-bold bg-slate-50 border border-border text-slate-700 hover:bg-white hover:border-slate-300 transition-all"
          >
            <MessageSquare size={16} className="mr-2" />
            {showSimple ? 'Hide Simple Note' : 'Explain Simply'}
          </button>
          
          <a 
            href={step.actionLink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-2.5 rounded-xl text-sm font-bold text-secondary bg-secondary/10 border border-secondary/20 hover:bg-secondary/20 transition-all ml-auto"
          >
            Action Link <ExternalLink size={16} className="ml-1" />
          </a>
        </div>
      </div>
    </div>
  );
};

const FirstTimeVoterPage = () => {
  const [completedSteps, setCompletedSteps] = useState([]);

  const toggleStep = (stepId) => {
    if (completedSteps.includes(stepId)) {
      setCompletedSteps(completedSteps.filter(id => id !== stepId));
    } else {
      setCompletedSteps([...completedSteps, stepId]);
    }
  };

  const progressPercentage = Math.round((completedSteps.length / guideSteps.length) * 100);

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <SectionHeader 
        title="First-Time Voter Guide" 
        subtitle="Your step-by-step checklist to exercising your democratic right for the very first time."
      />
      
      {/* Progress Bar */}
      <div className="bg-white/95 backdrop-blur-2xl border border-border shadow-lg rounded-3xl p-6 mb-10 sticky top-24 z-30">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-extrabold text-primary">Your Progress</h3>
          <span className="font-bold text-secondary text-lg">{progressPercentage}%</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-3 border border-border overflow-hidden">
          <div 
            className="bg-gradient-to-r from-success to-[#34d399] h-full rounded-full transition-all duration-700 ease-out shadow-[0_0_10px_rgba(16,185,129,0.5)]" 
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <p className="text-sm text-slate-500 mt-3 font-light">
          {completedSteps.length === guideSteps.length 
            ? "Amazing! You are fully prepared to vote." 
            : `${completedSteps.length} of ${guideSteps.length} steps completed. Keep going!`}
        </p>
      </div>
      
      <div className="space-y-6 relative">
        {guideSteps.map((step) => (
          <GuideStep 
            key={step.step}
            step={step}
            isComplete={completedSteps.includes(step.step)}
            onToggleComplete={toggleStep}
          />
        ))}
      </div>
      
      {completedSteps.length === guideSteps.length && (
        <div className="mt-12 bg-success/10 border border-success/30 rounded-3xl p-10 text-center animate-in zoom-in-95 duration-500 shadow-sm">
          <h2 className="text-3xl font-extrabold text-success mb-3 tracking-tight">Congratulations! 🎉</h2>
          <p className="text-slate-700 font-light text-lg mb-8">You have completed the preparation guide. You are now an informed citizen ready to participate in the democratic process.</p>
          <Link to="/process" className="inline-flex items-center text-white bg-primary hover:bg-primary/90 shadow-md font-bold py-3.5 px-8 rounded-xl transition-all">
            See the Full Election Process <ArrowRight className="ml-2" size={18} />
          </Link>
        </div>
      )}
    </div>
  );
};

export default FirstTimeVoterPage;
