import React, { useState, useEffect } from 'react';
import { Globe, Users, Play, History, Trash2, Key, AlertCircle } from 'lucide-react';
import { getBootstrapStatus, startBootstrap, saveBootstrap, cancelBootstrap } from '../api';

export default function URLInput({ onSubmit, history = [], onSelectHistory, onDeleteHistory, loading = false }) {
  const [url, setUrl] = useState('');
  const [personas, setPersonas] = useState(3);
  const [error, setError] = useState('');
  
  // Shared Login States
  const [useSharedSession, setUseSharedSession] = useState(false);
  const [hasSavedSession, setHasSavedSession] = useState(false);
  const [bootstrapActive, setBootstrapActive] = useState(false);
  const [bootstrapUrl, setBootstrapUrl] = useState('');
  const [bootstrapLoading, setBootstrapLoading] = useState(false);
  const [bootstrapMessage, setBootstrapMessage] = useState('');
  const [showBootstrapPanel, setShowBootstrapPanel] = useState(false);

  useEffect(() => {
    fetchSessionStatus();
    const interval = setInterval(fetchSessionStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchSessionStatus = async () => {
    try {
      const status = await getBootstrapStatus();
      setHasSavedSession(status.has_saved_session);
      setBootstrapActive(status.active);
    } catch (e) {
      console.error('Failed to fetch session status:', e);
    }
  };

  const handleStartBootstrap = async () => {
    if (!bootstrapUrl) {
      setBootstrapMessage('Please enter a login page URL.');
      return;
    }
    setBootstrapLoading(true);
    setBootstrapMessage('');
    try {
      await startBootstrap(bootstrapUrl);
      setBootstrapActive(true);
      setBootstrapMessage('Browser opened! Please log in manually in the Chromium window, then click "Save Session" below.');
    } catch (e) {
      setBootstrapMessage(`Error: ${e.message}`);
    } finally {
      setBootstrapLoading(false);
    }
  };

  const handleSaveBootstrap = async () => {
    setBootstrapLoading(true);
    setBootstrapMessage('');
    try {
      await saveBootstrap();
      setBootstrapActive(false);
      setHasSavedSession(true);
      setUseSharedSession(true);
      setBootstrapMessage('Session saved successfully! You can now run the simulation.');
    } catch (e) {
      setBootstrapMessage(`Error: ${e.message}`);
    } finally {
      setBootstrapLoading(false);
    }
  };

  const handleCancelBootstrap = async () => {
    setBootstrapLoading(true);
    setBootstrapMessage('');
    try {
      await cancelBootstrap();
      setBootstrapActive(false);
      setBootstrapMessage('Browser closed.');
    } catch (e) {
      setBootstrapMessage(`Error: ${e.message}`);
    } finally {
      setBootstrapLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    
    if (!url) {
      setError('Please enter a website URL.');
      return;
    }
    
    // Simple URL check
    let cleanUrl = url.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'https://' + cleanUrl;
    }
    
    try {
      new URL(cleanUrl);
      onSubmit(cleanUrl, personas, useSharedSession);
    } catch (_) {
      setError('Please enter a valid URL.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero Header */}
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-neonCyan via-neonPurple to-neonOrange bg-clip-text text-transparent">
          PopuSim
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          Simulate populations of autonomous AI users navigating your site. Uncover bugs, churn funnels, NPS, and price sensitivity signals in minutes.
        </p>
      </div>

      {/* Main Submission Form */}
      <form onSubmit={handleSubmit} className="bg-darkCard border border-darkBorder rounded-2xl p-8 shadow-neonCyan transition-all duration-300">
        <div className="space-y-6">
          {/* URL Entry */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <Globe size={16} className="text-neonCyan" /> Target Website URL
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. news.ycombinator.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                className="w-full bg-darkBg border border-darkBorder focus:border-neonCyan focus:ring-1 focus:ring-neonCyan rounded-xl px-5 py-4 pl-12 text-white outline-none transition-all placeholder-gray-500"
              />
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={20} />
            </div>
            {error && <p className="text-neonRed text-sm mt-1">{error}</p>}
          </div>

          {/* Persona Count Slider */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <Users size={16} className="text-neonPurple" /> Persona Swarm Population
              </label>
              <span className="text-sm font-bold bg-neonPurple/20 text-neonPurple px-2.5 py-0.5 rounded-full">
                {personas} Agents
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={personas}
              onChange={(e) => setPersonas(parseInt(e.target.value))}
              disabled={loading}
              className="w-full h-2 bg-darkBg rounded-lg appearance-none cursor-pointer accent-neonPurple"
            />
            <div className="flex justify-between text-xs text-gray-500 px-1">
              <span>1 Persona</span>
              <span>3 Personas</span>
              <span>5 Personas</span>
            </div>
          </div>

          {/* Shared Login Session Section */}
          <div className="border border-darkBorder bg-darkBg/50 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <Key size={16} className="text-neonCyan" /> Shared Login Session (Hackathon Mode)
              </label>
              <button
                type="button"
                onClick={() => setShowBootstrapPanel(!showBootstrapPanel)}
                className="text-xs text-neonCyan hover:underline font-semibold font-sans"
              >
                {showBootstrapPanel ? 'Hide Settings' : 'Configure Session'}
              </button>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="useSharedSession"
                checked={useSharedSession}
                onChange={(e) => setUseSharedSession(e.target.checked)}
                disabled={loading || !hasSavedSession || bootstrapActive}
                className="w-4 h-4 bg-darkBg border border-darkBorder rounded text-neonCyan focus:ring-neonCyan accent-neonCyan cursor-pointer"
              />
              <label htmlFor="useSharedSession" className={`text-sm ${hasSavedSession ? 'text-gray-300 cursor-pointer select-none font-medium' : 'text-gray-500 cursor-not-allowed select-none font-medium'}`}>
                Use saved login session state ({hasSavedSession ? 'shared.json loaded' : 'no saved session found'})
              </label>
            </div>

            {showBootstrapPanel && (
              <div className="mt-4 border-t border-darkBorder pt-4 space-y-4 transition-all duration-300">
                <p className="text-xs text-gray-400 font-medium">
                  Bootstrap a browser session to authenticate agents on targets that require logins (e.g. Gmail, SaaS dashboards).
                </p>

                {bootstrapActive ? (
                  <div className="bg-neonCyan/10 border border-neonCyan/30 rounded-xl p-4 space-y-3">
                    <div className="flex items-center gap-2 text-neonCyan text-sm font-bold">
                      <span className="w-2 h-2 rounded-full bg-neonCyan animate-ping"></span>
                      Manual Login Browser is Open
                    </div>
                    <p className="text-xs text-gray-300">
                      Please look at your taskbar/desktop for the Chromium window. Log in manually, handle 2FA/CAPTCHAs, and once logged in, click "Save Session" below.
                    </p>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={handleSaveBootstrap}
                        disabled={bootstrapLoading}
                        className="bg-neonCyan text-darkBg font-bold text-xs px-4 py-2 rounded-lg hover:opacity-95 transition-all"
                      >
                        {bootstrapLoading ? 'Saving...' : 'Save Session & Close'}
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelBootstrap}
                        disabled={bootstrapLoading}
                        className="bg-transparent border border-gray-600 text-gray-300 text-xs px-4 py-2 rounded-lg hover:bg-darkCard transition-all"
                      >
                        Cancel / Close
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Login page URL (e.g., https://example.com/login)"
                        value={bootstrapUrl}
                        onChange={(e) => setBootstrapUrl(e.target.value)}
                        disabled={bootstrapLoading}
                        className="flex-1 bg-darkBg border border-darkBorder focus:border-neonCyan focus:ring-1 focus:ring-neonCyan rounded-xl px-3 py-2 text-xs text-white outline-none placeholder-gray-600"
                      />
                      <button
                        type="button"
                        onClick={handleStartBootstrap}
                        disabled={bootstrapLoading}
                        className="bg-gradient-to-r from-neonCyan to-neonPurple text-darkBg font-bold text-xs px-4 py-2 rounded-xl hover:opacity-90 transition-all shrink-0"
                      >
                        {bootstrapLoading ? 'Opening...' : 'Launch Browser'}
                      </button>
                    </div>
                  </div>
                )}

                {bootstrapMessage && (
                  <div className={`text-xs p-3 rounded-lg flex items-start gap-2 ${
                    bootstrapMessage.startsWith('Error') 
                      ? 'bg-neonRed/15 border border-neonRed/30 text-neonRed' 
                      : 'bg-darkBg border border-darkBorder text-neonCyan'
                  }`}>
                    <AlertCircle size={14} className="shrink-0 mt-0.5" />
                    <span>{bootstrapMessage}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Trigger */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-neonCyan to-neonPurple hover:opacity-90 active:scale-[0.99] disabled:opacity-50 text-darkBg font-bold text-lg py-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-neonPurple"
          >
            {loading ? (
              <div className="w-6 h-6 border-2 border-darkBg border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <>
                <Play size={20} fill="currentColor" /> Run Simulation Swarm
              </>
            )}
          </button>
        </div>
      </form>

      {/* Recent simulations List */}
      {history.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold flex items-center gap-2 text-gray-300">
            <History size={18} className="text-neonOrange" /> Simulation History
          </h2>
          
          <div className="grid gap-3">
            {history.map((sim) => (
              <div
                key={sim.id}
                className="bg-darkCard border border-darkBorder hover:border-gray-700 rounded-xl p-4 flex items-center justify-between group transition-all"
              >
                <div
                  className="flex-1 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between pr-4 gap-2"
                  onClick={() => onSelectHistory(sim.id)}
                >
                  <div className="space-y-1">
                    <p className="font-semibold text-white group-hover:text-neonCyan transition-all truncate max-w-md">
                      {sim.url}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>ID: {sim.id.substring(4)}</span>
                      <span>•</span>
                      <span>{new Date(sim.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {sim.status === 'completed' ? (
                      <>
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full border border-green-500/30">
                          NPS: {sim.nps}
                        </span>
                        <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full border border-red-500/30">
                          Churn: {sim.churn_rate}%
                        </span>
                      </>
                    ) : (
                      <span className={`text-xs px-2 py-0.5 rounded-full border capitalize ${
                        sim.status === 'failed' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                        sim.status === 'running' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30 animate-pulse' :
                        'bg-blue-500/20 text-blue-400 border-blue-500/30'
                      }`}>
                        {sim.status}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => onDeleteHistory(sim.id)}
                  className="text-gray-500 hover:text-neonRed p-2 rounded-lg hover:bg-darkBg transition-all"
                  title="Delete Simulation Record"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
