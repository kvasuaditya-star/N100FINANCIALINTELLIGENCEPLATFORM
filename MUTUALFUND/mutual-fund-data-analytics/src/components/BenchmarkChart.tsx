/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo, useRef } from 'react';
import { FundMetrics, IndexPoint, DailyPoint } from '../types';
import { findClosestPoint } from '../utils/analyticsEngine';

interface BenchmarkChartProps {
  metrics: FundMetrics[];
  indices: IndexPoint[];
  dates: string[];
  fundsRaw: any[];
}

export default function BenchmarkChart({ metrics, indices, dates, fundsRaw }: BenchmarkChartProps) {
  const [hoveredPointIdx, setHoveredPointIdx] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 1. Prepare Top 5 Funds
  const top5Funds = useMemo(() => metrics.slice(0, 5), [metrics]);

  // 2. Extract last 3 years data points
  const dateData = useMemo(() => {
    const N = dates.length;
    const endD = new Date(dates[N - 1]);
    const target3YrDateStr = new Date(endD.getFullYear() - 3, endD.getMonth(), endD.getDate())
      .toISOString()
      .split('T')[0];
    
    const index3YrPrior = dates.findIndex(d => d >= target3YrDateStr);
    const startIdx = index3YrPrior !== -1 ? index3YrPrior : Math.max(0, N - 252 * 3);

    const subsetDates = dates.slice(startIdx);
    const subsetIndices = indices.slice(startIdx);

    // Map each of top 5 funds daily NAV subset
    const subsetFunds = top5Funds.map(fundMetric => {
      const fullRaw = fundsRaw.find(f => f.id === fundMetric.id);
      if (!fullRaw) return { name: fundMetric.name, navs: [] };
      return {
        id: fundMetric.id,
        name: fundMetric.name,
        navs: fullRaw.historicalNAVs.slice(startIdx) as DailyPoint[]
      };
    });

    return {
      dates: subsetDates,
      indices: subsetIndices,
      funds: subsetFunds,
      length: subsetDates.length
    };
  }, [dates, indices, top5Funds, fundsRaw]);

  // 3. Rebase NAVs/Indices to 100 at start of the 3-year window
  const rebasedCurves = useMemo(() => {
    if (dateData.length === 0) return [];

    const curves: { id: string; label: string; points: number[]; color: string; isIndex: boolean; trackingError?: number }[] = [];
    const colors = [
      '#10b981', // Emerald - Top 1
      '#06b6d4', // Cyan - Top 2
      '#8b5cf6', // Purple - Top 3
      '#f59e0b', // Amber - Top 4
      '#ec4899', // Pink - Top 5
    ];

    // Top 5 Funds
    dateData.funds.forEach((fund, idx) => {
      if (fund.navs.length === 0) return;
      const startNav = fund.navs[0].nav;
      const points = fund.navs.map(pt => (pt.nav / startNav) * 100);
      const metric = top5Funds.find(m => m.id === fund.id);
      
      curves.push({
        id: fund.id || `fund_${idx}`,
        label: fund.name,
        points,
        color: colors[idx % colors.length],
        isIndex: false,
        trackingError: metric?.trackingErrorNifty100
      });
    });

    // Nifty 100 Benchmark
    const startN100 = dateData.indices[0].nifty100;
    curves.push({
      id: 'nifty100',
      label: 'Nifty 100 Index',
      points: dateData.indices.map(idx => (idx.nifty100 / startN100) * 100),
      color: '#38bdf8', // Light sky blue
      isIndex: true,
    });

    // Nifty 50 Benchmark
    const startN50 = dateData.indices[0].nifty50;
    curves.push({
      id: 'nifty50',
      label: 'Nifty 50 Index',
      points: dateData.indices.map(idx => (idx.nifty50 / startN50) * 100),
      color: '#94a3b8', // Slate grey
      isIndex: true,
    });

    return curves;
  }, [dateData, top5Funds]);

  // 4. Calculate boundaries for drawing
  const bounds = useMemo(() => {
    let minY = 100;
    let maxY = 100;

    rebasedCurves.forEach(c => {
      c.points.forEach(p => {
        if (p < minY) minY = p;
        if (p > maxY) maxY = p;
      });
    });

    // Add padding
    minY = Math.max(0, Math.floor(minY - 10));
    maxY = Math.ceil(maxY + 10);

    return { minY, maxY };
  }, [rebasedCurves]);

  // SVG parameters
  const width = 800;
  const height = 400;
  const paddingLeft = 50;
  const paddingRight = 30;
  const paddingTop = 20;
  const paddingBottom = 40;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Coordinate mappers
  const getX = (idx: number) => paddingLeft + (idx / (dateData.length - 1)) * chartWidth;
  const getY = (val: number) => {
    const range = bounds.maxY - bounds.minY;
    const pct = (val - bounds.minY) / (range || 1);
    return paddingTop + chartHeight - pct * chartHeight;
  };

  // Generate path coordinates
  const linePaths = useMemo(() => {
    return rebasedCurves.map(c => {
      const coords = c.points.map((p, idx) => `${getX(idx).toFixed(1)},${getY(p).toFixed(1)}`);
      return {
        ...c,
        path: `M ${coords.join(' L ')}`
      };
    });
  }, [rebasedCurves, bounds, dateData.length]);

  // Gridlines
  const gridLines = useMemo(() => {
    const lines = [];
    const step = Math.ceil((bounds.maxY - bounds.minY) / 5);
    const startY = Math.ceil(bounds.minY / step) * step;

    for (let val = startY; val <= bounds.maxY; val += step) {
      lines.push({
        value: val,
        y: getY(val)
      });
    }
    return lines;
  }, [bounds]);

  // Handle Mouse Hovering
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!containerRef.current || dateData.length === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    
    // Scale back to SVG coordinate space
    const svgX = (x / rect.width) * width;
    const chartX = svgX - paddingLeft;
    
    if (chartX < 0 || chartX > chartWidth) {
      setHoveredPointIdx(null);
      return;
    }

    const pctX = chartX / chartWidth;
    const idx = Math.min(
      dateData.length - 1,
      Math.max(0, Math.round(pctX * (dateData.length - 1)))
    );
    setHoveredPointIdx(idx);
  };

  return (
    <div id="benchmark_chart_container" className="flex flex-col gap-6" ref={containerRef}>
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-xl border border-slate-800">
        <div>
          <h3 className="text-lg font-medium text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            3-Year Rebased Cumulative Growth Chart
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Simulates the compounding growth of ₹100 invested on <span className="font-mono text-xs bg-slate-800/80 px-1.5 py-0.5 rounded text-emerald-400">{dateData.dates[0]}</span> against indices.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <div className="bg-slate-800/60 border border-slate-700/60 px-2.5 py-1.5 rounded flex items-center gap-2">
            <span className="text-slate-400">Time Interval:</span>
            <span className="text-slate-200 font-medium">36 Months</span>
          </div>
          <div className="bg-slate-800/60 border border-slate-700/60 px-2.5 py-1.5 rounded flex items-center gap-2">
            <span className="text-slate-400">Frequency:</span>
            <span className="text-slate-200 font-medium">Daily Trading Days</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Chart Canvas Area */}
        <div className="lg:col-span-3 bg-slate-900/40 p-4 rounded-xl border border-slate-800/80 relative overflow-hidden">
          {dateData.length === 0 ? (
            <div className="h-[400px] flex items-center justify-center text-slate-500 font-mono">
              Generating active metrics...
            </div>
          ) : (
            <div className="relative">
              <svg
                viewBox={`0 0 ${width} ${height}`}
                className="w-full h-auto select-none overflow-visible"
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setHoveredPointIdx(null)}
              >
                {/* Horizontal Gridlines & Y-Axis Labels */}
                {gridLines.map((line, i) => (
                  <g key={i} className="opacity-40">
                    <line
                      x1={paddingLeft}
                      y1={line.y}
                      x2={width - paddingRight}
                      y2={line.y}
                      stroke="#475569"
                      strokeWidth={1}
                      strokeDasharray="3 3"
                    />
                    <text
                      x={paddingLeft - 10}
                      y={line.y + 4}
                      fill="#94a3b8"
                      fontSize={11}
                      fontFamily="monospace"
                      textAnchor="end"
                    >
                      {Math.round(line.value)}
                    </text>
                  </g>
                ))}

                {/* X-Axis Labels (Months/Years) */}
                {useMemo(() => {
                  const labelSteps = 5;
                  const stepSize = Math.floor(dateData.length / labelSteps);
                  return Array.from({ length: labelSteps + 1 }).map((_, i) => {
                    const idx = Math.min(dateData.length - 1, i * stepSize);
                    const dateStr = dateData.dates[idx];
                    return (
                      <text
                        key={i}
                        x={getX(idx)}
                        y={height - 15}
                        fill="#94a3b8"
                        fontSize={10}
                        fontFamily="monospace"
                        textAnchor="middle"
                        className="opacity-60"
                      >
                        {new Date(dateStr).toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })}
                      </text>
                    );
                  });
                }, [dateData])}

                {/* Plot Lines */}
                {linePaths.map((line, idx) => (
                  <path
                    key={line.id}
                    d={line.path}
                    fill="none"
                    stroke={line.color}
                    strokeWidth={line.isIndex ? 2.5 : 1.8}
                    strokeDasharray={line.isIndex ? (line.id === 'nifty100' ? '5 5' : '3 3') : 'none'}
                    className="transition-all duration-300"
                    style={{
                      opacity: hoveredPointIdx === null ? 0.95 : 0.4
                    }}
                  />
                ))}

                {/* Hover Vertical Line and Points */}
                {hoveredPointIdx !== null && (
                  <g>
                    <line
                      x1={getX(hoveredPointIdx)}
                      y1={paddingTop}
                      x2={getX(hoveredPointIdx)}
                      y2={paddingTop + chartHeight}
                      stroke="#64748b"
                      strokeWidth={1}
                      strokeDasharray="2 2"
                    />

                    {/* Plot Points on Hover Line */}
                    {rebasedCurves.map(c => {
                      const val = c.points[hoveredPointIdx];
                      return (
                        <circle
                          key={c.id}
                          cx={getX(hoveredPointIdx)}
                          cy={getY(val)}
                          r={4.5}
                          fill="#0f172a"
                          stroke={c.color}
                          strokeWidth={2}
                        />
                      );
                    })}
                  </g>
                )}
              </svg>
              
              {/* Floating Tooltip in Canvas Area */}
              {hoveredPointIdx !== null && (
                <div
                  className="absolute bg-slate-950/95 border border-slate-800 p-3 rounded-lg shadow-xl text-xs z-20 w-64 pointer-events-none"
                  style={{
                    left: `${Math.min(70, (getX(hoveredPointIdx) / width) * 100)}%`,
                    top: '20px'
                  }}
                >
                  <p className="text-slate-400 font-mono border-b border-slate-800 pb-1.5 mb-1.5 flex justify-between">
                    <span>Date:</span>
                    <span className="text-slate-200 font-medium">
                      {new Date(dateData.dates[hoveredPointIdx]).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </span>
                  </p>
                  <div className="flex flex-col gap-1 font-mono">
                    {rebasedCurves.map(c => (
                      <div key={c.id} className="flex justify-between items-center text-[11px]">
                        <span className="flex items-center gap-1.5 truncate max-w-[140px]">
                          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c.color }} />
                          <span className="text-slate-300 truncate">{c.label}</span>
                        </span>
                        <span className="text-slate-100 font-medium">
                          {c.points[hoveredPointIdx].toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Legend & Tracking Error Stats Side Panel */}
        <div className="flex flex-col gap-4">
          <h4 className="text-xs font-semibold uppercase text-slate-500 font-mono tracking-wider">
            Rebased Cumulative Yield & Tracking Error
          </h4>
          <div className="flex flex-col gap-2.5">
            {rebasedCurves.map((c, idx) => {
              const lastVal = c.points[c.points.length - 1];
              const yieldPct = lastVal - 100;
              return (
                <div
                  key={c.id}
                  className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/80 flex flex-col gap-1 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 truncate max-w-[150px]">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.color }} />
                      <span className="text-slate-200 text-xs font-medium truncate">{c.label}</span>
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {c.isIndex ? 'Index' : `Rank #${idx + 1}`}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between mt-1">
                    <span className="text-[10px] text-slate-400">Growth:</span>
                    <span className="text-xs font-mono font-bold text-slate-100">
                      ₹{lastVal.toFixed(1)} <span className={`text-[10px] font-normal ${yieldPct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        ({yieldPct >= 0 ? '+' : ''}{yieldPct.toFixed(1)}%)
                      </span>
                    </span>
                  </div>
                  {!c.isIndex && c.trackingError !== undefined && (
                    <div className="flex items-center justify-between border-t border-slate-800/60 pt-1 mt-1 text-[10px] font-mono">
                      <span className="text-slate-500">Tracking Error:</span>
                      <span className="text-cyan-400">{(c.trackingError * 100).toFixed(2)}% p.a.</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
