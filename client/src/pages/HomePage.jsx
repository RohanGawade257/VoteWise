import React from 'react';
import { BookOpen, Calendar, Map, Users, ShieldQuestion, MessageSquare, ShieldCheck, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import QuickActionCard from '../components/QuickActionCard';
import SectionHeader from '../components/SectionHeader';
import AssetImage from '../components/AssetImage';

import logoImg from '../assets/votewise-logo.png';
import civicBadgeImg from '../assets/civic-session-badge.png';

const HomePage = () => {
  return (
    <div className="w-full">
      {/* Modern Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary via-primary to-[#0f213a] text-surface pt-24 pb-32">
        {/* Animated Background Elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
          <div className="absolute -top-[20%] -right-[10%] w-[70%] h-[70%] rounded-full bg-secondary/20 blur-[120px] animate-pulse"></div>
          <div className="absolute -bottom-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-secondary/10 blur-[100px]"></div>
          <div className="absolute top-[30%] left-[20%] w-[30%] h-[30%] rounded-full bg-primary/40 blur-[80px]"></div>
        </div>
        
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTAgMjBoMjBWMEgweiIgZmlsbD0ibm9uZSIvPjxwYXRoIGQPSJNMCAxOS41aDIwdjFoLTIwem0xOS41IDB2MjBIMTkuNXoiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wMykiLz48L3N2Zz4=')] z-0 opacity-50"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col md:flex-row items-center justify-between mt-8">
          <div className="w-full md:w-[55%] mb-12 md:mb-0">
            <div className="inline-flex items-center space-x-2 bg-surface/10 backdrop-blur-md rounded-full px-5 py-2 mb-8 border border-surface/20 shadow-[0_0_15px_rgba(37,99,235,0.2)] animate-in fade-in slide-in-from-bottom-4 duration-700">
              <ShieldCheck size={18} className="text-[#60a5fa]" />
              <span className="text-sm font-semibold tracking-wide text-surface/90">100% Neutral & Non-Partisan</span>
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-tight animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
              Empowering Voters Through <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#60a5fa] to-secondary">Knowledge</span>
            </h1>
            <p className="text-lg md:text-xl text-surface/80 max-w-xl mb-10 leading-relaxed font-light animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
              VoteWise is your beautifully simple, comprehensive guide to understanding the Indian electoral process. Be informed. Be prepared. Vote wise.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-300">
              <a href="#explore" className="inline-flex items-center justify-center bg-gradient-to-r from-secondary to-[#3b82f6] hover:from-[#3b82f6] hover:to-secondary text-surface font-bold text-lg py-4 px-8 rounded-xl transition-all shadow-[0_8px_30px_rgb(37,99,235,0.3)] hover:shadow-[0_8px_30px_rgb(37,99,235,0.5)] hover:-translate-y-1">
                Explore Topics <ArrowRight className="ml-2" size={20} />
              </a>
              <Link to="/first-time-voter" className="inline-flex items-center justify-center bg-surface/10 hover:bg-surface/20 backdrop-blur-md border border-surface/30 text-surface font-bold text-lg py-4 px-8 rounded-xl transition-all hover:-translate-y-1 shadow-[0_4px_14px_rgba(0,0,0,0.1)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.15)]">
                First-Time Voter?
              </Link>
            </div>
          </div>
          <div className="w-full md:w-[40%] flex justify-center relative animate-in fade-in zoom-in-95 duration-1000 delay-300">
            {/* Glowing effect behind logo */}
            <div className="absolute inset-0 bg-secondary/30 rounded-full blur-[80px] -z-10 animate-pulse"></div>
            <div className="bg-surface/5 backdrop-blur-sm border border-surface/10 rounded-3xl p-8 shadow-2xl">
              <AssetImage 
                src={logoImg} 
                alt="VoteWise Logo" 
                className="w-56 h-56 md:w-72 md:h-72 object-contain drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)] transform transition-transform hover:scale-105 duration-500" 
              />
            </div>
          </div>
        </div>
        
        {/* Curved bottom separator */}
        <div className="absolute bottom-0 left-0 w-full overflow-hidden leading-none z-10">
          <svg className="relative block w-full h-[60px]" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none">
            <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V120H0V95.8C59.71,118.08,130.83,112.56,189.92,98.2,238.16,86.37,281.36,65.31,321.39,56.44Z" className="fill-background"></path>
          </svg>
        </div>
      </section>

      {/* Main Content Areas */}
      <section id="explore" className="py-20 bg-background relative z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-secondary font-bold tracking-wider uppercase text-sm mb-2 block">Your Civic Journey</span>
            <SectionHeader 
              title="Understand Your Democracy" 
              subtitle="Explore our comprehensive guides on how elections work in India."
              centered={true}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <QuickActionCard 
              to="/first-time-voter"
              title="I'm a First-Time Voter"
              description="Everything you need to know about registering, finding your polling booth, and casting your vote."
              icon={BookOpen}
              colorClass="from-[#3b82f6] to-[#2563eb]"
            />
            <QuickActionCard 
              to="/process"
              title="How Elections Work"
              description="A step-by-step visual guide of the entire electoral process from notification to results."
              icon={Map}
              colorClass="from-[#10b981] to-[#059669]"
            />
            <QuickActionCard 
              to="/timeline"
              title="Election Timeline"
              description="Keep track of key dates, deadlines for registration, and voting phases."
              icon={Calendar}
              colorClass="from-[#f59e0b] to-[#d97706]"
            />
            <QuickActionCard 
              to="/basics"
              title="Politics Basics"
              description="Learn about the Constitution, Parliament, and different tiers of government."
              icon={ShieldQuestion}
              colorClass="from-[#8b5cf6] to-[#7c3aed]"
            />
            <QuickActionCard 
              to="/parties"
              title="National Parties"
              description="Neutral information about recognized national political parties in India."
              icon={Users}
              colorClass="from-[#ef4444] to-[#dc2626]"
            />
            <QuickActionCard 
              to="/chat"
              title="Ask the Assistant"
              description="Get factual answers to your queries about voting rights and election rules."
              icon={MessageSquare}
              colorClass="from-[#06b6d4] to-[#0891b2]"
            />
          </div>
        </div>
      </section>

      {/* Feature Preview Cards */}
      <section className="py-24 bg-surface border-t border-border relative overflow-hidden">
        {/* Background decorative blob */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/3"></div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="order-2 lg:order-1">
              <span className="text-secondary font-bold tracking-wider uppercase text-sm mb-3 block">AI-Powered</span>
              <h2 className="text-4xl md:text-5xl font-extrabold text-primary mb-6 leading-tight">Have specific <span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary to-[#60a5fa]">questions?</span></h2>
              <p className="text-muted mb-8 text-lg md:text-xl leading-relaxed">
                Our AI-powered civic assistant is trained on official election guidelines to help answer your queries neutrally and accurately. We rely strictly on verified data sources like the Election Commission of India.
              </p>
              
              <div className="space-y-4 mb-10">
                <div className="flex items-center p-4 bg-background rounded-xl border border-border shadow-sm">
                  <div className="bg-success/10 p-2 rounded-lg mr-4"><ShieldCheck size={24} className="text-success" /></div>
                  <span className="font-semibold text-text">Neutral & Unbiased Responses</span>
                </div>
                <div className="flex items-center p-4 bg-background rounded-xl border border-border shadow-sm">
                  <div className="bg-primary/10 p-2 rounded-lg mr-4"><BookOpen size={24} className="text-primary" /></div>
                  <span className="font-semibold text-text">Sourced from Official Documents</span>
                </div>
              </div>
              
              <Link to="/chat" className="inline-flex items-center justify-center bg-primary hover:bg-[#152e4d] text-surface font-bold text-lg py-4 px-8 rounded-xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-1">
                Ask the Assistant <ArrowRight className="ml-2" size={20} />
              </Link>
            </div>
            
            <div className="order-1 lg:order-2 flex justify-center lg:justify-end relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-secondary/20 to-primary/20 rounded-[3rem] rotate-3 scale-105 blur-sm z-0"></div>
              <div className="bg-background rounded-[3rem] p-12 border border-border shadow-2xl relative z-10 w-full max-w-md flex justify-center items-center backdrop-blur-xl">
                <AssetImage 
                  src={civicBadgeImg} 
                  alt="Civic Session Badge" 
                  className="w-full h-auto object-contain drop-shadow-xl hover:scale-105 transition-transform duration-500 ease-out" 
                />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
