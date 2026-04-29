import React, { useState } from 'react';
import { ShieldCheck, Info, Users, X, AlertTriangle, ExternalLink } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import partiesData from '../data/parties.json';

const NeutralityBadge = () => (
  <div className="inline-flex items-center bg-background border border-border px-3 py-1.5 rounded-full text-xs font-medium text-muted">
    <ShieldCheck size={14} className="text-success mr-1.5" />
    Neutral Factual Data
  </div>
);

const SourceBadge = ({ source, date }) => (
  <div className="inline-flex items-center text-xs text-muted">
    <Info size={12} className="mr-1" />
    Source: {source} (Verified: {date})
  </div>
);

const PartyCard = ({ party, isSelected, onClick }) => {
  return (
    <button
      onClick={() => onClick(party)}
      className={`w-full text-left p-6 rounded-2xl border-2 transition-all duration-300 flex flex-col h-full ${
        isSelected 
          ? 'border-primary bg-primary/5 shadow-md' 
          : 'border-border bg-surface hover:border-primary/30 hover:shadow-sm'
      }`}
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-xl font-bold text-primary leading-tight">{party.name}</h3>
        <span className="bg-background text-text text-xs font-bold px-2 py-1 rounded border border-border ml-2">
          {party.abbreviation}
        </span>
      </div>
      
      <div className="mt-auto space-y-2">
        <div className="flex justify-between text-sm border-b border-border pb-2">
          <span className="text-muted">Symbol:</span>
          <span className="font-bold text-text">{party.symbol}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted">Status:</span>
          <span className="font-medium text-text">{party.status}</span>
        </div>
      </div>
    </button>
  );
};

const PartyDetailPanel = ({ party, onClose }) => {
  if (!party) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/20 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-surface w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border border-border animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="sticky top-0 bg-surface border-b border-border p-6 flex justify-between items-start z-10">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <span className="bg-primary/10 text-primary text-xs font-bold px-2 py-1 rounded">
                {party.abbreviation}
              </span>
              <NeutralityBadge />
            </div>
            <h2 className="text-3xl font-bold text-primary">{party.name}</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 bg-background rounded-full text-muted hover:text-text transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8">
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-background p-4 rounded-xl border border-border">
              <span className="block text-xs text-muted mb-1 uppercase tracking-wider">Symbol Name</span>
              <span className="font-bold text-text">{party.symbol}</span>
            </div>
            <div className="bg-background p-4 rounded-xl border border-border">
              <span className="block text-xs text-muted mb-1 uppercase tracking-wider">Founded</span>
              <span className="font-bold text-text">{party.foundedYear}</span>
            </div>
            <div className="bg-background p-4 rounded-xl border border-border">
              <span className="block text-xs text-muted mb-1 uppercase tracking-wider">Status</span>
              <span className="font-bold text-text">{party.status}</span>
            </div>
            <div className="bg-background p-4 rounded-xl border border-border">
              <span className="block text-xs text-muted mb-1 uppercase tracking-wider">Current Head</span>
              <span className="font-bold text-warning">{party.leadership}</span>
            </div>
          </div>

          <div>
            <h4 className="flex items-center font-bold text-lg text-primary mb-3">
              <Users size={20} className="mr-2" /> Formation Background
            </h4>
            <p className="text-text leading-relaxed">{party.founderBackground}</p>
          </div>

          <div>
            <h4 className="flex items-center font-bold text-lg text-primary mb-3">
              <Info size={20} className="mr-2" /> Stated Focus & Ideology
            </h4>
            <p className="text-text leading-relaxed">{party.statedFocus}</p>
          </div>

          <div className="bg-primary/5 p-5 rounded-xl border border-primary/10">
            <h4 className="font-bold text-primary mb-2">Governance Note</h4>
            <p className="text-text">{party.governanceNote}</p>
          </div>

          <div className="bg-warning/10 p-4 rounded-xl border border-warning/20 flex items-start">
            <AlertTriangle className="text-warning mr-3 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <p className="text-sm text-text font-medium">{party.disclaimer}</p>
              <p className="text-xs text-muted mt-1">Information is restricted to recognized National Parties only.</p>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="bg-background border-t border-border p-6 flex flex-col sm:flex-row justify-between items-center gap-4 rounded-b-2xl">
          <SourceBadge source={party.source} date={party.lastVerified} />
          <a 
            href={party.officialLink} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm font-bold text-secondary hover:text-secondary/80 bg-surface px-4 py-2 rounded border border-border hover:border-secondary transition-all"
          >
            Visit Official Website <ExternalLink size={16} className="ml-2" />
          </a>
        </div>
      </div>
    </div>
  );
};

const PartiesPage = () => {
  const [selectedParty, setSelectedParty] = useState(null);

  return (
    <div className="max-w-6xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <div className="text-center mb-8">
        <NeutralityBadge />
      </div>
      <SectionHeader 
        title="National Political Parties" 
        subtitle="A neutral, factual directory of India's recognized national parties."
        centered={true}
      />
      
      <p className="text-center text-muted max-w-2xl mx-auto mb-12">
        This directory strictly lists the six recognized National Parties as classified by the Election Commission of India. We do not use party colors, rankings, or real logos to maintain strict neutrality.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {partiesData.map((party) => (
          <PartyCard 
            key={party.id} 
            party={party} 
            isSelected={selectedParty?.id === party.id}
            onClick={setSelectedParty}
          />
        ))}
      </div>

      <PartyDetailPanel 
        party={selectedParty} 
        onClose={() => setSelectedParty(null)} 
      />
    </div>
  );
};

export default PartiesPage;
