import React, { useState } from 'react';
import { CheckCircle, Circle, ExternalLink, MessageSquare, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import SectionHeader from '../components/SectionHeader';
import guideSteps from '../data/guideSteps.json';

const GuideStep = ({ step, isComplete, onToggleComplete }) => {
  const [showSimple, setShowSimple] = useState(false);

  return (
    <div className={`relative flex gap-6 p-6 rounded-2xl border-2 transition-all duration-300 ${
      isComplete 
        ? 'border-success/30 bg-success/5' 
        : 'border-border bg-surface shadow-sm hover:border-secondary/30'
    }`}>
      {/* Progress Line & Circle */}
      <div className="flex flex-col items-center">
        <button 
          onClick={() => onToggleComplete(step.step)}
          className="relative z-10 flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-success rounded-full bg-surface"
          aria-label={isComplete ? "Mark as incomplete" : "Mark as complete"}
        >
          {isComplete ? (
            <CheckCircle className="text-success w-8 h-8" />
          ) : (
            <Circle className="text-border hover:text-secondary transition-colors w-8 h-8" />
          )}
        </button>
        {step.step !== 7 && (
          <div className={`w-0.5 h-full mt-2 -mb-8 ${isComplete ? 'bg-success/30' : 'bg-border'}`}></div>
        )}
      </div>

      {/* Content */}
      <div className="flex-grow pb-4">
        <div className="flex items-center space-x-2 mb-1">
          <span className="text-sm font-bold text-muted uppercase tracking-wider">Step {step.step}</span>
        </div>
        <h3 className={`text-xl font-bold mb-3 ${isComplete ? 'text-success' : 'text-primary'}`}>
          {step.title}
        </h3>
        
        <p className="text-text leading-relaxed mb-4">{step.explanation}</p>
        
        {showSimple && (
          <div className="bg-primary/5 p-4 rounded-lg mb-4 animate-in fade-in slide-in-from-top-2">
            <h4 className="text-sm font-bold text-primary mb-1">Explain it Simply:</h4>
            <p className="text-sm text-text/80">{step.beginnerNote}</p>
          </div>
        )}
        
        <div className="flex flex-wrap gap-3 mt-4">
          <button 
            onClick={() => onToggleComplete(step.step)}
            className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${
              isComplete 
                ? 'bg-success/10 text-success hover:bg-success/20' 
                : 'bg-primary text-surface hover:bg-primary/90'
            }`}
          >
            {isComplete ? '✓ Completed' : 'Mark Complete'}
          </button>
          
          <button 
            onClick={() => setShowSimple(!showSimple)}
            className="flex items-center px-4 py-2 rounded-lg text-sm font-bold bg-background border border-border text-text hover:bg-border/50 transition-colors"
          >
            <MessageSquare size={16} className="mr-2" />
            {showSimple ? 'Hide Simple Note' : 'Explain Simply'}
          </button>
          
          <a 
            href={step.actionLink}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-2 rounded-lg text-sm font-bold text-secondary hover:bg-secondary/10 transition-colors ml-auto"
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
      <div className="clay-card p-6 mb-10 sticky top-20 z-30">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-bold text-primary">Your Progress</h3>
          <span className="font-bold text-secondary">{progressPercentage}%</span>
        </div>
        <div className="w-full bg-background rounded-full h-3">
          <div 
            className="bg-success h-3 rounded-full transition-all duration-500 ease-out" 
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <p className="text-sm text-muted mt-2">
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
        <div className="mt-12 bg-success/10 border border-success/30 rounded-2xl p-8 text-center animate-in zoom-in-95 duration-500">
          <h2 className="text-2xl font-bold text-success mb-2">Congratulations! 🎉</h2>
          <p className="text-text mb-6">You have completed the preparation guide. You are now an informed citizen ready to participate in the democratic process.</p>
          <Link to="/process" className="inline-flex items-center text-surface bg-success hover:bg-success/90 font-bold py-3 px-6 rounded-lg transition-colors">
            See the Full Election Process <ArrowRight className="ml-2" size={18} />
          </Link>
        </div>
      )}
    </div>
  );
};

export default FirstTimeVoterPage;
