import React from 'react';
import { Target, Lightbulb, MapPin, MousePointer, Type, Eye, AlertTriangle } from 'lucide-react';

export default function AgentCard({ persona, logs = [] }) {
  if (!persona) {
    return (
      <div className="bg-darkCard border border-darkBorder rounded-2xl p-8 text-center text-gray-500 h-full flex items-center justify-center">
        <p>Select a persona from the swarm to inspect their autonomous browsing session.</p>
      </div>
    );
  }

  const latestStep = logs.length > 0 ? logs[logs.length - 1] : null;
  
  // Resolve screenshot path dynamically
  const getScreenshotUrl = (filename) => {
    if (!filename) return null;
    const backendHost = window.location.host.includes('5173') ? 'http://localhost:8000' : '';
    return `${backendHost}/screenshots/${filename}`;
  };

  const getActionIcon = (action) => {
    switch (action?.toLowerCase()) {
      case 'click':
        return <MousePointer size={14} className="text-neonCyan" />;
      case 'type':
        return <Type size={14} className="text-neonPurple" />;
      case 'navigate':
        return <MapPin size={14} className="text-neonGreen" />;
      case 'back':
        return <MapPin size={14} className="text-neonOrange rotate-180" />;
      case 'churn':
      case 'abandon':
        return <AlertTriangle size={14} className="text-neonRed" />;
      default:
        return <Eye size={14} className="text-gray-400" />;
    }
  };

  return (
    <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 space-y-6 h-full flex flex-col">
      {/* Header Info */}
      <div className="border-b border-darkBorder/60 pb-4">
        <h2 className="text-2xl font-bold text-white">{persona.name}</h2>
        <p className="text-sm text-neonCyan font-semibold">{persona.archetype}</p>
        
        {/* Goals Checklist */}
        <div className="mt-3 space-y-1.5">
          <p className="text-xs font-bold text-gray-500 flex items-center gap-1.5 uppercase tracking-wider">
            <Target size={12} /> Goals to Complete
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            {persona.goals.map((goal, idx) => (
              <span
                key={idx}
                className="text-xs bg-darkBg border border-darkBorder px-3 py-1 rounded-lg text-gray-300 flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-neonPurple"></span>
                {goal}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Live Browser Screenshot vs Action Reason / Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 overflow-hidden">
        {/* Screenshot View (7 cols) */}
        <div className="lg:col-span-7 flex flex-col space-y-3 h-full">
          <div className="flex justify-between items-center text-xs text-gray-400 font-semibold px-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-neonCyan animate-ping"></span> Live Screenshot
            </span>
            <span className="text-gray-500">
              {latestStep?.url ? latestStep.url.substring(0, 45) + '...' : 'Browser Standby'}
            </span>
          </div>

          <div className="bg-darkBg border border-darkBorder rounded-xl flex-1 relative overflow-hidden flex items-center justify-center min-h-[300px] max-h-[500px]">
            {latestStep && latestStep.screenshot ? (
              <img
                src={getScreenshotUrl(latestStep.screenshot)}
                alt="Agent Browser Step View"
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
            ) : null}
            <div
              className={`absolute inset-0 flex flex-col items-center justify-center text-gray-500 p-4 gap-2 ${
                latestStep && latestStep.screenshot ? 'hidden' : 'flex'
              }`}
            >
              <div className="w-8 h-8 border border-gray-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-xs">Waiting for step screenshot...</p>
            </div>
          </div>
        </div>

        {/* Action Decision & Logs (5 cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-4 h-full overflow-hidden">
          {/* Why current decision chosen */}
          {latestStep && (
            <div className="bg-darkBg border border-neonPurple/20 rounded-xl p-4 space-y-3 shadow-sm">
              <h4 className="text-xs font-bold text-neonPurple flex items-center gap-1.5 uppercase tracking-wider">
                <Lightbulb size={14} /> Cognitive Reasoning
              </h4>
              <p className="text-sm text-gray-300 italic">
                "{latestStep.reason || 'Navigating links matching target tasks.'}"
              </p>
              {latestStep.action && (
                <div className="flex items-center gap-2 text-xs bg-darkCard px-3 py-1.5 rounded-lg border border-darkBorder w-max">
                  {getActionIcon(latestStep.action)}
                  <span className="font-semibold text-gray-400">Action:</span>
                  <span className="font-bold text-white capitalize">{latestStep.action}</span>
                </div>
              )}
            </div>
          )}

          {/* Logs Feed */}
          <div className="flex-1 flex flex-col min-h-[200px] overflow-hidden">
            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
              Navigation Logs
            </h4>
            
            <div className="bg-darkBg/60 border border-darkBorder rounded-xl p-4 flex-1 overflow-y-auto space-y-4">
              {logs.length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-4">No events logged yet.</p>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="flex gap-3 text-xs relative group pb-1">
                    {/* Line Connector */}
                    {index < logs.length - 1 && (
                      <div className="absolute left-2 top-4 bottom-0 w-0.5 bg-darkBorder"></div>
                    )}
                    
                    {/* Event Marker */}
                    <div className="relative z-10 w-4.5 h-4.5 rounded-full bg-darkCard border border-darkBorder flex items-center justify-center shrink-0">
                      {getActionIcon(log.action)}
                    </div>
                    
                    {/* Content */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-300">Step {log.step}</span>
                        <span className="text-[10px] text-gray-500">
                          {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-gray-400 leading-relaxed">
                        {log.description}
                      </p>
                      {log.url && (
                        <p className="text-[10px] text-neonCyan truncate max-w-[200px]">
                          {log.url}
                        </p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
