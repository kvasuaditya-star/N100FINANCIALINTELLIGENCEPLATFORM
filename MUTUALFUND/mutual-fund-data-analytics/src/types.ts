/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type FundCategory = 'Equity Large Cap' | 'Equity Mid Cap' | 'Equity Small Cap' | 'Debt & Hybrid';

export interface DailyPoint {
  date: string; // YYYY-MM-DD
  nav: number;
}

export interface IndexPoint {
  date: string;
  nifty50: number;
  nifty100: number;
}

export interface FundRawData {
  id: string;
  name: string;
  category: FundCategory;
  expenseRatio: number; // e.g. 0.012 for 1.2%
  baseNAV: number;
  historicalNAVs: DailyPoint[];
}

export interface FundMetrics {
  id: string;
  name: string;
  category: FundCategory;
  expenseRatio: number;
  
  // Returns
  cagr1Yr: number;
  cagr3Yr: number;
  cagr5Yr: number;
  
  // Volatility and Ratios
  volatility: number; // Annualized standard deviation of daily returns
  sharpeRatio: number;
  sortinoRatio: number;
  
  // Regression against Nifty 100
  alpha: number; // Annualized Alpha (intercept * 252)
  beta: number; // Beta (slope of regression against Nifty 100)
  rSquared: number;
  
  // Drawdown
  maxDrawdown: number; // Worst drawdown
  drawdownStartDate: string;
  drawdownTroughDate: string;
  drawdownEndDate: string; // date of recovery (or end of series if not recovered)
  
  // Tracking Error against Nifty 100
  trackingErrorNifty100: number;
  trackingErrorNifty50: number;
  
  // Scores & Rankings
  rank3YrReturn: number;
  rankSharpe: number;
  rankAlpha: number;
  rankExpenseInverse: number;
  rankMaxDDInverse: number;
  
  score3YrReturn: number;
  scoreSharpe: number;
  scoreAlpha: number;
  scoreExpense: number;
  scoreMaxDD: number;
  
  compositeScore: number; // 0-100 score
  finalRank: number; // Overall rank (1 to 40)
}
