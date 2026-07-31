import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, MessageSquare, LayoutDashboard, Sun, Moon, Radio } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import wsManager from '../services/websocket';

export const Navbar = () => {
  const { theme, toggleTheme } = useTheme();
  const [wsStatus, setWsStatus] = useState('disconnected');

  useEffect(() => {
    const unsubscribe = wsManager.onStatusChange((status) => setWsStatus(status));
    wsManager.connect();
    return () => unsubscribe();
  }, []);

  return (
    <nav className="clean-card mb-6 sticky top-0 z-50 transition-colors duration-200 rounded-none border-t-0 border-x-0">
      <div className="max-w-7xl mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Brand Logo & Name */}
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-slate-100 dark:bg-white/10 text-slate-100 border border-slate-600/30 shadow-sm">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-wider text-slate-100 uppercase">
                Agent <span className="font-black">WAF</span>
              </span>
              <span className="block text-[10px] text-slate-400 font-mono tracking-widest uppercase">
                Security Platform
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-3">
            <NavLink
              to="/chat"
              className={({ isActive }) =>
                `flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all border ${
                  isActive
                    ? 'bg-slate-100 dark:bg-white/10 text-slate-100 border-slate-600/30'
                    : 'clean-btn text-slate-300 hover:text-white border-transparent'
                }`
              }
            >
              <MessageSquare className="w-4 h-4" />
              <span>Sample Agent</span>
            </NavLink>

            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all border ${
                  isActive
                    ? 'bg-slate-100 dark:bg-white/10 text-slate-100 border-slate-600/30'
                    : 'clean-btn text-slate-300 hover:text-white border-transparent'
                }`
              }
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>WAF Dashboard</span>
            </NavLink>
          </div>

          {/* WS Status Badge & Theme Switcher */}
          <div className="flex items-center space-x-4">
            <div className="clean-badge flex items-center space-x-2 px-3 py-1.5 text-xs">
              <Radio
                className={`w-3.5 h-3.5 ${
                  wsStatus === 'connected' ? 'text-slate-100 animate-pulse' : 'text-slate-500'
                }`}
              />
              <span className="text-slate-300 font-mono capitalize">{wsStatus}</span>
            </div>

            <button
              onClick={toggleTheme}
              className="clean-btn p-2.5 text-slate-300 hover:text-white transition"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-slate-100" /> : <Moon className="w-4 h-4 text-slate-100" />}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
