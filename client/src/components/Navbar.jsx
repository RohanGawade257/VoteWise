import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import logoImg from '../assets/votewise-logo.svg';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const links = [
    { name: 'Home', path: '/' },
    { name: 'Timeline', path: '/timeline' },
    { name: 'First-Time Voters', path: '/first-time-voter' },
    { name: 'Parties', path: '/parties' },
    { name: 'Basics', path: '/basics' },
    { name: 'Ask Assistant', path: '/chat' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className={`sticky top-0 left-0 w-full z-50 transition-all duration-500 flex justify-center pt-4 pb-4`}>
      <div className={`w-full transition-all duration-500 ease-[cubic-bezier(0.25,0.8,0.25,1)] ${
        scrolled 
          ? 'max-w-5xl mx-4 sm:mx-6 rounded-3xl bg-white/40 backdrop-blur-lg border border-white/60 shadow-[0_8px_32px_rgba(0,0,0,0.1)]' 
          : 'max-w-full bg-white/20 backdrop-blur-md border-b border-white/30'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`flex justify-between items-center transition-all duration-500 ${scrolled ? 'h-16' : 'h-20'}`}>
            <div className="flex items-center">
              <Link to="/" className="flex items-center group gap-3">
                <div className="bg-slate-50 p-2 rounded-xl border border-border shadow-sm group-hover:bg-white transition-all duration-300">
                  <img src={logoImg} alt="VoteWise Logo" className="h-7 w-auto sm:h-8 object-contain" />
                </div>
                <span className="font-extrabold text-xl sm:text-2xl tracking-tight text-primary group-hover:text-secondary transition-colors font-sans">
                  Vote<span className="text-secondary">Wise</span>
                </span>
              </Link>
            </div>
            
            {/* Desktop Menu */}
            <div className="hidden lg:flex items-center space-x-1">
              {links.map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`text-sm font-semibold px-4 py-2 rounded-full transition-all duration-300 ${
                    isActive(link.path) 
                      ? 'text-secondary bg-blue-50 border border-blue-100 shadow-inner' 
                      : 'text-muted hover:text-primary hover:bg-slate-50'
                  }`}
                >
                  {link.name}
                </Link>
              ))}
            </div>

            {/* Mobile menu button */}
            <div className="flex items-center lg:hidden">
              <button
                onClick={() => setIsOpen(!isOpen)}
                className="text-muted hover:text-primary transition-colors p-2 rounded-xl bg-slate-50 border border-border hover:bg-white"
              >
                {isOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        <div className={`lg:hidden overflow-hidden transition-all duration-500 ease-in-out ${isOpen ? 'max-h-[400px] border-t border-border bg-white/95 backdrop-blur-2xl rounded-b-3xl' : 'max-h-0'}`}>
          <div className="px-4 pt-4 pb-6 space-y-2">
            {links.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                onClick={() => setIsOpen(false)}
                className={`block px-5 py-3.5 rounded-2xl text-base font-bold transition-all duration-300 ${
                  isActive(link.path)
                    ? 'bg-blue-50 text-secondary border border-blue-100'
                    : 'text-muted hover:bg-slate-50 hover:text-primary border border-transparent'
                }`}
              >
                {link.name}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
