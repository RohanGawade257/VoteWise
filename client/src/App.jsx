import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Layout
import Layout from './components/Layout';
import { LanguageProvider } from './context/LanguageContext';

// Pages
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import ProcessMapPage from './pages/ProcessMapPage';
import TimelinePage from './pages/TimelinePage';
import FirstTimeVoterPage from './pages/FirstTimeVoterPage';
import PartiesPage from './pages/PartiesPage';
import BasicsPage from './pages/BasicsPage';
import FAQPage from './pages/FAQPage';
import SourcesPage from './pages/SourcesPage';

function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="process" element={<ProcessMapPage />} />
            <Route path="timeline" element={<TimelinePage />} />
            <Route path="first-time-voter" element={<FirstTimeVoterPage />} />
            <Route path="parties" element={<PartiesPage />} />
            <Route path="basics" element={<BasicsPage />} />
            <Route path="faq" element={<FAQPage />} />
            <Route path="sources" element={<SourcesPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </LanguageProvider>
  );
}

export default App;
