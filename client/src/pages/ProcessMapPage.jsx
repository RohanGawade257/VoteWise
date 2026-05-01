import React, { useState } from 'react';
import { X, ArrowRight, Info, BookOpen, ExternalLink } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import processNodes from '../data/processNodes.json';

const ProcessNode = ({ node, index, isSelected, onClick }) => {
  return (
    <button
      onClick={() => onClick(node)}
      aria-expanded={isSelected}
      aria-controls={`step-details-${node.id}`}
      className={`relative w-full text-left p-4 rounded-xl border-2 transition-all duration-300 ${
        isSelected 
          ? 'border-secondary bg-secondary/10 shadow-md' 
          : 'border-border bg-surface hover:border-secondary/50 hover:shadow-sm'
      }`}
    >
      <div className="flex items-center space-x-3">
        <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
          isSelected ? 'bg-secondary text-surface' : 'bg-primary/10 text-primary'
        }`}>
          {index + 1}
        </div>
        <h3 className={`font-bold ${isSelected ? 'text-secondary' : 'text-text'}`}>
          {node.title}
        </h3>
      </div>
      
      {/* Desktop connector line (hidden on mobile) */}
      {index < 11 && (
        <div className="hidden sm:block absolute -right-6 top-1/2 w-6 border-t-2 border-dashed border-border" />
      )}
    </button>
  );
};

const NodeDetailPanel = ({ node, onClose }) => {
  if (!node) return null;
  
  return (
    <div className="bg-surface rounded-2xl shadow-xl border border-border p-6 mt-6 md:mt-0 md:sticky md:top-24 animate-in slide-in-from-bottom-4 md:slide-in-from-right-8 duration-300">
      <div className="flex justify-between items-start mb-6 border-b border-border pb-4">
        <div>
          <div className="text-xs font-bold text-secondary uppercase tracking-wider mb-1">Step {node.id}</div>
          <h2 className="text-2xl font-bold text-primary">{node.title}</h2>
        </div>
        <button 
          onClick={onClose}
          className="p-2 text-muted hover:text-text hover:bg-background rounded-full transition-colors"
          aria-label="Close panel"
        >
          <X size={20} />
        </button>
      </div>
      
      <div className="space-y-6">
        <div>
          <h4 className="flex items-center font-semibold text-text mb-2">
            <Info size={18} className="text-secondary mr-2" /> 
            Simple Explanation
          </h4>
          <p className="text-muted leading-relaxed">{node.simpleExplanation}</p>
        </div>
        
        <div>
          <h4 className="flex items-center font-semibold text-text mb-2">
            <BookOpen size={18} className="text-primary mr-2" /> 
            Why it Matters
          </h4>
          <p className="text-muted leading-relaxed">{node.whyItMatters}</p>
        </div>
        
        <div className="bg-warning/10 border border-warning/20 rounded-lg p-4">
          <h4 className="font-semibold text-warning mb-1">What Voters Should Know:</h4>
          <p className="text-text text-sm">{node.whatVoterShouldKnow}</p>
        </div>
        
        <div className="bg-primary/5 rounded-lg p-4">
          <h4 className="font-semibold text-primary mb-1 text-sm">🔰 Beginner Note:</h4>
          <p className="text-muted text-sm italic">{node.beginnerNote}</p>
        </div>
        
        <div className="pt-4 border-t border-border flex justify-between items-center text-xs text-muted">
          <span className="flex items-center">
            Source: {node.source}
          </span>
          {node.officialUrl && (
            <a href={node.officialUrl} target="_blank" rel="noopener noreferrer" className="flex items-center text-secondary hover:underline">
              Official Details <ExternalLink size={12} className="ml-1" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

const ProcessMapPage = () => {
  const [selectedNode, setSelectedNode] = useState(processNodes[0]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <SectionHeader 
        title="Election Process Map" 
        subtitle="A visual guide to how elections are conducted in India, step by step."
      />
      
      <div className="mt-8 flex flex-col md:flex-row gap-8">
        {/* Map Area */}
        <div className="w-full md:w-1/2 lg:w-3/5">
          <div className="bg-background rounded-2xl p-6 border border-border">
            <h3 className="text-center font-bold text-muted uppercase tracking-widest mb-8">The Electoral Lifecycle</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-x-12 gap-y-6 relative">
              {processNodes.map((node, index) => (
                <div key={node.id} className="relative z-10">
                  <ProcessNode 
                    node={node} 
                    index={index}
                    isSelected={selectedNode?.id === node.id}
                    onClick={(n) => setSelectedNode(selectedNode?.id === n.id ? null : n)}
                  />
                  
                  {/* Mobile Accordion Content */}
                  {selectedNode?.id === node.id && (
                    <div 
                      id={`step-details-${node.id}`}
                      className="md:hidden mt-2 p-4 bg-surface rounded-xl border border-secondary/30 shadow-inner animate-in slide-in-from-top-2 duration-200"
                    >
                      <div className="space-y-4">
                        <div>
                          <h4 className="flex items-center font-semibold text-text mb-1 text-sm">
                            <Info size={16} className="text-secondary mr-2" /> 
                            Simple Explanation
                          </h4>
                          <p className="text-muted text-sm leading-relaxed">{node.simpleExplanation}</p>
                        </div>
                        
                        <div>
                          <h4 className="flex items-center font-semibold text-text mb-1 text-sm">
                            <BookOpen size={16} className="text-primary mr-2" /> 
                            Why it Matters
                          </h4>
                          <p className="text-muted text-sm leading-relaxed">{node.whyItMatters}</p>
                        </div>
                        
                        <div className="bg-warning/10 border border-warning/20 rounded-lg p-3">
                          <h4 className="font-semibold text-warning mb-1 text-sm">What Voters Should Know:</h4>
                          <p className="text-text text-sm">{node.whatVoterShouldKnow}</p>
                        </div>
                        
                        <div className="bg-primary/5 rounded-lg p-3">
                          <h4 className="font-semibold text-primary mb-1 text-xs">🔰 Beginner Note:</h4>
                          <p className="text-muted text-xs italic">{node.beginnerNote}</p>
                        </div>
                        
                        <div className="pt-2 border-t border-secondary/10 flex justify-between items-center text-xs text-muted">
                          <span className="flex items-center">
                            Source: {node.source}
                          </span>
                          {node.officialUrl && (
                            <a href={node.officialUrl} target="_blank" rel="noopener noreferrer" className="flex items-center text-secondary hover:underline">
                              Official Details <ExternalLink size={12} className="ml-1" />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Mobile connector line */}
                  {index < processNodes.length - 1 && (
                    <div className={`sm:hidden absolute left-8 ${selectedNode?.id === node.id ? 'top-[4rem]' : 'top-full'} h-6 border-l-2 border-dashed border-border`} style={{ zIndex: -1 }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Detail Panel Area (Desktop Only) */}
        <div className="hidden md:block w-full md:w-1/2 lg:w-2/5">
          <NodeDetailPanel 
            node={selectedNode} 
            onClose={() => setSelectedNode(null)} 
          />
        </div>
      </div>
    </div>
  );
};

export default ProcessMapPage;
