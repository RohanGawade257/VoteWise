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
      
      <div className="clay-card p-6 md:p-8 mb-8">
        <div className="flex items-start space-x-4 mb-6">
          <ShieldAlert className="text-secondary mt-1 flex-shrink-0" size={24} />
          <div>
            <h3 className="text-xl font-bold text-primary mb-2">Neutral Educational Disclaimer</h3>
            <p className="text-text leading-relaxed">
              VoteWise is a <strong>non-partisan, independent educational platform</strong>. We are not affiliated with the Election Commission of India, any government body, or any political party. Our sole mission is civic education. We do not endorse any candidates, ideologies, or parties. All information provided is for educational purposes only.
            </p>
          </div>
        </div>
      </div>

      <div className="clay-card overflow-hidden">
        <div className="bg-background border-b border-border px-6 py-4 flex justify-between items-center">
          <h3 className="font-bold text-lg text-primary">Verified Data Sources</h3>
          <div className="flex items-center text-sm text-muted bg-surface px-3 py-1 rounded-full border border-border">
            <Calendar size={14} className="mr-2" />
            <span>Last Updated: {currentDate}</span>
          </div>
        </div>
        <div className="divide-y divide-border">
          {sources.map((source, index) => (
            <div key={index} className="p-6 hover:bg-background/50 transition-colors">
              <h4 className="text-lg font-bold text-text mb-1 flex items-center">
                {source.name}
                {source.url !== "#" && (
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="ml-2 text-secondary hover:text-secondary/80">
                    <ExternalLink size={16} />
                  </a>
                )}
              </h4>
              <p className="text-muted">{source.description}</p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-8 text-center text-sm text-muted">
        <p>Information may change dynamically. Always verify critical dates and rules from official sources.</p>
      </div>
    </div>
  );
};

export default SourcesPage;
