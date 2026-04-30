import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import logoImg from '../assets/votewise-logo.png';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
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
    <nav className={`sticky top-0 z-40 transition-all duration-300 ${scrolled ? 'bg-surface/80 backdrop-blur-xl border-b border-border shadow-sm py-2' : 'bg-surface border-b border-transparent py-3'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-12">
          <div className="flex items-center">
            <Link to="/" className="flex items-center group gap-3">
              <div className="bg-surface/50 backdrop-blur-md p-1.5 rounded-xl border border-border/50 shadow-sm group-hover:shadow-md transition-all duration-300 group-hover:scale-105">
                <img src={logoImg} alt="VoteWise Logo" className="h-8 w-8 sm:h-9 sm:w-9 object-contain" />
              </div>
              <span className="font-extrabold text-xl sm:text-2xl tracking-tight text-primary group-hover:text-secondary transition-colors">
                Vote<span className="text-secondary">Wise</span>
              </span>
            </Link>
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden md:flex items-center space-x-1 lg:space-x-4">
            {links.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className={`text-sm lg:text-base font-semibold px-3 py-2 rounded-lg transition-all duration-300 ${
                  isActive(link.path) 
                    ? 'text-secondary bg-secondary/10' 
                    : 'text-text hover:text-secondary hover:bg-secondary/5'
                }`}
              >
                {link.name}
              </Link>
            ))}
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-text hover:text-secondary transition-colors p-2 rounded-lg hover:bg-secondary/10"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <div className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-96 border-b border-border bg-surface/95 backdrop-blur-xl' : 'max-h-0'}`}>
        <div className="px-4 pt-2 pb-6 space-y-2">
          {links.map((link) => (
            <Link
              key={link.name}
              to={link.path}
              onClick={() => setIsOpen(false)}
              className={`block px-4 py-3 rounded-xl text-base font-bold transition-colors ${
                isActive(link.path)
                  ? 'bg-secondary/10 text-secondary'
                  : 'text-text hover:bg-secondary/5 hover:text-secondary'
              }`}
            >
              {link.name}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
