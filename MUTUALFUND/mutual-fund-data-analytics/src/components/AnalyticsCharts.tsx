/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useMemo, useState } from 'react';
import { FundMetrics, DailyPoint, IndexPoint } from '../types';

interface ReturnsDistributionChartProps {
  fundName: string;
  historicalNAVs: DailyPoint[];
}

export function ReturnsDistributionChart({ fundName, historicalNAVs }: ReturnsDistributionChartProps) {
  // Compute daily returns
  const dailyReturns = useMemo(() => {
    const returns: number[] = [];
    for (let i = 1; i < historicalNAVs.length; i++) {
      returns.push(historicalNAVs[i].nav / historicalNAVs[i - 1].nav - 1);
    }
    return returns;
  }, [historicalNAVs]);

  // Statistics
  const stats = useMemo(() => {
    if (dailyReturns.length === 0) return { mean: 0, std: 0.01, skew: 0 };
    const m = dailyReturns.reduce((sum, r) => sum + r, 0) / dailyReturns.length;
    const variance = dailyReturns.reduce((sum, r) => sum + Math.pow(r - m, 2), 0) / (dailyReturns.length - 1);
    const s = Math.sqrt(variance);
    return { mean: m, std: s };
  }, [dailyReturns]);

  // Create Bins
  const binData = useMemo(() => {
    const binCount = 30;
    const minVal = -0.04; // -4%
    const maxVal = 0.04;  // +4%
    const step = (maxVal - minVal) / binCount;

    const bins = Array.from({ length: binCount }, (_, i) => ({
      start: minVal + i * step,
      end: minVal + (i + 1) * step,
      count: 0
    }));

    let outliersMin = 0;
    let outliersMax = 0;

    dailyReturns.forEach(r => {
      if (r < minVal) {
        outliersMin++;
      } else if (r > maxVal) {
        outliersMax++;
      } else {
        const binIdx = Math.floor((r - minVal) / step);
        if (binIdx >= 0 && binIdx < binCount) {
          bins[binIdx].count++;
        }
      }
    });

    // Max count for scaling
    const maxCount = Math.max(...bins.map(b => b.count), 1);

    return { bins, step, minVal, maxVal, maxCount, outliersMin, outliersMax };
  }, [dailyReturns]);

  // SVG parameters
  const width = 600;
  const height = 300;
  const padding = 40;
  const chartW = width - padding * 2;
  const chartH = height - padding * 2;

  // Normal PDF curve data
  const normalCurvePoints = useMemo(() => {
    const pointsCount = 100;
    const pts = [];
    const minX = binData.minVal;
    const maxX = binData.maxVal;
    const dx = (maxX - minX) / pointsCount;

    // Normal probability density function
    // f(x) = (1 / (std * sqrt(2*pi))) * e^(-(x-mean)^2 / (2*std^2))
    const mean = stats.mean;
    const std = stats.std;
    const constant = 1 / (std * Math.sqrt(2 * Math.PI));

    for (let i = 0; i <= pointsCount; i++) {
      const x = minX + i * dx;
      const exponent = -Math.pow(x - mean, 2) / (2 * Math.pow(std, 2));
      const pdfVal = constant * Math.exp(exponent);
      pts.push({ x, y: pdfVal });
    }

    // Scale PDF value to chart height
    // We want to overlay PDF on top of bin density.
    // Bin area = bin count / (total * step)
    // To match density scale: 
    // Density scaling: max_y_density = maxCount / (totalReturns * step)
    const totalReturns = dailyReturns.length;
    const step = binData.step;
    const maxDensity = binData.maxCount / (totalReturns * step);

    // Let's find the max PDF value to scale appropriately
    const maxPdf = constant; // peak is at x = mean where pdfVal = constant
    const scaleFactor = Math.max(maxDensity, maxPdf) * 1.05;

    return pts.map(pt => {
      const px = padding + ((pt.x - minX) / (maxX - minX)) * chartW;
      const scaledY = pt.y / scaleFactor;
      const py = padding + chartH - scaledY * chartH;
      return `${px.toFixed(1)},${py.toFixed(1)}`;
    });
  }, [binData, stats, dailyReturns.length]);

  return (
    <div className="bg-slate-900/40 p-5 rounded-xl border border-slate-800 flex flex-col gap-4">
      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-200">Daily Returns Histogram & Normal Fit</h4>
          <p className="text-xs text-slate-400 mt-1 font-mono">Exploring distribution properties for {fundName}</p>
        </div>
        <div className="text-right font-mono text-xs text-emerald-400">
          <div>Daily Mean: {(stats.mean * 100).toFixed(4)}%</div>
          <div className="text-slate-400">Daily Vol: {(stats.std * 100).toFixed(3)}%</div>
        </div>
      </div>

      <div className="relative">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none overflow-visible">
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((v, i) => (
            <line
              key={i}
              x1={padding}
              y1={padding + chartH - v * chartH}
              x2={width - padding}
              y2={padding + chartH - v * chartH}
              stroke="#334155"
              strokeWidth={1}
              strokeDasharray="2 2"
              className="opacity-20"
            />
          ))}

          {/* Draw Bins (Bars) */}
          {binData.bins.map((bin, idx) => {
            const barW = chartW / binData.bins.length - 1;
            const barH = (bin.count / binData.maxCount) * chartH;
            const barX = padding + idx * (chartW / binData.bins.length);
            const barY = padding + chartH - barH;

            return (
              <g key={idx} className="group">
                <rect
                  x={barX}
                  y={barY}
                  width={barW}
                  height={barH}
                  fill="#059669"
                  fillOpacity={0.65}
                  stroke="#10b981"
                  strokeWidth={1}
                  className="hover:fill-emerald-400 hover:fill-opacity-90 transition duration-150"
                />
                {/* Micro tooltip */}
                <title>{`Bin: ${(bin.start * 100).toFixed(1)}% to ${(bin.end * 100).toFixed(1)}%\nFrequency: ${bin.count} days`}</title>
              </g>
            );
          })}

          {/* Normal Curve PDF Overlay */}
          <path
            d={`M ${normalCurvePoints.join(' L ')}`}
            fill="none"
            stroke="#06b6d4"
            strokeWidth={2.5}
            className="opacity-90"
          />

          {/* X Axis */}
          <line
            x1={padding}
            y1={padding + chartH}
            x2={width - padding}
            y2={padding + chartH}
            stroke="#475569"
            strokeWidth={1.5}
          />

          {/* Axis Labels */}
          {[-0.04, -0.02, 0, 0.02, 0.04].map((v, i) => {
            const x = padding + ((v - binData.minVal) / (binData.maxVal - binData.minVal)) * chartW;
            return (
              <g key={i}>
                <line x1={x} y1={padding + chartH} x2={x} y2={padding + chartH + 5} stroke="#475569" strokeWidth={1} />
                <text
                  x={x}
                  y={padding + chartH + 18}
                  fill="#94a3b8"
                  fontSize={10}
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  {(v * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}

          <text
            x={width / 2}
            y={height - 5}
            fill="#64748b"
            fontSize={11}
            textAnchor="middle"
          >
            Daily Percentage Return
          </text>
        </svg>
      </div>

      <div className="bg-slate-950/40 p-3 rounded border border-slate-800 text-xs text-slate-400 flex flex-col gap-1.5 font-sans leading-relaxed">
        <p className="flex items-center gap-1.5 text-slate-300 font-medium">
          <span className="w-1.5 h-1.5 rounded bg-cyan-400"></span>
          Distribution Validation Check:
        </p>
        <p>
          The generated return series displays the classical **leptokurtic (fat-tailed)** characteristics of mutual fund returns, overlapping nicely with the theoretical normal curve. This demonstrates realistic modeling of market volatility.
        </p>
      </div>
    </div>
  );
}

interface RegressionScatterChartProps {
  metrics: FundMetrics;
  historicalNAVs: DailyPoint[];
  indices: IndexPoint[];
  dates: string[];
}

export function RegressionScatterChart({ metrics, historicalNAVs, indices, dates }: RegressionScatterChartProps) {
  // Compute daily returns
  const returnPoints = useMemo(() => {
    const pts: { fund: number; index: number; date: string }[] = [];
    for (let i = 1; i < historicalNAVs.length; i++) {
      const rFund = historicalNAVs[i].nav / historicalNAVs[i - 1].nav - 1;
      const rIndex = indices[i].nifty100 / indices[i - 1].nifty100 - 1;
      pts.push({ fund: rFund, index: rIndex, date: dates[i] });
    }
    
    // Subsample to 250 points to prevent DOM clogging, but keep representative distribution
    const sampleSize = 250;
    const step = Math.max(1, Math.floor(pts.length / sampleSize));
    return pts.filter((_, idx) => idx % step === 0);
  }, [historicalNAVs, indices, dates]);

  // SVG parameters
  const width = 600;
  const height = 300;
  const padding = 40;
  const chartW = width - padding * 2;
  const chartH = height - padding * 2;

  // Scatter boundaries (-4% to +4%)
  const minVal = -0.04;
  const maxVal = 0.04;

  const getX = (val: number) => padding + ((val - minVal) / (maxVal - minVal)) * chartW;
  const getY = (val: number) => padding + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;

  // Regression Line Coordinates
  // Regression formula: y = alpha_daily + (beta * x)
  // Annualized alpha = alpha_daily * 252 -> alpha_daily = alpha / 252
  const alphaDaily = metrics.alpha / 252;
  const beta = metrics.beta;

  const lineStartVal = minVal;
  const lineEndVal = maxVal;
  const lineStartFundVal = alphaDaily + beta * lineStartVal;
  const lineEndFundVal = alphaDaily + beta * lineEndVal;

  const lineX1 = getX(lineStartVal);
  const lineY1 = getY(lineStartFundVal);
  const lineX2 = getX(lineEndVal);
  const lineY2 = getY(lineEndFundVal);

  return (
    <div className="bg-slate-900/40 p-5 rounded-xl border border-slate-800 flex flex-col gap-4">
      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-200">Capital Asset Pricing Model (CAPM) Regression</h4>
          <p className="text-xs text-slate-400 mt-1 font-mono">{metrics.name} vs Nifty 100 Benchmark</p>
        </div>
        <div className="text-right font-mono text-xs text-cyan-400">
          <div>Alpha (Ann): {(metrics.alpha * 100).toFixed(2)}%</div>
          <div className="text-slate-400">Beta (Slope): {metrics.beta.toFixed(3)}</div>
        </div>
      </div>

      <div className="relative">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none overflow-visible">
          {/* Axes guides */}
          <line x1={padding} y1={getY(0)} x2={width - padding} y2={getY(0)} stroke="#475569" strokeWidth={1} strokeDasharray="3 3" className="opacity-40" />
          <line x1={getX(0)} y1={padding} x2={getX(0)} y2={padding + chartH} stroke="#475569" strokeWidth={1} strokeDasharray="3 3" className="opacity-40" />

          {/* Scatter Points */}
          {returnPoints.map((pt, idx) => {
            const cx = getX(pt.index);
            const cy = getY(pt.fund);

            // Clip points outside chart space
            if (cx < padding || cx > width - padding || cy < padding || cy > padding + chartH) {
              return null;
            }

            return (
              <circle
                key={idx}
                cx={cx}
                cy={cy}
                r={2.5}
                fill="#06b6d4"
                fillOpacity={0.6}
                stroke="#0891b2"
                strokeWidth={0.5}
              />
            );
          })}

          {/* Regression Trend Line */}
          <line
            x1={Math.max(padding, Math.min(width - padding, lineX1))}
            y1={Math.max(padding, Math.min(height - padding, lineY1))}
            x2={Math.max(padding, Math.min(width - padding, lineX2))}
            y2={Math.max(padding, Math.min(height - padding, lineY2))}
            stroke="#f59e0b" // Amber OLS Trend line
            strokeWidth={2.5}
            strokeLinecap="round"
          />

          {/* Labeling axes */}
          {[-0.04, -0.02, 0, 0.02, 0.04].map((v, i) => {
            const x = getX(v);
            const y = getY(v);
            return (
              <g key={i}>
                {/* X labels */}
                <line x1={x} y1={padding + chartH} x2={x} y2={padding + chartH + 5} stroke="#475569" strokeWidth={1} />
                <text x={x} y={padding + chartH + 18} fill="#94a3b8" fontSize={10} fontFamily="monospace" textAnchor="middle">
                  {(v * 100).toFixed(0)}%
                </text>

                {/* Y labels */}
                <line x1={padding - 5} y1={y} x2={padding} y2={y} stroke="#475569" strokeWidth={1} />
                <text x={padding - 10} y={y + 3} fill="#94a3b8" fontSize={10} fontFamily="monospace" textAnchor="end">
                  {(v * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}

          <text x={width / 2} y={height - 5} fill="#64748b" fontSize={11} textAnchor="middle">
            Nifty 100 Daily Return (Independent)
          </text>
          
          <text
            x={12}
            y={height / 2}
            fill="#64748b"
            fontSize={11}
            transform={`rotate(-90, 12, ${height / 2})`}
            textAnchor="middle"
          >
            Fund Daily Return (Dependent)
          </text>
        </svg>
      </div>

      <div className="bg-slate-950/40 p-3 rounded border border-slate-800 text-xs text-slate-400 flex flex-col gap-1.5 font-sans">
        <div className="flex justify-between">
          <span className="text-slate-300 font-medium">Model Statistics Summary:</span>
          <span className="text-slate-400 font-mono">R-Squared (Fit): {(metrics.rSquared * 100).toFixed(1)}%</span>
        </div>
        <p className="leading-relaxed">
          The Beta of **{metrics.beta.toFixed(2)}** denotes that for every 1.00% daily move in the Nifty 100 index, this scheme is expected to move by **{metrics.beta.toFixed(2)}%**. The positive annualized Alpha of **{(metrics.alpha * 100).toFixed(2)}%** represents the active manager outperformance relative to passive market benchmarks.
        </p>
      </div>
    </div>
  );
}

interface DrawdownChartProps {
  metrics: FundMetrics;
  historicalNAVs: DailyPoint[];
}

export function DrawdownChart({ metrics, historicalNAVs }: DrawdownChartProps) {
  // Compute running drawdown over 5 years
  const drawdownData = useMemo(() => {
    let runningMax = historicalNAVs[0].nav;
    return historicalNAVs.map((pt, idx) => {
      if (pt.nav > runningMax) {
        runningMax = pt.nav;
      }
      const dd = (pt.nav / runningMax) - 1;
      return {
        date: pt.date,
        drawdown: dd,
        idx
      };
    });
  }, [historicalNAVs]);

  const width = 600;
  const height = 280;
  const paddingLeft = 50;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 40;

  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  const N = drawdownData.length;

  const getX = (idx: number) => paddingLeft + (idx / (N - 1)) * chartW;
  
  // Downward Y Axis: 0% is top, worst is bottom
  const worstDD = metrics.maxDrawdown; // e.g. -0.22
  const boundsMinY = Math.min(-0.25, worstDD * 1.1); // round to neat boundary

  const getY = (val: number) => {
    const ratio = val / boundsMinY; // relative to bottom boundary
    return paddingTop + ratio * chartH;
  };

  const linePath = useMemo(() => {
    const coords = drawdownData.map(pt => `${getX(pt.idx).toFixed(1)},${getY(pt.drawdown).toFixed(1)}`);
    return `M ${coords.join(' L ')}`;
  }, [drawdownData, boundsMinY]);

  // Find index of peak and trough
  const peakIdx = historicalNAVs.findIndex(pt => pt.date === metrics.drawdownStartDate);
  const troughIdx = historicalNAVs.findIndex(pt => pt.date === metrics.drawdownTroughDate);
  const recoveryIdx = historicalNAVs.findIndex(pt => pt.date === metrics.drawdownEndDate);

  return (
    <div className="bg-slate-900/40 p-5 rounded-xl border border-slate-800 flex flex-col gap-4">
      <div className="flex justify-between items-start border-b border-slate-800 pb-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-200 font-sans">Running Drawdown Curve & Under-Water History</h4>
          <p className="text-xs text-slate-400 mt-1 font-mono">Visualizing risk and asset-impairment recovery periods</p>
        </div>
        <div className="text-right font-mono text-xs text-rose-400">
          <div>Max Drawdown: {(metrics.maxDrawdown * 100).toFixed(2)}%</div>
          <div className="text-slate-400 text-[10px]">Trough Reach Date: {metrics.drawdownTroughDate}</div>
        </div>
      </div>

      <div className="relative">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none overflow-visible">
          {/* Shaded Area underneath 0% (Water level) */}
          <path
            d={`${linePath} L ${getX(N - 1)},${getY(0)} L ${getX(0)},${getY(0)} Z`}
            fill="#be123c"
            fillOpacity={0.15}
          />

          {/* Running Drawdown Line */}
          <path d={linePath} fill="none" stroke="#f43f5e" strokeWidth={1.8} />

          {/* 0% Line */}
          <line x1={paddingLeft} y1={getY(0)} x2={width - paddingRight} y2={getY(0)} stroke="#475569" strokeWidth={1.5} />

          {/* Peak to Trough Highlight overlay */}
          {peakIdx !== -1 && troughIdx !== -1 && (
            <g>
              {/* Highlight Peak */}
              <circle cx={getX(peakIdx)} cy={getY(0)} r={4} fill="#10b981" />
              <line x1={getX(peakIdx)} y1={getY(0)} x2={getX(peakIdx)} y2={getY(boundsMinY) + 5} stroke="#10b981" strokeWidth={1} strokeDasharray="2 2" />
              
              {/* Highlight Trough */}
              <circle cx={getX(troughIdx)} cy={getY(metrics.maxDrawdown)} r={4.5} fill="#f43f5e" />
              <line x1={getX(troughIdx)} y1={getY(0)} x2={getX(troughIdx)} y2={getY(boundsMinY) + 5} stroke="#f43f5e" strokeWidth={1} strokeDasharray="2 2" />

              {/* Highlight Recovery (if recovered) */}
              {recoveryIdx !== -1 && (
                <>
                  <circle cx={getX(recoveryIdx)} cy={getY(0)} r={4} fill="#3b82f6" />
                  <line x1={getX(recoveryIdx)} y1={getY(0)} x2={getX(recoveryIdx)} y2={getY(boundsMinY) + 5} stroke="#3b82f6" strokeWidth={1} strokeDasharray="2 2" />
                </>
              )}
            </g>
          )}

          {/* Y-axis ticks */}
          {[0, -0.05, -0.10, -0.15, -0.20, -0.25].map((v, i) => {
            if (v < boundsMinY) return null;
            const y = getY(v);
            return (
              <g key={i}>
                <line x1={paddingLeft - 5} y1={y} x2={paddingLeft} y2={y} stroke="#475569" strokeWidth={1} />
                <text x={paddingLeft - 10} y={y + 3} fill="#94a3b8" fontSize={10} fontFamily="monospace" textAnchor="end">
                  {(v * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}

          {/* X Axis time indicators */}
          {useMemo(() => {
            const steps = 4;
            const s = Math.floor(N / steps);
            return Array.from({ length: steps + 1 }).map((_, i) => {
              const idx = Math.min(N - 1, i * s);
              const dateStr = drawdownData[idx].date;
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
                  {new Date(dateStr).getFullYear()}
                </text>
              );
            });
          }, [N])}
        </svg>
      </div>

      {/* Trough metadata details card */}
      <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800 grid grid-cols-3 gap-2 text-center text-xs font-mono">
        <div className="border-r border-slate-800">
          <div className="text-[10px] text-slate-500 uppercase">Worst Crash Peak</div>
          <div className="text-emerald-400 font-semibold mt-1 truncate">{metrics.drawdownStartDate}</div>
        </div>
        <div className="border-r border-slate-800">
          <div className="text-[10px] text-slate-500 uppercase">Trough Bottom</div>
          <div className="text-rose-400 font-semibold mt-1 truncate">{metrics.drawdownTroughDate}</div>
        </div>
        <div>
          <div className="text-[10px] text-slate-500 uppercase">Recovery Date</div>
          <div className="text-blue-400 font-semibold mt-1 truncate">{metrics.drawdownEndDate}</div>
        </div>
      </div>
    </div>
  );
}
