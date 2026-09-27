import React, { useState, useRef } from 'react';

export interface ChartDataPoint {
  label: string;
  value: number;
  secondaryValue?: number;
  date?: string;
  meta?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
    details?: string;
  };
}

interface SmoothAreaChartProps {
  data: ChartDataPoint[];
  height?: number;
  colorScheme?: 'sky' | 'emerald' | 'rose' | 'amber';
  valueLabel?: string;
  secondaryLabel?: string;
  showSecondary?: boolean;
}

export const SmoothAreaChart: React.FC<SmoothAreaChartProps> = ({
  data,
  height = 240,
  colorScheme = 'sky',
  valueLabel = 'Incidents',
  secondaryLabel = 'Resolved',
  showSecondary = false,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-500 text-xs font-mono">
        No telemetry data available for visualization
      </div>
    );
  }

  const width = 600;
  const padding = { top: 20, right: 20, bottom: 35, left: 35 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Compute domain
  const maxValue = Math.max(
    ...data.map((d) => Math.max(d.value, showSecondary && d.secondaryValue ? d.secondaryValue : 0)),
    10
  );

  // Generate coordinates
  const points = data.map((d, i) => {
    const x = padding.left + (i / Math.max(data.length - 1, 1)) * graphWidth;
    const y = padding.top + graphHeight - (d.value / maxValue) * graphHeight;
    return { x, y, data: d };
  });

  const secondaryPoints = showSecondary
    ? data.map((d, i) => {
        const x = padding.left + (i / Math.max(data.length - 1, 1)) * graphWidth;
        const val = d.secondaryValue || 0;
        const y = padding.top + graphHeight - (val / maxValue) * graphHeight;
        return { x, y, data: d };
      })
    : [];

  // Helper to build smooth cubic bezier path
  const buildSmoothPath = (pts: { x: number; y: number }[]) => {
    if (pts.length === 0) return '';
    if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;

    let path = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = i > 0 ? pts[i - 1] : pts[i];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = i < pts.length - 2 ? pts[i + 2] : p2;

      // Tension factor
      const tension = 0.2;
      const cp1x = p1.x + (p2.x - p0.x) * tension;
      const cp1y = p1.y + (p2.y - p0.y) * tension;
      const cp2x = p2.x - (p3.x - p1.x) * tension;
      const cp2y = p2.y - (p3.y - p1.y) * tension;

      path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
    return path;
  };

  const linePath = buildSmoothPath(points);
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + graphHeight} L ${
    points[0].x
  } ${padding.top + graphHeight} Z`;

  const secondaryLinePath = showSecondary ? buildSmoothPath(secondaryPoints) : '';

  // Theme gradient config
  const gradientStyles = {
    sky: {
      gradientId: 'gradient-sky',
      stroke: '#38bdf8',
      fillStart: 'rgba(56, 189, 248, 0.45)',
      fillEnd: 'rgba(56, 189, 248, 0.0)',
      dotColor: '#0284c7',
      glowColor: 'rgba(56, 189, 248, 0.4)',
    },
    emerald: {
      gradientId: 'gradient-emerald',
      stroke: '#10b981',
      fillStart: 'rgba(16, 185, 129, 0.45)',
      fillEnd: 'rgba(16, 185, 129, 0.0)',
      dotColor: '#059669',
      glowColor: 'rgba(16, 185, 129, 0.4)',
    },
    rose: {
      gradientId: 'gradient-rose',
      stroke: '#f43f5e',
      fillStart: 'rgba(244, 63, 94, 0.45)',
      fillEnd: 'rgba(244, 63, 94, 0.0)',
      dotColor: '#e11d48',
      glowColor: 'rgba(244, 63, 94, 0.4)',
    },
    amber: {
      gradientId: 'gradient-amber',
      stroke: '#f59e0b',
      fillStart: 'rgba(245, 158, 11, 0.45)',
      fillEnd: 'rgba(245, 158, 11, 0.0)',
      dotColor: '#d97706',
      glowColor: 'rgba(245, 158, 11, 0.4)',
    },
  }[colorScheme];

  // Mouse movement handler
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = ((e.clientX - rect.left) / rect.width) * width;

    // Find nearest point
    let closestIndex = 0;
    let minDistance = Infinity;

    points.forEach((pt, idx) => {
      const dist = Math.abs(pt.x - mouseX);
      if (dist < minDistance) {
        minDistance = dist;
        closestIndex = idx;
      }
    });

    setHoverIndex(closestIndex);
  };

  const activePoint = hoverIndex !== null ? points[hoverIndex] : null;

  return (
    <div className="relative w-full overflow-hidden select-none">
      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto overflow-visible"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoverIndex(null)}
      >
        <defs>
          <linearGradient id={gradientStyles.gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={gradientStyles.fillStart} />
            <stop offset="100%" stopColor={gradientStyles.fillEnd} />
          </linearGradient>
          {showSecondary && (
            <linearGradient id="gradient-secondary" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(16, 185, 129, 0.35)" />
              <stop offset="100%" stopColor="rgba(16, 185, 129, 0.0)" />
            </linearGradient>
          )}
        </defs>

        {/* Horizontal Background Grid Lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const y = padding.top + graphHeight * (1 - pct);
          const val = Math.round(maxValue * pct);
          return (
            <g key={i}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="rgba(51, 65, 85, 0.35)"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
              <text
                x={padding.left - 6}
                y={y + 3}
                fill="#64748b"
                fontSize="9"
                fontFamily="JetBrains Mono, monospace"
                textAnchor="end"
              >
                {val}
              </text>
            </g>
          );
        })}

        {/* X-Axis Ticks */}
        {points.map((pt, i) => {
          if (data.length > 8 && i % Math.ceil(data.length / 6) !== 0 && i !== data.length - 1)
            return null;
          return (
            <text
              key={i}
              x={pt.x}
              y={height - 10}
              fill="#94a3b8"
              fontSize="9"
              fontFamily="Inter, sans-serif"
              textAnchor="middle"
            >
              {pt.data.label}
            </text>
          );
        })}

        {/* Gradient Area Fills */}
        <path d={areaPath} fill={`url(#${gradientStyles.gradientId})`} />

        {/* Main Smooth Line */}
        <path
          d={linePath}
          fill="none"
          stroke={gradientStyles.stroke}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ filter: `drop-shadow(0 2px 6px ${gradientStyles.glowColor})` }}
        />

        {/* Secondary Line if applicable */}
        {showSecondary && (
          <path
            d={secondaryLinePath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2"
            strokeDasharray="4 3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {/* Interactive Hover Indicators */}
        {activePoint && (
          <g>
            {/* Vertical Crosshair Line */}
            <line
              x1={activePoint.x}
              y1={padding.top}
              x2={activePoint.x}
              y2={padding.top + graphHeight}
              stroke="#38bdf8"
              strokeWidth="1"
              strokeDasharray="3 3"
              opacity="0.8"
            />

            {/* Glowing Main Point Dot */}
            <circle
              cx={activePoint.x}
              cy={activePoint.y}
              r="7"
              fill={gradientStyles.stroke}
              opacity="0.3"
              className="animate-ping"
            />
            <circle
              cx={activePoint.x}
              cy={activePoint.y}
              r="4.5"
              fill={gradientStyles.stroke}
              stroke="#070b14"
              strokeWidth="2"
            />

            {/* Secondary Point Dot */}
            {showSecondary && secondaryPoints[hoverIndex!] && (
              <circle
                cx={secondaryPoints[hoverIndex!].x}
                cy={secondaryPoints[hoverIndex!].y}
                r="3.5"
                fill="#10b981"
                stroke="#070b14"
                strokeWidth="1.5"
              />
            )}
          </g>
        )}
      </svg>

      {/* Floating Interactive Tooltip */}
      {activePoint && (
        <div
          className="absolute z-30 pointer-events-none transition-all duration-75"
          style={{
            left: `${(activePoint.x / width) * 100}%`,
            top: `${Math.max(10, (activePoint.y / height) * 100 - 30)}%`,
            transform:
              activePoint.x > width * 0.75
                ? 'translate(-105%, -50%)'
                : activePoint.x < width * 0.25
                ? 'translate(10%, -50%)'
                : 'translate(-50%, -115%)',
          }}
        >
          <div className="glass-card rounded-xl p-3 border border-slate-700/80 shadow-2xl backdrop-blur-md min-w-[150px]">
            <div className="flex items-center justify-between gap-2 pb-1.5 mb-1.5 border-b border-slate-800">
              <span className="text-[11px] font-bold text-slate-200">{activePoint.data.label}</span>
              {activePoint.data.date && (
                <span className="text-[9px] font-mono text-slate-400">{activePoint.data.date}</span>
              )}
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between gap-3">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: gradientStyles.stroke }}
                  />
                  {valueLabel}:
                </span>
                <span className="font-mono font-bold text-white">
                  {activePoint.data.value}
                </span>
              </div>

              {showSecondary && typeof activePoint.data.secondaryValue === 'number' && (
                <div className="flex items-center justify-between gap-3">
                  <span className="text-slate-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    {secondaryLabel}:
                  </span>
                  <span className="font-mono font-bold text-emerald-300">
                    {activePoint.data.secondaryValue}
                  </span>
                </div>
              )}

              {activePoint.data.meta && (
                <div className="pt-1.5 mt-1 border-t border-slate-800/80 flex items-center justify-between text-[10px]">
                  <span className="text-rose-400 font-semibold">
                    {activePoint.data.meta.critical ?? 0} Critical
                  </span>
                  <span className="text-amber-400 font-semibold">
                    {activePoint.data.meta.medium ?? 0} Med
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
