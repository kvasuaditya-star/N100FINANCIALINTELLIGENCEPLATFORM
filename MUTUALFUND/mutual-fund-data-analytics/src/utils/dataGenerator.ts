/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { FundCategory, FundRawData, DailyPoint, IndexPoint } from '../types';

// Simple seedable random generator (LCG)
export function createRandom(seed: number) {
  let s = seed;
  return function() {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

// Box-Muller transform for normal distribution
export function boxMuller(randomFn: () => number): number {
  let u1 = randomFn();
  let u2 = randomFn();
  while (u1 <= 0.0000001) { // Avoid log(0)
    u1 = randomFn();
  }
  return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
}

const SCHEME_NAMES: { name: string; category: FundCategory; expenseRatio: number; baseNAV: number }[] = [
  // Equity Large Cap (10 schemes)
  { name: 'SBI Bluechip Fund', category: 'Equity Large Cap', expenseRatio: 0.0155, baseNAV: 65.40 },
  { name: 'HDFC Top 100 Fund', category: 'Equity Large Cap', expenseRatio: 0.0162, baseNAV: 98.20 },
  { name: 'ICICI Prudential Bluechip Fund', category: 'Equity Large Cap', expenseRatio: 0.0148, baseNAV: 78.50 },
  { name: 'Axis Bluechip Fund', category: 'Equity Large Cap', expenseRatio: 0.0170, baseNAV: 52.10 },
  { name: 'Mirae Asset Large Cap Fund', category: 'Equity Large Cap', expenseRatio: 0.0150, baseNAV: 88.60 },
  { name: 'Nippon India Large Cap Fund', category: 'Equity Large Cap', expenseRatio: 0.0165, baseNAV: 62.30 },
  { name: 'UTI Mastershare Unit Scheme', category: 'Equity Large Cap', expenseRatio: 0.0142, baseNAV: 145.20 },
  { name: 'Kotak Bluechip Fund', category: 'Equity Large Cap', expenseRatio: 0.0158, baseNAV: 45.80 },
  { name: 'Aditya Birla Frontline Equity Fund', category: 'Equity Large Cap', expenseRatio: 0.0175, baseNAV: 320.40 },
  { name: 'Canara Robeco Bluechip Equity Fund', category: 'Equity Large Cap', expenseRatio: 0.0135, baseNAV: 50.70 },

  // Equity Mid Cap (10 schemes)
  { name: 'HDFC Mid-Cap Opportunities Fund', category: 'Equity Mid Cap', expenseRatio: 0.0182, baseNAV: 110.50 },
  { name: 'Nippon India Growth Fund', category: 'Equity Mid Cap', expenseRatio: 0.0195, baseNAV: 2200.00 },
  { name: 'Kotak Emerging Equity Fund', category: 'Equity Mid Cap', expenseRatio: 0.0178, baseNAV: 85.30 },
  { name: 'Axis Midcap Fund', category: 'Equity Mid Cap', expenseRatio: 0.0185, baseNAV: 74.20 },
  { name: 'DSP Midcap Fund', category: 'Equity Mid Cap', expenseRatio: 0.0190, baseNAV: 102.60 },
  { name: 'SBI Magnum Midcap Fund', category: 'Equity Mid Cap', expenseRatio: 0.0180, baseNAV: 155.40 },
  { name: 'Mirae Asset Midcap Fund', category: 'Equity Mid Cap', expenseRatio: 0.0172, baseNAV: 35.60 },
  { name: 'Franklin India Primus Fund', category: 'Equity Mid Cap', expenseRatio: 0.0198, baseNAV: 1350.00 },
  { name: 'Tata Midcap Growth Fund', category: 'Equity Mid Cap', expenseRatio: 0.0188, baseNAV: 285.40 },
  { name: 'ICICI Prudential Midcap Fund', category: 'Equity Mid Cap', expenseRatio: 0.0168, baseNAV: 180.20 },

  // Equity Small Cap (10 schemes)
  { name: 'Nippon India Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0210, baseNAV: 115.80 },
  { name: 'SBI Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0198, baseNAV: 142.40 },
  { name: 'HDFC Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0205, baseNAV: 98.70 },
  { name: 'Axis Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0215, baseNAV: 76.50 },
  { name: 'Quant Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0245, baseNAV: 195.20 },
  { name: 'Kotak Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0202, baseNAV: 185.60 },
  { name: 'DSP Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0212, baseNAV: 130.40 },
  { name: 'ICICI Prudential Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0192, baseNAV: 68.30 },
  { name: 'Tata Small Cap Fund', category: 'Equity Small Cap', expenseRatio: 0.0220, baseNAV: 32.50 },
  { name: 'Franklin India Smaller Companies Fund', category: 'Equity Small Cap', expenseRatio: 0.0225, baseNAV: 110.10 },

  // Debt & Hybrid (10 schemes)
  { name: 'SBI Equity Hybrid Fund', category: 'Debt & Hybrid', expenseRatio: 0.0115, baseNAV: 220.50 },
  { name: 'ICICI Prudential Equity & Debt Fund', category: 'Debt & Hybrid', expenseRatio: 0.0125, baseNAV: 275.80 },
  { name: 'HDFC Hybrid Equity Fund', category: 'Debt & Hybrid', expenseRatio: 0.0118, baseNAV: 92.40 },
  { name: 'Kotak Equity Hybrid Fund', category: 'Debt & Hybrid', expenseRatio: 0.0122, baseNAV: 45.30 },
  { name: 'Canara Robeco Conservative Hybrid Fund', category: 'Debt & Hybrid', expenseRatio: 0.0095, baseNAV: 88.60 },
  { name: 'SBI Magnum Constant Maturity Fund', category: 'Debt & Hybrid', expenseRatio: 0.0055, baseNAV: 55.40 },
  { name: 'HDFC Corporate Bond Fund', category: 'Debt & Hybrid', expenseRatio: 0.0062, baseNAV: 28.50 },
  { name: 'ICICI Prudential Savings Fund', category: 'Debt & Hybrid', expenseRatio: 0.0058, baseNAV: 452.10 },
  { name: 'Nippon India Liquid Fund', category: 'Debt & Hybrid', expenseRatio: 0.0035, baseNAV: 3450.00 },
  { name: 'Axis Gilt Fund', category: 'Debt & Hybrid', expenseRatio: 0.0072, baseNAV: 85.30 },
];

export interface GeneratedDataset {
  dates: string[];
  indices: IndexPoint[];
  funds: FundRawData[];
}

export function generateDataset(): GeneratedDataset {
  const random = createRandom(42); // Seed for determinism
  
  // Date setup: 5 years, ending today (roughly 2026-06-29)
  const tradingDays: string[] = [];
  const curDate = new Date('2021-06-30');
  const endDate = new Date('2026-06-29');
  
  while (curDate <= endDate) {
    const day = curDate.getDay();
    if (day !== 0 && day !== 6) { // Exclude Saturday and Sunday
      tradingDays.push(curDate.toISOString().split('T')[0]);
    }
    curDate.setDate(curDate.getDate() + 1);
  }
  
  const N = tradingDays.length; // Number of trading days, approx 1303 days
  
  // Benchmark Indices Random Walk Parameters (annualized)
  // Nifty 100: Drift 14% p.a., Volatility 15% p.a.
  // Nifty 50: Drift 13.5% p.a., Volatility 14.5% p.a. (highly correlated with Nifty 100)
  const nifty100Drift = 0.14 / 252;
  const nifty100Vol = 0.15 / Math.sqrt(252);
  
  const nifty50Drift = 0.135 / 252;
  const nifty50Vol = 0.145 / Math.sqrt(252);
  
  const nifty100Prices: number[] = [15000]; // Base value
  const nifty50Prices: number[] = [15700]; // Base value
  
  // Accumulate index series
  const indices: IndexPoint[] = [
    { date: tradingDays[0], nifty50: nifty50Prices[0], nifty100: nifty100Prices[0] }
  ];
  
  const indexReturnsNifty100: number[] = [0];
  const indexReturnsNifty50: number[] = [0];
  
  for (let i = 1; i < N; i++) {
    const r100Normal = boxMuller(random);
    const r100 = nifty100Drift + nifty100Vol * r100Normal;
    const next100 = nifty100Prices[i - 1] * (1 + r100);
    nifty100Prices.push(next100);
    indexReturnsNifty100.push(r100);
    
    // Correlate Nifty 50 returns with Nifty 100 returns (correlation coeff ~0.96)
    const correlation = 0.96;
    const residualNormal = boxMuller(random);
    const r50Idiosyncratic = nifty50Vol * Math.sqrt(1 - correlation * correlation) * residualNormal;
    const r50 = correlation * (r100 * (nifty50Vol / nifty100Vol)) + r50Idiosyncratic;
    const next50 = nifty50Prices[i - 1] * (1 + r50);
    nifty50Prices.push(next50);
    indexReturnsNifty50.push(r50);
    
    indices.push({
      date: tradingDays[i],
      nifty50: Math.round(next50 * 100) / 100,
      nifty100: Math.round(next100 * 100) / 100
    });
  }
  
  // Generate Funds Daily NAV
  const funds: FundRawData[] = SCHEME_NAMES.map((scheme, index) => {
    const historicalNAVs: DailyPoint[] = [{ date: tradingDays[0], nav: scheme.baseNAV }];
    
    // Customize fund factors based on category
    let beta = 1.0;
    let categoryVol = 0.15; // annual
    let alphaAnnual = 0.0; // annual alpha outperformance
    
    switch (scheme.category) {
      case 'Equity Large Cap':
        beta = 0.9 + (index % 5) * 0.05; // 0.9 to 1.1
        categoryVol = 0.14 + (index % 3) * 0.01; // 14% to 16%
        alphaAnnual = -0.01 + (index % 4) * 0.01; // -1% to +2%
        break;
      case 'Equity Mid Cap':
        beta = 1.1 + (index % 5) * 0.05; // 1.1 to 1.3
        categoryVol = 0.18 + (index % 3) * 0.015; // 18% to 21%
        alphaAnnual = 0.0 + (index % 4) * 0.015; // 0% to +4.5%
        break;
      case 'Equity Small Cap':
        beta = 1.25 + (index % 5) * 0.06; // 1.25 to 1.49
        categoryVol = 0.22 + (index % 4) * 0.02; // 22% to 28%
        alphaAnnual = 0.01 + (index % 5) * 0.015; // 1% to +7%
        break;
      case 'Debt & Hybrid':
        if (index >= 35) { // Pure Debt (funds 36-40)
          beta = 0.05 + (index % 5) * 0.02; // 0.05 to 0.13
          categoryVol = 0.03 + (index % 3) * 0.01; // 3% to 5%
          alphaAnnual = 0.005 + (index % 3) * 0.005; // 0.5% to 1.5%
        } else { // Hybrid (funds 31-35)
          beta = 0.45 + (index % 5) * 0.04; // 0.45 to 0.61
          categoryVol = 0.08 + (index % 3) * 0.01; // 8% to 10%
          alphaAnnual = 0.01 + (index % 3) * 0.01; // 1% to 3%
        }
        break;
    }
    
    // Scale parameters to daily
    const alphaDaily = alphaAnnual / 252;
    const dailyIdiosyncraticVol = categoryVol * Math.sqrt(1 - 0.75) / Math.sqrt(252); // Assuming R-squared ~ 0.75
    
    let currentNAV = scheme.baseNAV;
    for (let i = 1; i < N; i++) {
      const marketReturn = indexReturnsNifty100[i];
      const idiosyncraticNormal = boxMuller(random);
      
      // Capital Asset Pricing Model (CAPM) daily return formulation
      // daily_return = beta * market_return + alpha_daily + error - expense_ratio/252
      const dailyExpense = scheme.expenseRatio / 252;
      const dailyReturn = beta * marketReturn + alphaDaily + dailyIdiosyncraticVol * idiosyncraticNormal - dailyExpense;
      
      currentNAV = currentNAV * (1 + dailyReturn);
      historicalNAVs.push({
        date: tradingDays[i],
        nav: Math.round(currentNAV * 10000) / 10000
      });
    }
    
    return {
      id: `fund_${index + 1}`,
      name: scheme.name,
      category: scheme.category,
      expenseRatio: scheme.expenseRatio,
      baseNAV: scheme.baseNAV,
      historicalNAVs
    };
  });
  
  return {
    dates: tradingDays,
    indices,
    funds
  };
}
