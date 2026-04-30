import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const QuickActionCard = ({ title, description, icon: Icon, to, colorClass = 'from-secondary to-primary' }) => {
  return (
    <Link 
      to={to} 
      className="group relative clay-card clay-card-hoverable p-8 flex flex-col h-full overflow-hidden"
    >
      {/* Animated gradient background on hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${colorClass} opacity-0 group-hover:opacity-10 transition-opacity duration-700 z-0`}></div>
      <div className={`absolute -bottom-10 -right-10 w-32 h-32 bg-gradient-to-br ${colorClass} opacity-0 group-hover:opacity-20 blur-[40px] rounded-full transition-all duration-700 z-0`}></div>

      <div className="relative z-10 flex flex-col h-full">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-8 bg-slate-50 border border-border shadow-sm group-hover:shadow-md transition-all duration-500 group-hover:scale-110 origin-left relative overflow-hidden">
          <div className={`absolute inset-0 bg-gradient-to-br ${colorClass} opacity-10 group-hover:opacity-20 transition-opacity`}></div>
          <Icon size={26} className="text-slate-700 group-hover:text-secondary relative z-10 transition-colors duration-300" />
        </div>
        
        <h3 className="text-3xl font-extrabold text-primary mb-4 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-primary group-hover:to-secondary transition-all duration-500 font-sans tracking-tight leading-tight">{title}</h3>
        <p className="text-muted leading-relaxed mb-8 flex-grow font-light text-base group-hover:text-slate-700 transition-colors duration-300">{description}</p>
        
        <div className="flex items-center mt-auto text-secondary font-bold tracking-widest text-xs uppercase transition-colors duration-300">
          <span className="opacity-70 group-hover:opacity-100 transition-opacity duration-300">Explore Module</span>
          <div className="ml-4 w-8 h-8 rounded-full bg-white border border-border flex items-center justify-center group-hover:bg-secondary group-hover:text-white group-hover:border-secondary transition-all duration-500 shadow-sm group-hover:shadow-md">
            <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform duration-300" />
          </div>
        </div>
      </div>
    </Link>
  );
};

export default QuickActionCard;
