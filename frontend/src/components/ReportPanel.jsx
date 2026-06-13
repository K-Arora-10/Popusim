import React, { useState } from 'react';
import { FileText, DollarSign, ListChecks, Award } from 'lucide-react';

export default function ReportPanel({ report }) {
  const [activeTab, setActiveTab] = useState('summary');

  if (!report) {
    return (
      <div className="bg-darkCard border border-darkBorder rounded-2xl p-8 text-center text-gray-500">
        <p>No report generated yet. Run the simulation to view synthesized AI reports.</p>
      </div>
    );
  }

  // Simple rule-based Markdown parser to avoid npm module loading errors
  const parseMarkdown = (text) => {
    if (!text) return null;
    return text.split('\n').map((line, idx) => {
      const trimmed = line.trim();
      
      // H1 Header
      if (trimmed.startsWith('# ')) {
        return <h1 key={idx} className="text-2xl font-extrabold text-white mt-6 mb-4">{trimmed.substring(2)}</h1>;
      }
      // H2 Header
      if (trimmed.startsWith('## ')) {
        return <h2 key={idx} className="text-lg font-bold text-white mt-5 mb-3 border-b border-darkBorder pb-1.5 flex items-center gap-1">{trimmed.substring(3)}</h2>;
      }
      // H3 Header
      if (trimmed.startsWith('### ')) {
        return <h3 key={idx} className="text-sm font-bold text-white mt-4 mb-2">{trimmed.substring(4)}</h3>;
      }
      // Bullet list items
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        // Handle bold items inside bullet points e.g. **Title:** text
        const content = trimmed.substring(2);
        return (
          <li key={idx} className="ml-4 list-disc text-gray-300 text-xs my-1 leading-relaxed">
            {renderBoldText(content)}
          </li>
        );
      }
      // Divider
      if (trimmed === '---') {
        return <hr key={idx} className="border-darkBorder my-5" />;
      }
      // Empty spaces
      if (trimmed === '') {
        return <div key={idx} className="h-1.5" />;
      }
      // Standard Paragraph
      return (
        <p key={idx} className="text-gray-300 leading-relaxed text-xs my-2">
          {renderBoldText(trimmed)}
        </p>
      );
    });
  };

  const renderBoldText = (text) => {
    const parts = text.split('**');
    return parts.map((part, index) => {
      // Odd indices represent text wrapped in **
      if (index % 2 === 1) {
        return <strong key={index} className="text-white font-semibold">{part}</strong>;
      }
      // Handle inline code formatting e.g. `code`
      const codeParts = part.split('`');
      return codeParts.map((subPart, subIdx) => {
        if (subIdx % 2 === 1) {
          return <code key={subIdx} className="bg-darkBg px-1.5 py-0.5 rounded text-neonCyan font-mono text-[10px]">{subPart}</code>;
        }
        return subPart;
      });
    });
  };

  return (
    <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 space-y-6 flex flex-col">
      {/* Tabs list */}
      <div className="flex border-b border-darkBorder/60 gap-4 text-xs font-semibold no-print">
        <button
          onClick={() => setActiveTab('summary')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'summary'
              ? 'border-neonCyan text-neonCyan'
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          <FileText size={14} /> Executive Summary
        </button>

        <button
          onClick={() => setActiveTab('wtp')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'wtp'
              ? 'border-neonPurple text-neonPurple'
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          <DollarSign size={14} /> Willingness to Pay
        </button>

        <button
          onClick={() => setActiveTab('recommendations')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'recommendations'
              ? 'border-neonOrange text-neonOrange'
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          <ListChecks size={14} /> Key Recommendations
        </button>
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-y-auto min-h-[350px] max-h-[600px] pr-2 print:overflow-visible print:max-h-none">
        {/* Executive Summary */}
        <div className={`${activeTab === 'summary' ? 'block' : 'hidden print:block'} space-y-4 print:mb-8`}>
          <div className="flex items-center gap-2 text-neonCyan">
            <Award size={18} />
            <h3 className="font-bold text-white text-md">Executive UX Report Summary</h3>
          </div>
          <div className="bg-darkBg/30 p-5 rounded-xl border border-darkBorder">
            {parseMarkdown(report.summary)}
          </div>
        </div>

        {/* Willingness to Pay */}
        <div className={`${activeTab === 'wtp' ? 'block' : 'hidden print:block'} space-y-5 print:mb-8 print:break-inside-avoid`}>
          <div className="flex items-center gap-2 text-neonPurple">
            <DollarSign size={18} />
            <h3 className="font-bold text-white text-md">Synthetic Pricing & Value Sensitivity</h3>
          </div>
          
          <div className="bg-darkBg/30 p-6 rounded-xl border border-darkBorder space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold text-gray-400 uppercase">Willingness-to-pay rating:</span>
              <span className="bg-neonPurple/20 text-neonPurple border border-neonPurple/30 font-extrabold text-sm px-3.5 py-1 rounded-full shadow-sm">
                {report.wtp.split(' - ')[0]}
              </span>
            </div>
            
            <p className="text-gray-300 text-xs leading-relaxed">
              {report.wtp.split(' - ').slice(1).join(' - ') || 
               "Price sensitive user personas evaluated your landing and pricing tiers. If conversion metrics are high, user signals report solid value clarity."}
            </p>
            
            <div className="mt-4 pt-4 border-t border-darkBorder/60 space-y-2 text-xs text-gray-400">
              <h4 className="font-bold text-white mb-2 uppercase text-[10px]">WTP Evaluation Metrics:</h4>
              <p>• <strong>Low WTP:</strong> Impatient/skeptical users churned prior to pricing details, or expressed confusion about product ROI.</p>
              <p>• <strong>Medium WTP:</strong> Users explored pricing, compared tiers, but faced UX bottlenecks in forms, reducing complete conversions.</p>
              <p>• <strong>High WTP:</strong> Power users navigated seamlessly and completed registration, showing clear perceived utility.</p>
            </div>
          </div>
        </div>

        {/* Key Recommendations */}
        <div className={`${activeTab === 'recommendations' ? 'block' : 'hidden print:block'} space-y-4 print:break-inside-avoid`}>
          <div className="flex items-center gap-2 text-neonOrange">
            <ListChecks size={18} />
            <h3 className="font-bold text-white text-md">Actionable Optimization Items</h3>
          </div>
          <div className="bg-darkBg/30 p-5 rounded-xl border border-darkBorder space-y-4 text-xs text-gray-300">
            <p>Based on behavioral friction and encountered console crashes, prioritize these items:</p>
            <ul className="space-y-3">
              <li className="flex gap-2">
                <span className="text-neonOrange shrink-0">1.</span>
                <div>
                  <strong className="text-white block font-bold mb-0.5">Streamline Form Flows:</strong>
                  Ensure input fields have explicit labels, autocomplete support, and error validations. Confused Novices and Impatient Scanners churn fast at inputs.
                </div>
              </li>
              <li className="flex gap-2">
                <span className="text-neonOrange shrink-0">2.</span>
                <div>
                  <strong className="text-white block font-bold mb-0.5">Stabilize DOM Click handlers:</strong>
                  Resolve any element overlaps or loading latency which cause clicks to fail or trigger timeout exceptions.
                </div>
              </li>
              <li className="flex gap-2">
                <span className="text-neonOrange shrink-0">3.</span>
                <div>
                  <strong className="text-white block font-bold mb-0.5">Optimize Mobile/Tablet layouts:</strong>
                  Ensure interactive buttons and menus scale cleanly to fit standard viewports.
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
