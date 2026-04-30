import React from 'react';
import { ExternalLink, ShieldAlert, Calendar } from 'lucide-react';
import SectionHeader from '../components/SectionHeader';

const SourcesPage = () => {
  const currentDate = new Date().toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const sources = [
    {
      name: "Election Commission of India (ECI)",
      url: "https://eci.gov.in/",
      description: "Primary constitutional authority for conducting elections in India."
    },
    {
      name: "Voters' Services Portal",
      url: "https://voters.eci.gov.in/",
      description: "Official portal for voter registration, electoral roll search, and EPIC download."
    },
    {
      name: "SVEEP (Systematic Voters' Education and Electoral Participation)",
      url: "https://ecisveep.nic.in/",
      description: "Flagship program of ECI for voter education and spreading voter awareness."
    },
    {
      name: "Results Portal",
      url: "https://results.eci.gov.in/",
      description: "Official portal for real-time election counting trends and results."
    },
    {
      name: "Official Party Websites",
      url: "#",
      description: "Information regarding political parties is sourced from their respective official websites and ECI affidavits."
    }
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
      <SectionHeader 
        title="Sources & Methodology" 
        subtitle="VoteWise relies strictly on official, verified data to ensure neutrality."
      />
      
      <div className="bg-white backdrop-blur-xl border border-border shadow-md rounded-3xl p-6 md:p-8 mb-10">
        <div className="flex items-start space-x-5 mb-2">
          <div className="bg-blue-50 p-3 rounded-2xl flex-shrink-0 mt-1 shadow-inner border border-blue-100">
            <ShieldAlert className="text-secondary drop-shadow-sm" size={28} />
          </div>
          <div>
            <h3 className="text-2xl font-extrabold text-primary mb-3 tracking-tight">Neutral Educational Disclaimer</h3>
            <p className="text-slate-700 font-light leading-relaxed text-lg">
              VoteWise is a <strong>non-partisan, independent educational platform</strong>. We are not affiliated with the Election Commission of India, any government body, or any political party. Our sole mission is civic education. We do not endorse any candidates, ideologies, or parties. All information provided is for educational purposes only.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white backdrop-blur-xl border border-border shadow-md rounded-3xl overflow-hidden">
        <div className="bg-slate-50 border-b border-border px-6 sm:px-8 py-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="font-extrabold text-xl text-primary">Verified Data Sources</h3>
          <div className="flex items-center text-xs font-bold uppercase tracking-wider text-slate-500 bg-white px-4 py-2 rounded-full border border-border shadow-sm">
            <Calendar size={14} className="mr-2 text-secondary" />
            <span>Last Updated: {currentDate}</span>
          </div>
        </div>
        <div className="divide-y divide-border">
          {sources.map((source, index) => (
            <div key={index} className="p-6 sm:p-8 hover:bg-slate-50 transition-all">
              <h4 className="text-xl font-bold text-primary mb-2 flex items-center">
                {source.name}
                {source.url !== "#" && (
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="ml-3 text-secondary hover:text-white transition-colors bg-blue-50 p-1.5 rounded-lg border border-blue-100 hover:bg-primary hover:border-primary">
                    <ExternalLink size={16} />
                  </a>
                )}
              </h4>
              <p className="text-slate-600 font-light leading-relaxed">{source.description}</p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-8 text-center text-sm text-slate-400 font-light">
        <p>Information may change dynamically. Always verify critical dates and rules from official sources.</p>
      </div>
    </div>
  );
};

export default SourcesPage;
