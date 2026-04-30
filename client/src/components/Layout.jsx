import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';
import LanguageWidget from './LanguageWidget';
import DisclaimerBanner from './DisclaimerBanner';
import ScrollToTop from './ScrollToTop';

const Layout = () => {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className="min-h-screen flex flex-col font-sans relative">
      {!isHome && (
        <div className="fixed inset-0 z-0 opacity-[0.08] mix-blend-multiply pointer-events-none">
          <img src="/images/bg-3.jpg" alt="" className="w-full h-full object-cover grayscale" />
        </div>
      )}
      <ScrollToTop />
      <DisclaimerBanner />
      <Navbar />
      <LanguageWidget />
      <main className="flex-grow w-full relative z-10">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
