import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { ShieldCheck, Info, Users, X, AlertTriangle, ExternalLink } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import partiesData from '../data/parties.json';

const NeutralityBadge = () => (
  <div className="inline-flex items-center bg-blue-50 border border-blue-100 px-4 py-2 rounded-full text-xs font-bold text-primary backdrop-blur-md shadow-sm">
    <ShieldCheck size={16} className="text-secondary mr-2" />
    Neutral Factual Data
  </div>
);

const SourceBadge = ({ source, date }) => (
  <div className="inline-flex items-center text-xs text-slate-500">
    <Info size={14} className="mr-1.5" />
    Source: {source} (Verified: {date})
  </div>
);

const PartyCard = ({ party, isSelected, onClick }) => {
  return (
    <button
      onClick={() => onClick(party)}
      className={`w-full text-left p-6 sm:p-8 transition-all duration-500 flex flex-col h-full rounded-3xl ${
        isSelected 
          ? 'bg-white border border-secondary shadow-md scale-[1.02]' 
          : 'bg-slate-50 backdrop-blur-xl border border-border shadow-sm hover:border-secondary/50 hover:bg-white hover:-translate-y-1'
      }`}
    >
      <div className="flex justify-between items-start mb-6">
        <h3 className="text-2xl font-extrabold text-primary leading-tight tracking-tight">{party.name}</h3>
        <span className="bg-white text-primary text-xs font-bold px-3 py-1.5 rounded-lg border border-border ml-3 shadow-sm">
          {party.abbreviation}
        </span>
      </div>
      
      <div className="mt-auto space-y-3">
        <div className="flex justify-between text-sm border-b border-border pb-3">
          <span className="text-slate-500 font-light">Symbol:</span>
          <span className="font-bold text-primary">{party.symbol}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-500 font-light">Status:</span>
          <span className="font-medium text-primary">{party.status}</span>
        </div>
      </div>
    </button>
  );
};

const PartyDetailPanel = ({ party, onClose }) => {
  if (!party) return null;

  return createPortal(
    <div className="fixed inset-0 z-40 flex items-start justify-center px-4 pb-4 pt-28 sm:pb-6 sm:pt-24 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-300">
      <div className="bg-white border border-border rounded-[2rem] w-full max-w-4xl max-h-[calc(100svh-8rem)] sm:max-h-[calc(100svh-7rem)] flex flex-col shadow-2xl animate-in zoom-in-95 duration-300 overflow-hidden">
        
        {/* Header */}
        <div className="bg-slate-50 border-b border-border p-6 sm:p-8 flex justify-between items-start z-10 shrink-0">
          <div>
            <div className="flex items-center space-x-3 mb-3">
              <span className="bg-blue-50 border border-blue-200 text-secondary text-xs font-bold px-3 py-1.5 rounded-lg shadow-sm">
                {party.abbreviation}
              </span>
              <NeutralityBadge />
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-primary tracking-tight">{party.name}</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2.5 bg-slate-100 rounded-full text-slate-500 hover:text-primary hover:bg-slate-200 border border-border transition-all"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 sm:p-8 space-y-10 overflow-y-auto">
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            <div className="bg-slate-50 p-5 rounded-2xl border border-border shadow-sm">
              <span className="block text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">Symbol Name</span>
              <span className="font-bold text-primary text-lg">{party.symbol}</span>
            </div>
            <div className="bg-slate-50 p-5 rounded-2xl border border-border shadow-sm">
              <span className="block text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">Founded</span>
              <span className="font-bold text-primary text-lg">{party.foundedYear}</span>
            </div>
            <div className="bg-slate-50 p-5 rounded-2xl border border-border shadow-sm">
              <span className="block text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">Status</span>
              <span className="font-bold text-primary text-lg">{party.status}</span>
            </div>
            <div className="bg-slate-50 p-5 rounded-2xl border border-border shadow-sm">
              <span className="block text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">Current Head</span>
              <span className="font-bold text-secondary text-lg">{party.leadership}</span>
            </div>
          </div>

          <div>
            <h4 className="flex items-center font-bold text-xl text-primary mb-4 tracking-tight">
              <Users size={22} className="mr-3 text-secondary" /> Formation Background
            </h4>
            <p className="text-slate-700 font-light leading-relaxed text-lg">{party.founderBackground}</p>
          </div>

          <div>
            <h4 className="flex items-center font-bold text-xl text-primary mb-4 tracking-tight">
              <Info size={22} className="mr-3 text-secondary" /> Stated Focus & Ideology
            </h4>
            <p className="text-slate-700 font-light leading-relaxed text-lg">{party.statedFocus}</p>
          </div>

          <div className="bg-blue-50 p-6 rounded-2xl border border-blue-100 shadow-inner">
            <h4 className="font-bold text-secondary mb-3">Governance Note</h4>
            <p className="text-slate-800 font-light leading-relaxed">{party.governanceNote}</p>
          </div>

          <div className="bg-amber-50 p-5 rounded-2xl border border-amber-200 flex items-start shadow-inner">
            <AlertTriangle className="text-amber-500 mr-4 flex-shrink-0 mt-0.5" size={22} />
            <div>
              <p className="text-sm text-slate-800 font-medium">{party.disclaimer}</p>
              <p className="text-xs text-slate-500 mt-1.5 font-light">Information is restricted to recognized National Parties only.</p>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="bg-slate-100 border-t border-border p-6 sm:p-8 flex flex-col sm:flex-row justify-between items-center gap-4 shrink-0">
          <SourceBadge source={party.source} date={party.lastVerified} />
          <a 
            href={party.officialLink} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm font-bold text-white hover:text-white/90 bg-primary px-5 py-3 rounded-xl border border-transparent shadow-sm transition-all hover:-translate-y-0.5"
          >
            Visit Official Website <ExternalLink size={16} className="ml-2" />
          </a>
        </div>
      </div>
    </div>,
    document.body
  );
};

const PartiesPage = () => {
  const [selectedParty, setSelectedParty] = useState(null);

  useEffect(() => {
    if (!selectedParty) return undefined;

    const scrollY = window.scrollY;
    const { body, documentElement } = document;
    const scrollbarWidth = window.innerWidth - documentElement.clientWidth;
    const previousBodyOverflow = body.style.overflow;
    const previousBodyPaddingRight = body.style.paddingRight;
    const previousBodyOverscroll = body.style.overscrollBehavior;
    const previousHtmlOverflow = documentElement.style.overflow;
    const previousHtmlOverscroll = documentElement.style.overscrollBehavior;

    body.classList.add('party-modal-open');
    documentElement.style.overflow = 'hidden';
    documentElement.style.overscrollBehavior = 'none';
    body.style.overflow = 'hidden';
    body.style.overscrollBehavior = 'none';
    if (scrollbarWidth > 0) {
      body.style.paddingRight = `${scrollbarWidth}px`;
    }

    return () => {
      body.classList.remove('party-modal-open');
      documentElement.style.overflow = previousHtmlOverflow;
      documentElement.style.overscrollBehavior = previousHtmlOverscroll;
      body.style.overflow = previousBodyOverflow;
      body.style.paddingRight = previousBodyPaddingRight;
      body.style.overscrollBehavior = previousBodyOverscroll;
      window.scrollTo(0, scrollY);
    };
  }, [selectedParty]);

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
      
      <p className="text-center text-slate-600 font-light max-w-2xl mx-auto mb-12 text-lg">
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
