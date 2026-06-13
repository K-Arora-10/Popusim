import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function FunnelChart({ personas = [], logs = {} }) {
  // Compute funnel steps dynamically
  const total = personas.length || 1;
  
  let landed = total;
  let explored = 0;
  let engaged = 0;
  let completed = 0;

  personas.forEach(p => {
    const agentLogs = logs[p.id] || [];
    const maxStep = agentLogs.length ? agentLogs[agentLogs.length - 1].step : 0;
    
    if (maxStep >= 1) explored++;
    
    // Engaged means completed at least 3 steps or filled input or clicked significant links
    const hasAttempted = agentLogs.some(l => 
      l.action === 'Type' || 
      (l.action === 'Click' && (
        l.description.toLowerCase().includes('signup') || 
        l.description.toLowerCase().includes('pricing') ||
        l.description.toLowerCase().includes('register')
      ))
    );
    if (maxStep >= 3 || hasAttempted) engaged++;
    
    if (p.status === 'completed') completed++;
  });

  // Ensure explored contains completed, and engaged is scaled logically
  explored = Math.max(explored, engaged);
  engaged = Math.max(engaged, completed);

  const data = [
    { name: '1. Landed', value: landed, rate: '100%', color: '#06b6d4' },
    { name: '2. Explored', value: explored, rate: `${Math.round((explored / total) * 100)}%`, color: '#8b5cf6' },
    { name: '3. Engaged', value: engaged, rate: `${Math.round((engaged / total) * 100)}%`, color: '#f97316' },
    { name: '4. Converted', value: completed, rate: `${Math.round((completed / total) * 100)}%`, color: '#10b981' }
  ];

  return (
    <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-bold text-white text-lg flex items-center gap-2">
          📊 Conversion Funnel
        </h3>
        <span className="text-xs bg-neonCyan/10 text-neonCyan px-2 py-0.5 rounded-full font-semibold border border-neonCyan/20">
          Conversion: {Math.round((completed / total) * 100)}%
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
            <XAxis type="number" stroke="#9ca3af" domain={[0, total]} hide />
            <YAxis
              dataKey="name"
              type="category"
              stroke="#9ca3af"
              tickLine={false}
              axisLine={false}
              width={85}
              style={{ fontSize: '11px', fontWeight: 'bold' }}
            />
            <Tooltip
              contentStyle={{ background: '#111827', borderColor: '#1f2937', color: '#f3f4f6', borderRadius: '8px' }}
              labelStyle={{ color: '#9ca3af', fontWeight: 'bold' }}
            />
            <Bar dataKey="value" barSize={28} radius={[0, 6, 6, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Funnel Metrics Grid */}
      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-darkBorder/60 text-center text-xs">
        {data.map((stage, idx) => (
          <div key={idx} className="space-y-1">
            <span className="text-[10px] text-gray-500 font-semibold uppercase">{stage.name.split(' ')[1]}</span>
            <div className="font-bold text-white text-sm">{stage.value}</div>
            <div className="text-[10px] font-semibold text-gray-400">{stage.rate}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
