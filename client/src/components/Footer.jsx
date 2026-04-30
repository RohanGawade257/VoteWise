import React from 'react';
import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import logoImg from '../assets/votewise-logo.png';

const Footer = () => {
  return (
    <footer className="bg-gradient-to-b from-[#0f213a] to-primary text-surface mt-auto relative overflow-hidden">
      {/* Decorative background circle */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-secondary/10 rounded-full blur-[100px] translate-x-1/2 -translate-y-1/2"></div>
      
      <div className="max-w-7xl mx-auto px-4 py-16 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 lg:gap-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center mb-6 gap-3">
              <div className="bg-white/10 p-1.5 rounded-xl backdrop-blur-sm">
                <img src={logoImg} alt="VoteWise Logo" className="h-10 w-10 object-contain filter brightness-0 invert" />
              </div>
              <span className="font-extrabold text-2xl tracking-tight text-white">
                VoteWise
              </span>
            </div>
            <p className="text-surface/70 text-base max-w-md leading-relaxed font-light">
              A beautifully simple, neutral, and non-partisan educational platform dedicated to helping Indian citizens understand the election process and exercise their right to vote effectively.
            </p>
          </div>
          
          <div>
            <h3 className="font-bold text-lg mb-6 text-surface">Quick Links</h3>
            <ul className="space-y-3 text-sm text-surface/70">
              <li><Link to="/process" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">Election Process Map</Link></li>
              <li><Link to="/timeline" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">Important Dates</Link></li>
              <li><Link to="/faq" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">FAQ</Link></li>
              <li><Link to="/sources" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">Sources & Disclaimers</Link></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-bold text-lg mb-6 text-surface">Resources</h3>
            <ul className="space-y-3 text-sm text-surface/70">
              <li><a href="https://eci.gov.in" target="_blank" rel="noopener noreferrer" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">Election Commission of India</a></li>
              <li><a href="https://voters.eci.gov.in/" target="_blank" rel="noopener noreferrer" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">Voter Portal</a></li>
              <li><Link to="/chat" className="hover:text-secondary transition-colors inline-block transform hover:translate-x-1 duration-200">Ask VoteWise Assistant</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-surface/10 mt-16 pt-8 flex flex-col md:flex-row justify-between items-center text-sm text-surface/50 font-light">
          <p>&copy; {new Date().getFullYear()} VoteWise. Non-partisan civic tech project.</p>
          <p className="flex items-center mt-4 md:mt-0">
            Built with <Heart size={14} className="mx-1.5 text-secondary animate-pulse" /> for Indian Democracy
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
