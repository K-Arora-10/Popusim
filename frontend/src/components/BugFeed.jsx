import React from 'react';
import { AlertCircle, ShieldAlert, Sparkles, MapPin, Code, Image as ImageIcon } from 'lucide-react';

export default function BugFeed({ bugs = [] }) {
  const getSeverityStyle = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'major':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default:
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <ShieldAlert size={14} className="text-red-400" />;
      case 'major':
        return <AlertCircle size={14} className="text-orange-400" />;
      default:
        return <Sparkles size={14} className="text-cyan-400" />;
    }
  };

  const getScreenshotUrl = (filename) => {
    if (!filename) return null;
    const backendHost = window.location.host.includes('5173') ? 'http://localhost:8000' : '';
    return `${backendHost}/screenshots/${filename}`;
  };

  return (
    <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 space-y-4 h-full flex flex-col">
      <div className="flex justify-between items-center border-b border-darkBorder pb-3">
        <h3 className="font-bold text-white text-lg flex items-center gap-2">
          🐛 Bug Feed
        </h3>
        <span className="text-xs bg-red-500/10 text-red-400 px-2 py-0.5 rounded-full font-semibold border border-red-500/20">
          {bugs.length} Issues Found
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[400px]">
        {bugs.length === 0 ? (
          <div className="text-center py-8 text-gray-500 flex flex-col items-center justify-center gap-2">
            <Sparkles size={28} className="text-emerald-500" />
            <p className="text-sm font-semibold text-gray-300">Clean Session Log</p>
            <p className="text-xs text-gray-500">No console errors or click issues detected.</p>
          </div>
        ) : (
          bugs.map((bug, idx) => (
            <div
              key={idx}
              className="bg-darkBg/60 border border-darkBorder hover:border-gray-700 rounded-xl p-4 space-y-3 transition-all"
            >
              <div className="flex justify-between items-center gap-3">
                <span className={`text-[10px] px-2.5 py-0.5 rounded-full border flex items-center gap-1 capitalize font-bold ${getSeverityStyle(bug.severity)}`}>
                  {getSeverityIcon(bug.severity)} {bug.severity}
                </span>
                <span className="text-[10px] text-gray-500 font-bold">BUG #{idx + 1}</span>
              </div>

              <p className="text-xs text-gray-200 font-semibold leading-relaxed">
                {bug.description}
              </p>

              <div className="space-y-1.5 text-[10px] text-gray-400">
                {bug.url && (
                  <div className="flex items-center gap-1.5 truncate">
                    <MapPin size={11} className="text-neonCyan shrink-0" />
                    <span className="font-bold text-gray-500">URL:</span>
                    <span className="truncate text-gray-300">{bug.url}</span>
                  </div>
                )}
                
                {bug.selector && (
                  <div className="flex items-center gap-1.5">
                    <Code size={11} className="text-neonPurple shrink-0" />
                    <span className="font-bold text-gray-500">Selector:</span>
                    <code className="bg-darkCard px-1.5 py-0.5 rounded border border-darkBorder font-mono text-neonPurple text-[9px]">
                      {bug.selector}
                    </code>
                  </div>
                )}

                {bug.screenshot && (
                  <div className="pt-2">
                    <a
                      href={getScreenshotUrl(bug.screenshot)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-neonCyan hover:underline font-bold text-[9px] uppercase tracking-wider"
                    >
                      <ImageIcon size={10} /> View Bug Screenshot
                    </a>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
