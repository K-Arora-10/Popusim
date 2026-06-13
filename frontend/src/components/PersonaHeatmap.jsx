import React from 'react';

export default function PersonaHeatmap({ personas = [], logs = {} }) {
  // 1. Identify distinct pages visited across all logs
  const pageSet = new Set(['Home (/)']);
  
  personas.forEach(p => {
    const agentLogs = logs[p.id] || [];
    agentLogs.forEach(log => {
      if (log.url) {
        try {
          const path = new URL(log.url).pathname;
          // Group simple paths
          if (path === '/') return; // already handled
          
          let displayPath = path;
          if (path.includes('/pricing')) displayPath = '/pricing';
          if (path.includes('/signup') || path.includes('/register')) displayPath = '/signup';
          if (path.includes('/doc') || path.includes('/help') || path.includes('/faq')) displayPath = '/docs';
          if (path.includes('/checkout') || path.includes('/pay')) displayPath = '/checkout';
          
          pageSet.add(displayPath);
        } catch (_) {
          // ignore invalid URLs
        }
      }
    });
  });

  const pages = Array.from(pageSet).slice(0, 5); // limit columns for layout sizing
  
  // 2. Count actions per persona per page
  const gridData = personas.map(p => {
    const pageCounts = {};
    pages.forEach(pg => { pageCounts[pg] = 0; });
    
    const agentLogs = logs[p.id] || [];
    agentLogs.forEach(log => {
      let activePage = 'Home (/)';
      if (log.url) {
        try {
          const path = new URL(log.url).pathname;
          if (path !== '/') {
            let displayPath = path;
            if (path.includes('/pricing')) displayPath = '/pricing';
            if (path.includes('/signup') || path.includes('/register')) displayPath = '/signup';
            if (path.includes('/doc') || path.includes('/help') || path.includes('/faq')) displayPath = '/docs';
            if (path.includes('/checkout') || path.includes('/pay')) displayPath = '/checkout';
            
            if (pages.includes(displayPath)) {
              activePage = displayPath;
            }
          }
        } catch (_) {}
      }
      
      if (log.action === 'Click' || log.action === 'Type') {
        pageCounts[activePage] = (pageCounts[activePage] || 0) + 1;
      }
    });

    return {
      name: p.name,
      archetype: p.archetype,
      counts: pageCounts
    };
  });

  // Cell shade color evaluator
  const getCellBg = (count) => {
    if (count === 0) return 'bg-darkBg text-gray-700';
    if (count === 1) return 'bg-neonPurple/20 text-neonPurple border border-neonPurple/20';
    if (count <= 3) return 'bg-neonPurple/40 text-white border border-neonPurple/40';
    return 'bg-neonPurple text-darkBg font-bold border border-neonPurple shadow-neonPurple';
  };

  return (
    <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 space-y-4">
      <div className="flex justify-between items-center border-b border-darkBorder/60 pb-3">
        <h3 className="font-bold text-white text-md flex items-center gap-2">
          🗺️ Persona Heatmap
        </h3>
        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
          Interaction Counts
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-darkBorder/40">
              <th className="py-2.5 px-3 text-gray-500 font-semibold uppercase tracking-wider">Persona</th>
              {pages.map((pg, idx) => (
                <th key={idx} className="py-2.5 px-3 text-gray-500 font-semibold uppercase tracking-wider text-center">
                  {pg}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {gridData.map((row, rIdx) => (
              <tr key={rIdx} className="border-b border-darkBorder/20 hover:bg-darkBg/20 transition-all">
                <td className="py-3 px-3">
                  <div className="font-bold text-white text-xs">{row.name}</div>
                  <div className="text-[10px] text-gray-500">{row.archetype}</div>
                </td>
                {pages.map((pg, cIdx) => {
                  const count = row.counts[pg] || 0;
                  return (
                    <td key={cIdx} className="p-2 text-center">
                      <div className={`w-10 h-10 mx-auto rounded-lg flex items-center justify-center transition-all ${getCellBg(count)}`}>
                        {count}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Heatmap Legend */}
      <div className="flex justify-end gap-4 text-[9px] text-gray-500 font-semibold pt-2 border-t border-darkBorder/40 uppercase">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 bg-darkBg border border-darkBorder rounded"></span>
          <span>0 clicks</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 bg-neonPurple/20 border border-neonPurple/20 rounded"></span>
          <span>1 click</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 bg-neonPurple/40 border border-neonPurple/40 rounded"></span>
          <span>2-3 clicks</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 bg-neonPurple rounded shadow-neonPurple"></span>
          <span>4+ clicks</span>
        </div>
      </div>
    </div>
  );
}
