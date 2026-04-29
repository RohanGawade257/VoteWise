import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';
import AccessibilityBar from './AccessibilityBar';
import DisclaimerBanner from './DisclaimerBanner';

const Layout = () => {
  return (
    <div className="min-h-screen flex flex-col font-sans">
      <AccessibilityBar />
      <DisclaimerBanner />
      <Navbar />
      <main className="flex-grow w-full">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
