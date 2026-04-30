import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';
import AccessibilityWidget from './AccessibilityWidget';
import DisclaimerBanner from './DisclaimerBanner';
import ScrollToTop from './ScrollToTop';

const Layout = () => {
  return (
    <div className="min-h-screen flex flex-col font-sans relative">
      <ScrollToTop />
      <DisclaimerBanner />
      <Navbar />
      <AccessibilityWidget />
      <main className="flex-grow w-full">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
