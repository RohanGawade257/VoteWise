import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const QuickActionCard = ({ title, description, icon: Icon, to, colorClass = 'from-secondary to-primary' }) => {
  return (
    <Link 
      to={to} 
      className="group relative bg-surface border border-border rounded-2xl p-8 hover:border-transparent transition-all duration-500 flex flex-col h-full overflow-hidden shadow-sm hover:shadow-2xl hover:-translate-y-2"
    >
      {/* Animated gradient border on hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${colorClass} opacity-0 group-hover:opacity-10 transition-opacity duration-500 z-0`}></div>
      <div className={`absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r ${colorClass} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left`}></div>

      <div className="relative z-10">
        <div className={`inline-flex items-center justify-center p-4 rounded-xl mb-6 bg-background border border-border shadow-sm group-hover:shadow-md transition-all duration-300 group-hover:scale-110 origin-left relative overflow-hidden`}>
          <div className={`absolute inset-0 bg-gradient-to-br ${colorClass} opacity-10`}></div>
          <Icon size={28} className="text-primary group-hover:text-secondary relative z-10 transition-colors" />
        </div>
        
        <h3 className="text-2xl font-bold text-primary mb-3 group-hover:text-secondary transition-colors duration-300">{title}</h3>
        <p className="text-muted leading-relaxed mb-8 flex-grow group-hover:text-text transition-colors duration-300">{description}</p>
        
        <div className="flex items-center font-bold mt-auto group-hover:text-secondary text-primary transition-colors duration-300">
          <span className="uppercase tracking-wider text-sm">Explore module</span>
          <div className="ml-3 w-8 h-8 rounded-full bg-background border border-border flex items-center justify-center group-hover:bg-secondary group-hover:text-surface group-hover:border-secondary transition-all duration-300">
            <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform duration-300" />
          </div>
        </div>
      </div>
    </Link>
  );
};

export default QuickActionCard;
