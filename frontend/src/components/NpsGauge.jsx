import React from 'react';

export default function NpsGauge({ score = 0 }) {
  // Map score from [-100, 100] to rotation angle [0, 180]
  const percentage = (score + 100) / 200;
  const rotationAngle = percentage * 180 - 90; // -90 deg is horizontal left, 90 deg is horizontal right

  let ratingLabel = 'Good';
  let ratingColor = 'text-neonCyan';
  
  if (score >= 70) {
    ratingLabel = 'Excellent';
    ratingColor = 'text-neonGreen';
  } else if (score >= 30) {
    ratingLabel = 'Very Good';
    ratingColor = 'text-neonPurple';
  } else if (score >= 0) {
    ratingLabel = 'Average';
    ratingColor = 'text-neonOrange';
  } else {
    ratingLabel = 'Detrimental';
    ratingColor = 'text-neonRed';
  }

  // Format sign prefix
  const formattedScore = score > 0 ? `+${score}` : score;

  return (
    <div className="bg-darkCard border border-darkBorder rounded-2xl p-6 flex flex-col items-center text-center justify-between h-full relative">
      <div className="w-full flex justify-between items-center mb-4">
        <h3 className="font-bold text-white text-md flex items-center gap-1.5">
          🎯 NPS Prediction
        </h3>
        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
          Net Promoter Score
        </span>
      </div>

      {/* SVG Speedometer Gauge */}
      <div className="relative w-48 h-24 flex items-end justify-center overflow-hidden pt-2">
        <svg className="w-full h-full" viewBox="0 0 100 50">
          <defs>
            <linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="35%" stopColor="#f97316" />
              <stop offset="70%" stopColor="#8b5cf6" />
              <stop offset="100%" stopColor="#10b981" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          {/* Gauge Track */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#1f2937"
            strokeWidth="8"
            strokeLinecap="round"
            className="nps-gauge-track"
          />
          
          {/* Active Gradient Track */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="url(#gauge-grad)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray="126"
            strokeDashoffset={126 - (percentage * 126)}
            className="transition-all duration-1000 ease-out"
          />

          {/* Needle Pin */}
          <circle cx="50" cy="50" r="4" fill="#f3f4f6" className="nps-needle-pin" />
          
          {/* Needle Line */}
          <line
            x1="50" y1="50"
            x2="50" y2="15"
            stroke="#f3f4f6"
            strokeWidth="2.5"
            strokeLinecap="round"
            transform={`rotate(${rotationAngle} 50 50)`}
            className="transition-transform duration-1000 ease-out origin-center nps-needle-line"
            filter="url(#glow)"
          />
        </svg>

        {/* Floating Core Score */}
        <div className="absolute bottom-0 text-center">
          <div className="text-3xl font-extrabold text-white tracking-tight leading-none">
            {formattedScore}
          </div>
          <div className={`text-[10px] font-bold mt-1 ${ratingColor} uppercase tracking-widest`}>
            {ratingLabel}
          </div>
        </div>
      </div>

      {/* Details Description */}
      <div className="mt-4 pt-3 border-t border-darkBorder/60 w-full flex justify-between text-[10px] text-gray-500 font-semibold uppercase">
        <span className="text-neonRed">-100 Min</span>
        <span className="text-neonGreen">+100 Max</span>
      </div>
    </div>
  );
}
