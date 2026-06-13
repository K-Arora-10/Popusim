import React from 'react';
import { User, ShieldAlert, CheckCircle2, XCircle, Settings, Play } from 'lucide-react';

export default function AgentSwarm({ personas = [], activePersonaId, onSelectPersona, logs = {} }) {
  const getStatusStyle = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'churned':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      case 'running':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30 animate-pulse';
      case 'failed':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={14} />;
      case 'churned':
        return <XCircle size={14} />;
      case 'running':
        return <Play size={14} className="fill-current animate-pulse" />;
      case 'failed':
        return <ShieldAlert size={14} />;
      default:
        return <Settings size={14} className="animate-spin" />;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          🤖 Persona Swarm
        </h2>
        <span className="text-xs text-gray-500">Click a card to inspect live agent browser</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {personas.map((persona) => {
          const isSelected = activePersonaId === persona.id;
          const agentLogs = logs[persona.id] || [];
          const currentStep = agentLogs.length ? agentLogs[agentLogs.length - 1].step : 0;
          const latestAction = agentLogs.length ? agentLogs[agentLogs.length - 1].description : 'Idle...';

          return (
            <div
              key={persona.id}
              onClick={() => onSelectPersona(persona.id)}
              className={`cursor-pointer rounded-xl border p-5 transition-all duration-200 relative overflow-hidden group ${
                isSelected
                  ? 'bg-darkCard border-neonCyan shadow-neonCyan'
                  : 'bg-darkCard/60 border-darkBorder hover:border-gray-700'
              }`}
            >
              {/* Glow Accent */}
              {isSelected && (
                <div className="absolute top-0 left-0 w-1 h-full bg-neonCyan"></div>
              )}

              <div className="flex justify-between items-start gap-4">
                <div className="space-y-1">
                  <h3 className="font-bold text-white flex items-center gap-1.5 group-hover:text-neonCyan transition-all">
                    <User size={16} className="text-gray-400" /> {persona.name}
                  </h3>
                  <p className="text-xs text-gray-400 font-medium">
                    {persona.archetype}
                  </p>
                </div>

                <span className={`text-xs px-2.5 py-0.5 rounded-full border flex items-center gap-1 capitalize font-semibold ${getStatusStyle(persona.status)}`}>
                  {getStatusIcon(persona.status)} {persona.status}
                </span>
              </div>

              {/* Progress and Latest step description */}
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Progress</span>
                  <span className="font-bold text-white">Step {currentStep} / 12</span>
                </div>
                {/* Visual mini progress bar */}
                <div className="w-full h-1.5 bg-darkBg rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      persona.status === 'churned' ? 'bg-rose-500' :
                      persona.status === 'completed' ? 'bg-emerald-500' : 'bg-neonCyan'
                    }`}
                    style={{ width: `${(currentStep / 12) * 100}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 italic truncate" title={latestAction}>
                  {latestAction}
                </p>
              </div>

              {/* Traits Badges Grid */}
              <div className="mt-4 pt-3 border-t border-darkBorder/60 grid grid-cols-4 gap-1 text-[10px] text-center text-gray-400">
                <div className="bg-darkBg/60 px-1.5 py-1 rounded">
                  <span className="block text-gray-600 font-medium">IMP</span>
                  <span className="font-bold text-white">{Math.round(persona.impatience * 100)}%</span>
                </div>
                <div className="bg-darkBg/60 px-1.5 py-1 rounded">
                  <span className="block text-gray-600 font-medium">TECH</span>
                  <span className="font-bold text-white">{Math.round(persona.tech_savviness * 100)}%</span>
                </div>
                <div className="bg-darkBg/60 px-1.5 py-1 rounded">
                  <span className="block text-gray-600 font-medium">PRICE</span>
                  <span className="font-bold text-white">{Math.round(persona.price_sensitivity * 100)}%</span>
                </div>
                <div className="bg-darkBg/60 px-1.5 py-1 rounded">
                  <span className="block text-gray-600 font-medium">SUPP</span>
                  <span className="font-bold text-white">{Math.round(persona.support_reliance * 100)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
