import React from 'react';
import { BookOpen, Calendar, Map, Users, ShieldQuestion, MessageSquare, ShieldCheck, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import QuickActionCard from '../components/QuickActionCard';
import SectionHeader from '../components/SectionHeader';
import AssetImage from '../components/AssetImage';

import logoImg from '../assets/votewise-logo.svg';

const HomePage = () => {
  return (
    <div className="w-full">
      {/* Modern Dark Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-24 border-b border-border">
        {/* Animated Background Glows */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
          <div className="absolute -top-[20%] -right-[10%] w-[70%] h-[70%] rounded-full bg-secondary/10 blur-[120px] animate-pulse"></div>
          <div className="absolute -bottom-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-secondary/5 blur-[100px]"></div>
          <div className="absolute top-[30%] left-[20%] w-[30%] h-[30%] rounded-full bg-secondary/5 blur-[80px]"></div>
        </div>
        
        {/* Background Image overlay */}
        <div className="absolute inset-0 z-0 opacity-[0.06] mix-blend-multiply">
          <img src="/images/bg-1.jpg" alt="" className="w-full h-full object-cover grayscale" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col md:flex-row items-center justify-between mt-8">
          <div className="w-full md:w-[55%] mb-12 md:mb-0">
            <div className="inline-flex items-center space-x-2 bg-white/80 backdrop-blur-md rounded-full px-5 py-2 mb-8 border border-border shadow-[0_0_15px_rgba(59,130,246,0.1)] animate-in fade-in slide-in-from-bottom-4 duration-700">
              <ShieldCheck size={18} className="text-secondary" />
              <span className="text-sm font-semibold tracking-wide text-primary">100% Neutral & Non-Partisan</span>
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-tight animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
              Empowering Voters Through <span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary to-[#4F46E5]">Knowledge</span>
            </h1>
            <p className="text-lg md:text-xl text-muted max-w-xl mb-10 leading-relaxed font-light animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
              VoteWise is your beautifully simple, comprehensive guide to understanding the Indian electoral process. Be informed. Be prepared. Vote wise.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-300">
              <a href="#explore" className="inline-flex items-center justify-center bg-secondary hover:bg-[#2563EB] text-white font-bold text-lg py-4 px-8 rounded-2xl transition-all shadow-[0_8px_30px_rgb(59,130,246,0.3)] hover:shadow-[0_8px_30px_rgb(59,130,246,0.5)] hover:-translate-y-1 border border-secondary/50">
                Explore Topics <ArrowRight className="ml-2" size={20} />
              </a>
              <Link to="/first-time-voter" className="inline-flex items-center justify-center bg-white/80 hover:bg-white backdrop-blur-md border border-border text-primary font-bold text-lg py-4 px-8 rounded-2xl transition-all shadow-sm hover:shadow-md hover:-translate-y-1">
                First-Time Voter?
              </Link>
            </div>
          </div>
          <div className="w-full md:w-[40%] flex justify-center relative animate-in fade-in zoom-in-95 duration-1000 delay-300">
            {/* Glowing effect behind logo */}
            <div className="absolute inset-0 bg-secondary/20 rounded-full blur-[80px] -z-10 animate-pulse"></div>
            <div className="bg-white/80 backdrop-blur-2xl border border-border rounded-[3rem] p-10 shadow-xl">
              <AssetImage 
                src={logoImg} 
                alt="VoteWise Logo" 
                className="w-56 h-56 md:w-72 md:h-72 object-contain drop-shadow-[0_20px_50px_rgba(59,130,246,0.2)] transform transition-transform hover:scale-105 duration-500" 
              />
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Areas */}
      <section id="explore" className="py-20 relative z-20 overflow-hidden">
        <div className="absolute inset-0 z-0 opacity-[0.04] mix-blend-multiply pointer-events-none">
          <img src="/images/bg-2.jpg" alt="" className="w-full h-full object-cover grayscale" />
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
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
      <section className="py-32 relative overflow-hidden bg-slate-50">
        {/* Background Image */}
        <div className="absolute inset-0 z-0 opacity-[0.05] mix-blend-multiply pointer-events-none">
          <img src="/images/bg-3.jpg" alt="" className="w-full h-full object-cover grayscale" />
        </div>
        
        {/* Background decorative blob */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-secondary/10 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/3 z-0"></div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="order-2 lg:order-1">
              <span className="text-secondary font-bold tracking-wider uppercase text-sm mb-3 block">AI-Powered</span>
              <h2 className="text-4xl md:text-5xl font-extrabold text-primary mb-6 leading-tight">Have specific <span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary to-[#4F46E5]">questions?</span></h2>
              <p className="text-muted mb-8 text-lg md:text-xl leading-relaxed font-light">
                Our AI-powered civic assistant is trained on official election guidelines to help answer your queries neutrally and accurately. We rely strictly on verified data sources like the Election Commission of India.
              </p>
              
              <div className="space-y-4 mb-10">
                <div className="flex items-center p-5 bg-white/80 backdrop-blur-md rounded-2xl border border-border shadow-sm">
                  <div className="bg-success/10 p-2.5 rounded-xl mr-5"><ShieldCheck size={24} className="text-success" /></div>
                  <span className="font-semibold text-primary">Neutral & Unbiased Responses</span>
                </div>
                <div className="flex items-center p-5 bg-white/80 backdrop-blur-md rounded-2xl border border-border shadow-sm">
                  <div className="bg-secondary/10 p-2.5 rounded-xl mr-5"><BookOpen size={24} className="text-secondary" /></div>
                  <span className="font-semibold text-primary">Sourced from Official Documents</span>
                </div>
              </div>
              
              <Link to="/chat" className="inline-flex items-center justify-center bg-primary text-white hover:bg-primary/90 font-bold text-lg py-4 px-8 rounded-2xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-1">
                Ask the Assistant <ArrowRight className="ml-2" size={20} />
              </Link>
            </div>
            
            <div className="order-1 lg:order-2 flex justify-center lg:justify-end relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-secondary/10 to-[#4F46E5]/10 rounded-[3rem] rotate-3 scale-105 blur-2xl z-0"></div>
              <div className="bg-white/90 backdrop-blur-xl border border-border rounded-[2.5rem] p-8 shadow-xl relative z-10 w-full max-w-md">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 bg-secondary/10 rounded-full flex items-center justify-center">
                    <MessageSquare className="text-secondary" size={24} />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-primary">VoteWise Assistant</h3>
                    <p className="text-xs text-muted flex items-center"><span className="w-2 h-2 rounded-full bg-success mr-2"></span>Online & Ready</p>
                  </div>
                </div>
                <div className="space-y-4 mb-6">
                  <div className="bg-background rounded-2xl rounded-tl-none p-4 text-sm text-text border border-border shadow-sm">
                    How long do I have to register to vote before an election?
                  </div>
                  <div className="bg-secondary/10 rounded-2xl rounded-tr-none p-4 text-sm text-primary border border-secondary/20 shadow-sm">
                    You can register to vote up to the last date of filing nominations by candidates in your constituency. However, it's best to register well in advance...
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
