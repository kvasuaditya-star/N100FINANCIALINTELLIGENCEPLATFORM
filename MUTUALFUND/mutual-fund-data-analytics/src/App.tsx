/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo, useRef, useEffect } from 'react';
import { generateDataset } from './utils/dataGenerator';
import { computeAllMetrics } from './utils/analyticsEngine';
import { generateScorecardCSV, generateAlphaBetaCSV, generateJupyterNotebook } from './utils/deliverableGenerators';
import { FundCategory, FundMetrics } from './types';
import BenchmarkChart from './components/BenchmarkChart';
import { ReturnsDistributionChart, RegressionScatterChart, DrawdownChart } from './components/AnalyticsCharts';
import DeveloperGuide from './components/DeveloperGuide';
import {
  TrendingUp,
  Award,
  Download,
  Terminal,
  Grid,
  BarChart3,
  LineChart,
  ShieldAlert,
  ChevronDown,
  Search,
  CheckCircle,
  HelpCircle,
  TrendingDown,
  Activity,
  FileSpreadsheet
} from 'lucide-react';

export default function App() {
  // 1. Initialize Dataset & Metrics (deterministic seeded on load)
  const dataPackage = useMemo(() => {
    const raw = generateDataset();
    const computed = computeAllMetrics(raw.funds, raw.indices, raw.dates);
    return {
      dates: raw.dates,
      indices: raw.indices,
      fundsRaw: raw.funds,
      metrics: computed
    };
  }, []);

  const { dates, indices, fundsRaw, metrics } = dataPackage;

  // 2. React State management
  const [activeTab, setActiveTab] = useState<'scorecard' | 'benchmark' | 'explorer' | 'downloads' | 'guide'>('scorecard');
  const [selectedCategory, setSelectedCategory] = useState<FundCategory | 'All'>('All');
  const [selectedFundId, setSelectedFundId] = useState<string>(metrics[0].id); // Defaults to Top Rank 1 fund
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortField, setSortField] = useState<keyof FundMetrics>('finalRank');
  const [sortAscending, setSortAscending] = useState<boolean>(true);
  const [copiedStatus, setCopiedStatus] = useState<string | null>(null);

  // Retrieve the currently active fund object for granular exploration charts
  const selectedFundMetrics = useMemo(() => {
    return metrics.find(m => m.id === selectedFundId) || metrics[0];
  }, [metrics, selectedFundId]);

  const selectedFundRaw = useMemo(() => {
    return fundsRaw.find(f => f.id === selectedFundId) || fundsRaw[0];
  }, [fundsRaw, selectedFundId]);

  // 3. Filtering and Sorting
  const filteredMetrics = useMemo(() => {
    return metrics
      .filter(m => {
        const matchesCategory = selectedCategory === 'All' || m.category === selectedCategory;
        const matchesSearch = m.name.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesCategory && matchesSearch;
      })
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];

        if (typeof valA === 'string' && typeof valB === 'string') {
          return sortAscending ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }

        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortAscending ? valA - valB : valB - valA;
        }

        return 0;
      });
  }, [metrics, selectedCategory, searchTerm, sortField, sortAscending]);

  const handleSort = (field: keyof FundMetrics) => {
    if (sortField === field) {
      setSortAscending(!sortAscending);
    } else {
      setSortField(field);
      setSortAscending(true);
    }
  };

  // 4. KPI Calculations (Market summary details)
  const kpis = useMemo(() => {
    const totalFunds = metrics.length;
    const medianSharpe = metrics.map(m => m.sharpeRatio).sort((a, b) => a - b)[Math.floor(totalFunds / 2)];
    const bestAlpha = Math.max(...metrics.map(m => m.alpha));
    const average3YrReturn = metrics.reduce((sum, m) => sum + m.cagr3Yr, 0) / totalFunds;
    
    return {
      totalFunds,
      medianSharpe,
      bestAlpha,
      average3YrReturn
    };
  }, [metrics]);

  // 5. File Download Triggers
  const handleDownloadFile = (filename: string, content: string, contentType: string) => {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setCopiedStatus(filename);
    setTimeout(() => setCopiedStatus(null), 3000);
  };

  // Canvas Renders of the Benchmark Comparison Plot
  const handleDownloadBenchmarkPNG = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = 600;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw dark slate layout background
    ctx.fillStyle = '#0f172a'; // Deep slate slate-900
    ctx.fillRect(0, 0, 1200, 600);

    // Padding parameters
    const padL = 80;
    const padR = 300;
    const padT = 90;
    const padB = 80;
    const plotW = 1200 - padL - padR;
    const plotH = 600 - padT - padB;

    // Gridlines (y value 100 to 240)
    ctx.strokeStyle = '#334155'; // border-slate-800
    ctx.lineWidth = 1;
    ctx.font = '12px Courier New';
    ctx.fillStyle = '#94a3b8'; // text-slate-400

    const ticks = [100, 120, 140, 160, 180, 200, 220, 240];
    ticks.forEach(tick => {
      const pctY = (tick - 80) / 180;
      const py = padT + plotH - pctY * plotH;
      
      ctx.beginPath();
      ctx.moveTo(padL, py);
      ctx.lineTo(padL + plotW, py);
      ctx.stroke();

      ctx.fillText(tick.toString(), padL - 35, py + 4);
    });

    // Time cutoff
    const subsetDates = dates.slice(dates.length - 252 * 3);
    const subsetIndices = indices.slice(dates.length - 252 * 3);
    const top5 = metrics.slice(0, 5);

    // Draw grid dates (x-axis)
    const labelCount = 6;
    ctx.textAlign = 'center';
    for (let i = 0; i < labelCount; i++) {
      const idx = Math.min(subsetDates.length - 1, Math.floor((i / (labelCount - 1)) * (subsetDates.length - 1)));
      const px = padL + (idx / (subsetDates.length - 1)) * plotW;
      ctx.fillText(subsetDates[idx], px, padT + plotH + 22);
    }

    // Colors mapping
    const fundColors = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ec4899'];
    
    // Draw curves
    const drawLine = (pts: number[], color: string, isDashed: boolean = false) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = isDashed ? 3 : 2;
      if (isDashed) {
        ctx.setLineDash([6, 6]);
      } else {
        ctx.setLineDash([]);
      }

      ctx.beginPath();
      pts.forEach((pt, idx) => {
        const px = padL + (idx / (pts.length - 1)) * plotW;
        const pctY = (pt - 80) / 180;
        const py = padT + plotH - pctY * plotH;
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();
    };

    // Plot Nifty 50
    const n50Start = subsetIndices[0].nifty50;
    const n50Pts = subsetIndices.map(pt => (pt.nifty50 / n50Start) * 100);
    drawLine(n50Pts, '#94a3b8', true);

    // Plot Nifty 100
    const n100Start = subsetIndices[0].nifty100;
    const n100Pts = subsetIndices.map(pt => (pt.nifty100 / n100Start) * 100);
    drawLine(n100Pts, '#38bdf8', true);

    // Plot Top 5 Funds
    top5.forEach((fund, fIdx) => {
      const fullRaw = fundsRaw.find(f => f.id === fund.id);
      if (!fullRaw) return;
      const fSubset = fullRaw.historicalNAVs.slice(dates.length - 252 * 3);
      const fStart = fSubset[0].nav;
      const fPts = fSubset.map(pt => (pt.nav / fStart) * 100);
      drawLine(fPts, fundColors[fIdx]);
    });

    // Plot Titles
    ctx.setLineDash([]);
    ctx.fillStyle = '#f8fafc'; // slate-50
    ctx.font = 'bold 22px Helvetica';
    ctx.textAlign = 'left';
    ctx.fillText('3-Year Cumulative Growth Performance Comparison', padL, 40);

    ctx.font = '14px Helvetica';
    ctx.fillStyle = '#10b981'; // emerald-400
    ctx.fillText('Analysis Period: 2023-06-29 to 2026-06-29  |  Initial Capital Rebased to ₹100', padL, 65);

    // Draw Legend Box
    const startX = 1200 - padR + 20;
    ctx.fillStyle = '#1e293b'; // slate-800
    ctx.fillRect(startX - 10, padT - 10, 270, 300);
    ctx.strokeStyle = '#475569'; // slate-600
    ctx.strokeRect(startX - 10, padT - 10, 270, 300);

    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 12px Helvetica';
    ctx.fillText('LEGEND & RESULTS', startX, padT + 20);

    ctx.font = '11px Courier New';
    ctx.fillStyle = '#94a3b8';

    // Index markers legends
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('--- Nifty 100 Index: ' + n100Pts[n100Pts.length - 1].toFixed(1), startX, padT + 50);
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('--- Nifty 50 Index:  ' + n50Pts[n50Pts.length - 1].toFixed(1), startX, padT + 75);

    // Top 5 funds legend
    top5.forEach((fund, fIdx) => {
      const fullRaw = fundsRaw.find(f => f.id === fund.id);
      if (!fullRaw) return;
      const fSubset = fullRaw.historicalNAVs.slice(dates.length - 252 * 3);
      const fFinal = (fSubset[fSubset.length - 1].nav / fSubset[0].nav) * 100;
      
      ctx.fillStyle = fundColors[fIdx];
      ctx.fillText(`Rank #${fIdx + 1} ${fund.name.substring(0, 15)}...`, startX, padT + 110 + fIdx * 30);
      ctx.fillStyle = '#f8fafc';
      ctx.fillText(`Yield: ${fFinal.toFixed(1)}% (TE: ${(fund.trackingErrorNifty100 * 100).toFixed(1)}%)`, startX + 15, padT + 125 + fIdx * 30);
    });

    // Signature Credit footer
    ctx.font = '10px Helvetica';
    ctx.fillStyle = '#64748b';
    ctx.fillText('Generated dynamically via Mutual Fund Data Analytics Suite', padL, 575);

    // Trigger Download
    const dataUrl = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'benchmark_comparison_chart.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setCopiedStatus('benchmark_comparison_chart.png');
    setTimeout(() => setCopiedStatus(null), 3000);
  };

  return (
    <div id="application_root" className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-100">
      
      {/* Top Banner Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-emerald-600 to-cyan-500 flex items-center justify-center text-slate-950 font-bold shadow-md shadow-emerald-500/20">
              <TrendingUp className="w-5 h-5 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <span className="font-bold text-slate-50 tracking-tight text-base sm:text-lg block">Mutual Fund Data Analytics</span>
              <span className="text-[10px] text-emerald-400 font-mono tracking-widest uppercase block -mt-1">Quantum Portfolio Suite</span>
            </div>
          </div>
          <nav className="flex items-center gap-1.5 sm:gap-2">
            {[
              { id: 'scorecard', label: 'Fund Scorecard', icon: Award },
              { id: 'benchmark', label: 'Benchmark Chart', icon: LineChart },
              { id: 'explorer', label: 'Analytical Engine', icon: BarChart3 },
              { id: 'downloads', label: 'Download Deliverables', icon: Download },
              { id: 'guide', label: 'Git Sync Guide', icon: Terminal },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-1.5 px-3 py-1.5 sm:py-2 rounded-lg text-xs font-medium transition duration-150 border ${
                  activeTab === tab.id
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-sm shadow-emerald-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                <span className="hidden md:inline">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Body Grid */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        
        {/* KPI Dashboard Grid */}
        <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-xl flex items-center gap-4 hover:border-slate-700/60 transition">
            <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
              <Grid className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-mono tracking-wider block">Schemes Analyzed</span>
              <span className="text-xl font-bold font-mono text-slate-100 block mt-0.5">{kpis.totalFunds}</span>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-xl flex items-center gap-4 hover:border-slate-700/60 transition">
            <div className="p-3 bg-cyan-500/10 rounded-lg text-cyan-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-mono tracking-wider block">Median Sharpe</span>
              <span className="text-xl font-bold font-mono text-slate-100 block mt-0.5">{kpis.medianSharpe.toFixed(3)}</span>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-xl flex items-center gap-4 hover:border-slate-700/60 transition">
            <div className="p-3 bg-violet-500/10 rounded-lg text-violet-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-mono tracking-wider block">Best Alpha (vs Nifty 100)</span>
              <span className="text-xl font-bold font-mono text-slate-100 block mt-0.5">{(kpis.bestAlpha * 100).toFixed(2)}%</span>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-xl flex items-center gap-4 hover:border-slate-700/60 transition">
            <div className="p-3 bg-amber-500/10 rounded-lg text-amber-400">
              <TrendingDown className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase text-slate-500 font-mono tracking-wider block">Average 3Yr Yield</span>
              <span className="text-xl font-bold font-mono text-slate-100 block mt-0.5">{(kpis.average3YrReturn * 100).toFixed(2)}%</span>
            </div>
          </div>
        </section>

        {/* Dynamic Content Panel rendering current active tab */}
        <section className="flex-1 flex flex-col min-h-0">
          
          {/* TAB 1: FUND SCORECARD DATATABLE */}
          {activeTab === 'scorecard' && (
            <div className="bg-slate-900/30 rounded-xl border border-slate-800/80 p-6 flex flex-col gap-6">
              
              {/* Category selector & search filters */}
              <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
                <div className="flex flex-wrap gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-850">
                  {['All', 'Equity Large Cap', 'Equity Mid Cap', 'Equity Small Cap', 'Debt & Hybrid'].map(cat => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat as any)}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        selectedCategory === cat
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                          : 'text-slate-400 hover:text-slate-200 border border-transparent'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                <div className="relative w-full md:w-64">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <Search className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    placeholder="Search schemes..."
                    className="w-full pl-9 pr-4 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-medium text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              {/* Scorecard Table Grid */}
              <div className="overflow-x-auto rounded-lg border border-slate-850 bg-slate-950/65 shadow-inner">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-900/80 border-b border-slate-850 text-[10px] font-semibold text-slate-400 uppercase font-mono tracking-wider select-none">
                      <th className="py-4 px-4 text-center">Rank</th>
                      <th className="py-4 px-5 cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('name')}>Scheme Name</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('category')}>Category</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('cagr3Yr')}>3Yr CAGR</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('sharpeRatio')}>Sharpe</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('sortinoRatio')}>Sortino</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('alpha')}>Alpha (Ann)</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('beta')}>Beta</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('maxDrawdown')}>Max DD</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('expenseRatio')}>Expense</th>
                      <th className="py-4 px-4 text-center cursor-pointer hover:bg-slate-800/40" onClick={() => handleSort('compositeScore')}>Points</th>
                      <th className="py-4 px-4 text-center">Charts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-900 text-xs text-slate-300 font-mono">
                    {filteredMetrics.map((fund, idx) => {
                      const isSelected = selectedFundId === fund.id;
                      return (
                        <tr
                          key={fund.id}
                          onClick={() => setSelectedFundId(fund.id)}
                          className={`cursor-pointer transition group hover:bg-slate-900/60 ${
                            isSelected ? 'bg-emerald-500/[0.04] hover:bg-emerald-500/[0.06] border-l-2 border-l-emerald-500' : ''
                          }`}
                        >
                          <td className="py-3 px-4 text-center font-bold text-slate-200">
                            {fund.finalRank}
                          </td>
                          <td className="py-3 px-5 font-sans font-medium text-slate-100 group-hover:text-emerald-400 transition-colors">
                            {fund.name}
                          </td>
                          <td className="py-3 px-4 text-center font-sans">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                              fund.category === 'Equity Large Cap' ? 'bg-cyan-500/5 text-cyan-400 border-cyan-500/10' :
                              fund.category === 'Equity Mid Cap' ? 'bg-violet-500/5 text-violet-400 border-violet-500/10' :
                              fund.category === 'Equity Small Cap' ? 'bg-amber-500/5 text-amber-400 border-amber-500/10' :
                              'bg-slate-500/5 text-slate-400 border-slate-500/10'
                            }`}>
                              {fund.category}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            {(fund.cagr3Yr * 100).toFixed(2)}%
                          </td>
                          <td className="py-3 px-4 text-center text-cyan-400 font-semibold">
                            {fund.sharpeRatio.toFixed(3)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            {fund.sortinoRatio.toFixed(3)}
                          </td>
                          <td className="py-3 px-4 text-center text-emerald-400">
                            {(fund.alpha * 100).toFixed(2)}%
                          </td>
                          <td className="py-3 px-4 text-center">
                            {fund.beta.toFixed(3)}
                          </td>
                          <td className="py-3 px-4 text-center text-rose-400">
                            {(fund.maxDrawdown * 100).toFixed(2)}%
                          </td>
                          <td className="py-3 px-4 text-center text-slate-400">
                            {(fund.expenseRatio * 100).toFixed(2)}%
                          </td>
                          <td className="py-3 px-4 text-center font-bold text-slate-100">
                            {fund.compositeScore.toFixed(1)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedFundId(fund.id);
                                setActiveTab('explorer');
                              }}
                              className="px-2 py-1 bg-slate-900 hover:bg-slate-800 rounded border border-slate-800 text-[10px] text-slate-400 hover:text-emerald-400 transition"
                            >
                              Explore
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="text-[10px] text-slate-500 font-sans italic">
                * Pro-Tip: Click on any row to highlight the fund, then switch to the "Analytical Engine" or "Benchmark Chart" tabs to visualize its characteristics instantly.
              </p>
            </div>
          )}

          {/* TAB 2: BENCHMARK COMPARISON CHART */}
          {activeTab === 'benchmark' && (
            <div className="bg-slate-900/30 rounded-xl border border-slate-800/80 p-6">
              <BenchmarkChart
                metrics={metrics}
                indices={indices}
                dates={dates}
                fundsRaw={fundsRaw}
              />
            </div>
          )}

          {/* TAB 3: ADVANCED INTERACTIVE ANALYTICS ENGINE */}
          {activeTab === 'explorer' && (
            <div className="flex flex-col gap-6">
              {/* Fund Selector Banner */}
              <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <span className="text-[10px] uppercase font-mono tracking-wider text-emerald-400 font-semibold">Active Selected Scheme:</span>
                  <h3 className="text-lg font-bold text-slate-100 mt-1">{selectedFundMetrics.name}</h3>
                  <p className="text-xs text-slate-400 font-sans mt-0.5">
                    Category: <span className="font-semibold">{selectedFundMetrics.category}</span>  |  Expense Ratio: <span className="font-semibold font-mono text-[11px]">{(selectedFundMetrics.expenseRatio * 100).toFixed(2)}%</span>  |  Current Scorecard Rank: <span className="font-bold text-emerald-400 font-mono text-[11px]">#{selectedFundMetrics.finalRank}</span>
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-sans hidden md:inline">Switch fund:</span>
                  <select
                    value={selectedFundId}
                    onChange={e => setSelectedFundId(e.target.value)}
                    className="bg-slate-950 border border-slate-800 text-slate-200 text-xs px-3 py-2 rounded-lg font-mono focus:outline-none focus:border-emerald-500/50"
                  >
                    {metrics.map(m => (
                      <option key={m.id} value={m.id}>
                        #{m.finalRank} - {m.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Analytics Sub-Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <ReturnsDistributionChart
                  fundName={selectedFundMetrics.name}
                  historicalNAVs={selectedFundRaw.historicalNAVs}
                />
                <RegressionScatterChart
                  metrics={selectedFundMetrics}
                  historicalNAVs={selectedFundRaw.historicalNAVs}
                  indices={indices}
                  dates={dates}
                />
                <div className="xl:col-span-2">
                  <DrawdownChart
                    metrics={selectedFundMetrics}
                    historicalNAVs={selectedFundRaw.historicalNAVs}
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: DELIVERABLE DOWNLOAD CENTER */}
          {activeTab === 'downloads' && (
            <div className="bg-slate-900/30 rounded-xl border border-slate-800/80 p-6 flex flex-col gap-6">
              <div>
                <h3 className="text-lg font-medium text-slate-100">Deliverable Download Center</h3>
                <p className="text-sm text-slate-400 mt-1">
                  Download the complete offline deliverables requested by your project specifications.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* DELIVERABLE 1: JUPYTER NOTEBOOK */}
                <div className="bg-slate-950/60 border border-slate-800 p-6 rounded-xl hover:border-emerald-500/40 transition duration-200 flex flex-col justify-between group">
                  <div className="flex flex-col gap-3">
                    <div className="h-10 w-10 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400 font-mono text-sm font-bold">
                      PY
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors">Performance_Analytics.ipynb</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        A full Jupyter Notebook written in standard JSON ipynb format containing the entire Pandas and Scipy calculations and plotting suite.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownloadFile('Performance_Analytics.ipynb', generateJupyterNotebook(), 'application/json')}
                    className="mt-6 w-full flex items-center justify-center gap-2 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold hover:text-emerald-400 transition"
                  >
                    <Download className="w-4 h-4" />
                    Download Notebook
                  </button>
                </div>

                {/* DELIVERABLE 2: SCORECARD CSV */}
                <div className="bg-slate-950/60 border border-slate-800 p-6 rounded-xl hover:border-emerald-500/40 transition duration-200 flex flex-col justify-between group">
                  <div className="flex flex-col gap-3">
                    <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                      <FileSpreadsheet className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors">fund_scorecard.csv</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        A clean spreadsheet containing all 40 schemes, their raw metrics, component percentile weights, and composite ranking scores.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownloadFile('fund_scorecard.csv', generateScorecardCSV(metrics), 'text/csv')}
                    className="mt-6 w-full flex items-center justify-center gap-2 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold hover:text-emerald-400 transition"
                  >
                    <Download className="w-4 h-4" />
                    Download Scorecard CSV
                  </button>
                </div>

                {/* DELIVERABLE 3: ALPHA BETA CSV */}
                <div className="bg-slate-950/60 border border-slate-800 p-6 rounded-xl hover:border-emerald-500/40 transition duration-200 flex flex-col justify-between group">
                  <div className="flex flex-col gap-3">
                    <div className="h-10 w-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors">alpha_beta.csv</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        Specifically exports the Capm beta slope regressions and annualized tracking errors against Nifty 100/50 indexes for local seeding.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownloadFile('alpha_beta.csv', generateAlphaBetaCSV(metrics), 'text/csv')}
                    className="mt-6 w-full flex items-center justify-center gap-2 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold hover:text-emerald-400 transition"
                  >
                    <Download className="w-4 h-4" />
                    Download Alpha/Beta CSV
                  </button>
                </div>

                {/* DELIVERABLE 4: PLOT PNG */}
                <div className="bg-slate-950/60 border border-slate-800 p-6 rounded-xl hover:border-emerald-500/40 transition duration-200 flex flex-col justify-between group">
                  <div className="flex flex-col gap-3">
                    <div className="h-10 w-10 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                      <LineChart className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors">benchmark_chart.png</h4>
                      <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        Draws the 3-year performance lines onto an offscreen canvas to compile a pixel-precise, high-resolution PNG image file instantly.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleDownloadBenchmarkPNG}
                    className="mt-6 w-full flex items-center justify-center gap-2 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold hover:text-emerald-400 transition"
                  >
                    <Download className="w-4 h-4" />
                    Compile & Download PNG
                  </button>
                </div>
              </div>

              {copiedStatus && (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-400 text-xs font-medium font-sans">
                  <CheckCircle className="w-5 h-5" />
                  Successfully generated and downloaded: <span className="font-mono text-slate-200 bg-slate-900 px-1.5 py-0.5 rounded">{copiedStatus}</span>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: LOCAL WORKSPACE & GIT SYNC GUIDE */}
          {activeTab === 'guide' && (
            <div className="bg-slate-900/30 rounded-xl border border-slate-800/80 p-6">
              <DeveloperGuide />
            </div>
          )}

        </section>
      </main>

      {/* Footer Branding and Copyright details */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <TrendingUp className="w-4 h-4" />
            <span>Mutual Fund Analytics Dashboard  |  Quantum Engine v1.0.4</span>
          </div>
          <div className="text-slate-600 text-[10px] font-mono leading-relaxed">
            Workspace: <span className="text-emerald-500">C:\Users\Vasu\OneDrive\Desktop\MUTUALFUNDDATAANALYTICS</span>
            <span className="block mt-0.5">Repo: https://github.com/kvasuaditya-star/MUTUALFUNDSDATAANALYTICS</span>
          </div>
        </div>
      </footer>

    </div>
  );
}
