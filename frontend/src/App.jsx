import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';

export function App() {
  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-slate-950 text-slate-100 font-sans transition-colors duration-200">
          <Navbar />
          <main className="pb-12">
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="*" element={<Navigate to="/chat" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
