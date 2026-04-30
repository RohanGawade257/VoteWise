import React from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Home, MessageSquare, Calendar, ShieldCheck } from 'lucide-react';

const NotFoundPage = () => {
  return (
    <div className="min-h-[calc(100svh-7rem)] flex items-center justify-center px-4 py-16 relative overflow-hidden">

      {/* Ambient background glows — matches HomePage style */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute -top-[20%] -right-[10%] w-[60%] h-[60%] rounded-full bg-secondary/8 blur-[120px]" />
        <div className="absolute -bottom-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-secondary/5 blur-[100px]" />
      </div>

      <div className="relative z-10 max-w-lg w-full text-center">

        {/* Glass card */}
        <div className="bg-white/80 backdrop-blur-2xl border border-border rounded-[2.5rem] p-10 sm:p-14 shadow-xl">

          {/* Icon cluster */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div className="w-24 h-24 rounded-[2rem] bg-blue-50 border border-blue-100 flex items-center justify-center shadow-inner">
                <MapPin
                  size={44}
                  className="text-secondary"
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              </div>
              {/* Small shield badge */}
              <div className="absolute -bottom-2 -right-2 w-9 h-9 rounded-full bg-white border border-border flex items-center justify-center shadow-sm">
                <ShieldCheck size={17} className="text-success" aria-hidden="true" />
              </div>
            </div>
          </div>

          {/* Error code */}
          <p className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-secondary to-[#4F46E5] mb-4 leading-none select-none">
            404
          </p>

          {/* Title */}
          <h1 className="text-2xl sm:text-3xl font-extrabold text-primary mb-4 tracking-tight leading-tight">
            Page Not Found
          </h1>

          {/* Helpful subtitle */}
          <p className="text-muted font-light text-base sm:text-lg leading-relaxed mb-10 max-w-sm mx-auto">
            This page does not exist, but VoteWise can still help you understand elections.
          </p>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 bg-secondary hover:bg-[#2563EB] text-white font-bold text-sm py-3 px-6 rounded-2xl transition-all shadow-[0_4px_20px_rgba(59,130,246,0.25)] hover:shadow-[0_4px_20px_rgba(59,130,246,0.4)] hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:ring-offset-2"
              aria-label="Go to VoteWise home page"
            >
              <Home size={16} aria-hidden="true" />
              Go Home
            </Link>

            <Link
              to="/chat"
              className="inline-flex items-center justify-center gap-2 bg-white hover:bg-slate-50 border border-border text-primary font-bold text-sm py-3 px-6 rounded-2xl transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:ring-offset-2"
              aria-label="Open VoteWise AI Assistant"
            >
              <MessageSquare size={16} aria-hidden="true" />
              Ask Assistant
            </Link>

            <Link
              to="/timeline"
              className="inline-flex items-center justify-center gap-2 bg-white hover:bg-slate-50 border border-border text-primary font-bold text-sm py-3 px-6 rounded-2xl transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary focus-visible:ring-offset-2"
              aria-label="View Indian Election Timeline"
            >
              <Calendar size={16} aria-hidden="true" />
              View Timeline
            </Link>
          </div>

          {/* Reassurance footer */}
          <p className="mt-10 text-xs text-muted/70">
            VoteWise is a neutral civic education platform.{' '}
            <a
              href="https://eci.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-secondary transition-colors focus-visible:ring-1 focus-visible:ring-secondary rounded"
            >
              eci.gov.in
            </a>{' '}
            is the official source for election information.
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
