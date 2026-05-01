import React, { useState, useEffect } from 'react';
import { MapPin, Globe, Users, FileText, Info, Building, Map, Phone, AlertTriangle, ChevronDown, ExternalLink } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import { getUserState, setUserState } from '../utils/preferences';
import { stateElectionResources, COMMON_LINKS } from '../data/stateElectionResources';

const Card = ({ title, icon: Icon, children }) => (
  <div className="clay-card p-6 h-full flex flex-col">
    <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border/50">
      <div className="bg-secondary/10 p-2.5 rounded-xl text-secondary">
        <Icon size={24} />
      </div>
      <h3 className="text-xl font-bold text-primary">{title}</h3>
    </div>
    <div className="flex-grow space-y-4 text-muted">
      {children}
    </div>
  </div>
);

const SafeLink = ({ href, children, className = "" }) => (
  <a 
    href={href} 
    target="_blank" 
    rel="noopener noreferrer"
    className={`inline-flex items-center text-secondary font-semibold hover:text-[#2563EB] hover:underline ${className}`}
  >
    {children} <ExternalLink size={14} className="ml-1" />
  </a>
);

export default function LocalHelpPage() {
  const [selectedState, setSelectedState] = useState('');
  const [isEditingState, setIsEditingState] = useState(false);
  const [stateSearch, setStateSearch] = useState('');

  useEffect(() => {
    const savedState = getUserState();
    if (savedState && stateElectionResources.some(s => s.name === savedState)) {
      setSelectedState(savedState);
    } else {
      setIsEditingState(true);
    }
  }, []);

  const handleStateSelect = (stateName) => {
    setSelectedState(stateName);
    setUserState(stateName);
    setIsEditingState(false);
    setStateSearch('');
  };

  const currentStateData = stateElectionResources.find(s => s.name === selectedState);

  const filteredStates = stateElectionResources.filter(s => 
    s.name.toLowerCase().includes(stateSearch.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8 animate-in fade-in duration-500">
      <SectionHeader 
        title="Local Election Help" 
        subtitle="Find official election resources and guidance for your state or union territory."
      />

      <div className="mt-10 mb-8 max-w-xl mx-auto">
        {(!selectedState || isEditingState) ? (
          <div className="clay-card p-6 shadow-lg animate-in zoom-in-95 duration-300">
            <h3 className="text-lg font-bold text-primary flex items-center gap-2 mb-4">
              <MapPin className="text-secondary" />
              Select Your State or UT
            </h3>
            <div className="relative mb-4">
              <input
                type="text"
                value={stateSearch}
                onChange={(e) => setStateSearch(e.target.value)}
                placeholder="Search states..."
                className="w-full bg-slate-50 border-2 border-slate-200 text-slate-800 py-3 px-4 rounded-xl font-medium focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary"
              />
            </div>
            <div className="max-h-[300px] overflow-y-auto space-y-1 pr-2">
              {filteredStates.map(state => (
                <button
                  key={state.name}
                  onClick={() => handleStateSelect(state.name)}
                  className="w-full text-left px-4 py-3 rounded-xl font-semibold text-slate-700 hover:bg-secondary/10 hover:text-secondary transition-colors"
                >
                  {state.name}
                </button>
              ))}
              {filteredStates.length === 0 && (
                <p className="text-muted text-center py-4">No states found.</p>
              )}
            </div>
            {selectedState && (
              <div className="mt-4 pt-4 border-t border-border/50 text-center">
                <button 
                  onClick={() => setIsEditingState(false)}
                  className="text-muted hover:text-primary font-semibold"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row items-center justify-between bg-white/60 backdrop-blur-md border border-white/80 p-4 sm:p-5 rounded-2xl shadow-sm">
            <div className="flex items-center gap-3 mb-3 sm:mb-0">
              <div className="bg-emerald-100 p-2 rounded-full text-emerald-600">
                <MapPin size={20} />
              </div>
              <div>
                <p className="text-xs font-bold text-muted uppercase tracking-wider">Current Selection</p>
                <p className="text-lg font-extrabold text-primary">{selectedState}</p>
              </div>
            </div>
            <button 
              onClick={() => setIsEditingState(true)}
              className="flex items-center gap-1 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold transition-colors text-sm"
            >
              Change State <ChevronDown size={16} />
            </button>
          </div>
        )}
      </div>

      {selectedState && !isEditingState && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 mt-10">
          
          <Card title="State Election Office" icon={Building}>
            <p>
              The Chief Electoral Officer (CEO) is responsible for conducting fair elections in your state.
            </p>
            {currentStateData?.ceoUrl ? (
              <div className="mt-4 p-4 bg-blue-50/50 rounded-xl border border-blue-100 flex flex-col gap-3">
                <div>
                  <p className="font-semibold text-slate-800 mb-1">Official CEO Website:</p>
                  <SafeLink href={currentStateData.ceoUrl}>
                    Visit {selectedState} CEO Portal
                  </SafeLink>
                </div>
                {currentStateData.contactUrl && (
                  <div className="pt-3 border-t border-blue-100/50">
                    <SafeLink href={currentStateData.contactUrl}>
                      Contact State Election Office
                    </SafeLink>
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-4 p-4 bg-amber-50/50 rounded-xl border border-amber-100 flex flex-col gap-2">
                <p className="text-amber-800 text-sm font-medium mb-1">
                  We don't have the specific URL for this state. Please visit the official ECI portals:
                </p>
                <SafeLink href={COMMON_LINKS.eciVoterPortal} className="text-sm">ECI Voters Portal</SafeLink>
                <SafeLink href={COMMON_LINKS.deoFallbackUrl} className="text-sm">ECI Officers Directory</SafeLink>
              </div>
            )}
            <p className="text-sm mt-4">
              Here you can find state-specific announcements, contact directories for District Election Officers (DEOs), and local voter forms.
            </p>
          </Card>

          <Card title="Voter Services" icon={Users}>
            <p>Access official ECI services directly:</p>
            <ul className="space-y-3 mt-4">
              <li className="flex items-start gap-2">
                <div className="mt-1 w-1.5 h-1.5 bg-secondary rounded-full flex-shrink-0" />
                <SafeLink href="https://voters.eci.gov.in/form6">Register as a New Voter (Form 6)</SafeLink>
              </li>
              <li className="flex items-start gap-2">
                <div className="mt-1 w-1.5 h-1.5 bg-secondary rounded-full flex-shrink-0" />
                <SafeLink href="https://electoralsearch.eci.gov.in/">Check your name in Voter List</SafeLink>
              </li>
              <li className="flex items-start gap-2">
                <div className="mt-1 w-1.5 h-1.5 bg-secondary rounded-full flex-shrink-0" />
                <SafeLink href="https://electoralsearch.eci.gov.in/pollingstation">Find your Polling Station</SafeLink>
              </li>
              <li className="flex items-start gap-2">
                <div className="mt-1 w-1.5 h-1.5 bg-secondary rounded-full flex-shrink-0" />
                <SafeLink href="https://voters.eci.gov.in/downloadform">Download other Voter Forms</SafeLink>
              </li>
            </ul>
          </Card>

          <Card title="Offline Help Guidance" icon={Map}>
            <p>
              If you prefer offline assistance or need to resolve an issue in person, you can contact official election authorities in your district:
            </p>
            <div className="space-y-4 mt-4">
              <a 
                href={currentStateData?.bloUrl || COMMON_LINKS.bloFallbackUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-slate-50 hover:bg-white p-4 rounded-xl border border-slate-200 hover:border-secondary hover:shadow-md transition-all group"
              >
                <h4 className="font-bold text-slate-800 text-sm mb-1 group-hover:text-secondary transition-colors">Booth Level Officer (BLO)</h4>
                <p className="text-xs text-muted mb-2">Your local representative. They can help with forms and verify your address.</p>
                <div className="inline-flex items-center text-sm text-secondary font-semibold group-hover:text-[#2563EB]">
                  Find / contact BLO <ExternalLink size={14} className="ml-1" />
                </div>
              </a>
              
              <a 
                href={currentStateData?.deoUrl || COMMON_LINKS.deoFallbackUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-slate-50 hover:bg-white p-4 rounded-xl border border-slate-200 hover:border-secondary hover:shadow-md transition-all group"
              >
                <h4 className="font-bold text-slate-800 text-sm mb-1 group-hover:text-secondary transition-colors">District Election Office</h4>
                <p className="text-xs text-muted mb-2">Usually located at the District Magistrate / Collector's office.</p>
                <div className="inline-flex items-center text-sm text-secondary font-semibold group-hover:text-[#2563EB]">
                  View district election contacts <ExternalLink size={14} className="ml-1" />
                </div>
              </a>
            </div>
            <p className="text-xs text-slate-500 italic mt-3 bg-slate-50 p-3 rounded-lg border border-slate-100">
              State-specific BLO/DEO pages may vary by state. If a direct list is unavailable, VoteWise links to official ECI fallback services.
            </p>
          </Card>

          <Card title="Important Official Links" icon={Globe}>
            <p>National portals managed by the Election Commission of India:</p>
            <div className="space-y-4 mt-4">
              <div className="flex flex-col">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Main Portal</span>
                <SafeLink href={COMMON_LINKS.eciVoterPortal}>Voters' Services Portal</SafeLink>
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Contact & Support</span>
                <SafeLink href={COMMON_LINKS.eciContactUrl}>ECI Official Contact Page</SafeLink>
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Directory</span>
                <SafeLink href={COMMON_LINKS.deoFallbackUrl}>ECI Officers Directory</SafeLink>
              </div>
            </div>
          </Card>

        </div>
      )}

      {selectedState && !isEditingState && (
        <div className="mt-12 bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-xl max-w-4xl mx-auto flex items-start gap-3">
          <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h4 className="font-bold text-amber-800 text-sm">Disclaimer</h4>
            <p className="text-sm text-amber-700 mt-1">
              VoteWise is a non-partisan educational platform and does not replace official election authorities. Always verify dates, addresses, and procedures directly from the Election Commission of India or your official state CEO website.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
