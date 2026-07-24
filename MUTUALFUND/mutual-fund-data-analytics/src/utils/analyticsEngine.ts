/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { FundRawData, FundMetrics, DailyPoint, IndexPoint, FundCategory } from '../types';

// Helper: Calculate average of an array
function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((sum, v) => sum + v, 0) / arr.length;
}

// Helper: Calculate sample standard deviation
function std(arr: number[], avg?: number): number {
  if (arr.length <= 1) return 0;
  const m = avg !== undefined ? avg : mean(arr);
  const variance = arr.reduce((sum, v) => sum + Math.pow(v - m, 2), 0) / (arr.length - 1);
  return Math.sqrt(variance);
}

// Helper: Find closest data point by date YYYY-MM-DD
export function findClosestPoint(points: DailyPoint[], targetDateStr: string): DailyPoint {
  const targetTime = new Date(targetDateStr).getTime();
  let closestPoint = points[0];
  let minDiff = Math.abs(new Date(closestPoint.date).getTime() - targetTime);

  for (let i = 1; i < points.length; i++) {
    const diff = Math.abs(new Date(points[i].date).getTime() - targetTime);
    if (diff < minDiff) {
      minDiff = diff;
      closestPoint = points[i];
    }
  }
  return closestPoint;
}

export function findClosestIndexPoint(points: IndexPoint[], targetDateStr: string): IndexPoint {
  const targetTime = new Date(targetDateStr).getTime();
  let closestPoint = points[0];
  let minDiff = Math.abs(new Date(closestPoint.date).getTime() - targetTime);

  for (let i = 1; i < points.length; i++) {
    const diff = Math.abs(new Date(points[i].date).getTime() - targetTime);
    if (diff < minDiff) {
      minDiff = diff;
      closestPoint = points[i];
    }
  }
  return closestPoint;
}

// Compute metrics for all 40 funds
export function computeAllMetrics(
  funds: FundRawData[],
  indices: IndexPoint[],
  dates: string[]
): FundMetrics[] {
  const N = dates.length;
  const endDateStr = dates[N - 1];

  // Benchmark index returns (entire history, day-to-day)
  const indexReturnsNifty100: number[] = [];
  const indexReturnsNifty50: number[] = [];
  for (let i = 1; i < N; i++) {
    indexReturnsNifty100.push(indices[i].nifty100 / indices[i - 1].nifty100 - 1);
    indexReturnsNifty50.push(indices[i].nifty50 / indices[i - 1].nifty50 - 1);
  }

  // 3-year cutoff calculations
  // End date is endDateStr. 3 years prior target date:
  const endD = new Date(endDateStr);
  const target3YrDateStr = new Date(endD.getFullYear() - 3, endD.getMonth(), endD.getDate())
    .toISOString()
    .split('T')[0];
  
  // Find index of the trading day closest to 3yr prior
  const index3YrPrior = dates.findIndex(d => d >= target3YrDateStr);
  const start3YrIndex = index3YrPrior !== -1 ? index3YrPrior : Math.max(0, N - 252 * 3);

  const calculatedMetricsList: Omit<FundMetrics, 'rank3YrReturn' | 'rankSharpe' | 'rankAlpha' | 'rankExpenseInverse' | 'rankMaxDDInverse' | 'score3YrReturn' | 'scoreSharpe' | 'scoreAlpha' | 'scoreExpense' | 'scoreMaxDD' | 'compositeScore' | 'finalRank'>[] = [];

  for (const fund of funds) {
    const navs = fund.historicalNAVs;
    
    // 1. Compute Daily Returns over entire history
    const fundReturns: number[] = [];
    for (let i = 1; i < N; i++) {
      fundReturns.push(navs[i].nav / navs[i - 1].nav - 1);
    }

    // 2. Compute CAGRs (1yr, 3yr, 5yr)
    // 1 Year prior lookup
    const target1YrDateStr = new Date(endD.getFullYear() - 1, endD.getMonth(), endD.getDate())
      .toISOString()
      .split('T')[0];
    const navEnd = navs[N - 1].nav;
    const p1Yr = findClosestPoint(navs, target1YrDateStr);
    const nav1YrStart = p1Yr.nav;
    const diffYears1Yr = (new Date(endDateStr).getTime() - new Date(p1Yr.date).getTime()) / (365.25 * 24 * 3600 * 1000);
    const cagr1Yr = Math.pow(navEnd / nav1YrStart, 1 / (diffYears1Yr || 1)) - 1;

    // 3 Year prior lookup
    const p3Yr = findClosestPoint(navs, target3YrDateStr);
    const nav3YrStart = p3Yr.nav;
    const diffYears3Yr = (new Date(endDateStr).getTime() - new Date(p3Yr.date).getTime()) / (365.25 * 24 * 3600 * 1000);
    const cagr3Yr = Math.pow(navEnd / nav3YrStart, 1 / (diffYears3Yr || 3)) - 1;

    // 5 Year prior lookup (or since inception if < 5yr, but here it's exactly 5 years since we start on 2021-06-30)
    const nav5YrStart = navs[0].nav;
    const diffYears5Yr = (new Date(endDateStr).getTime() - new Date(navs[0].date).getTime()) / (365.25 * 24 * 3600 * 1000);
    const cagr5Yr = Math.pow(navEnd / nav5YrStart, 1 / (diffYears5Yr || 5)) - 1;

    // 3. Volatility and Ratios
    const dailyVol = std(fundReturns);
    const volatility = dailyVol * Math.sqrt(252); // Annualized volatility
    
    // Sharpe Ratio: Use Rf = 6.5% (0.065), and CAGR 3Yr as return proxy (or CAGR 5Yr)
    // We use CAGR 3Yr as Rp
    const Rf = 0.065;
    const sharpeRatio = (cagr3Yr - Rf) / (volatility || 0.0001);

    // Sortino Ratio: Downside Deviation (negative return days only)
    // Specifically, days where daily return is negative
    const negativeReturns = fundReturns.filter(r => r < 0);
    // Downside daily deviation = sqrt( sum(r^2) / N_negative )
    const downsideSqSum = negativeReturns.reduce((sum, r) => sum + r * r, 0);
    const downsideDailyVol = Math.sqrt(downsideSqSum / (fundReturns.length - 1)); // scaled by full sample size minus 1, or negative count? Standard formula uses entire series count N in denominator: sqrt(sum(min(0, r)^2) / N)
    const downsideVolatility = downsideDailyVol * Math.sqrt(252);
    const sortinoRatio = (cagr3Yr - Rf) / (downsideVolatility || 0.0001);

    // 4. Alpha & Beta: OLS Regression against Nifty 100 daily returns
    // fund_return = alpha_daily + beta * market_return
    const meanX = mean(indexReturnsNifty100);
    const meanY = mean(fundReturns);
    
    let num = 0;
    let den = 0;
    for (let i = 0; i < fundReturns.length; i++) {
      const dx = indexReturnsNifty100[i] - meanX;
      const dy = fundReturns[i] - meanY;
      num += dx * dy;
      den += dx * dx;
    }
    
    const beta = den !== 0 ? num / den : 1.0;
    const alphaDaily = meanY - beta * meanX;
    const alpha = alphaDaily * 252; // Annualized Alpha

    // Compute R-squared
    let ssRes = 0;
    let ssTot = 0;
    for (let i = 0; i < fundReturns.length; i++) {
      const predY = alphaDaily + beta * indexReturnsNifty100[i];
      ssRes += Math.pow(fundReturns[i] - predY, 2);
      ssTot += Math.pow(fundReturns[i] - meanY, 2);
    }
    const rSquared = ssTot !== 0 ? 1 - ssRes / ssTot : 1.0;

    // 5. Maximum Drawdown & Date Ranges
    let maxDrawdown = 0;
    let runningMax = navs[0].nav;
    let peakDate = navs[0].date;
    
    let worstPeakDate = navs[0].date;
    let worstTroughDate = navs[0].date;
    let worstRecoveryDate = navs[0].date;
    
    let tempPeakNAV = navs[0].nav;
    let tempPeakDate = navs[0].date;
    let tempPeakIdx = 0;

    for (let i = 0; i < navs.length; i++) {
      const currentNAV = navs[i].nav;
      if (currentNAV > runningMax) {
        runningMax = currentNAV;
        peakDate = navs[i].date;
        
        tempPeakNAV = currentNAV;
        tempPeakDate = navs[i].date;
        tempPeakIdx = i;
      }
      
      const drawdown = (currentNAV / runningMax) - 1;
      if (drawdown < maxDrawdown) {
        maxDrawdown = drawdown;
        worstPeakDate = peakDate;
        worstTroughDate = navs[i].date;
        
        // Find recovery date from trough index onwards
        let recoveryFound = false;
        for (let j = i + 1; j < navs.length; j++) {
          if (navs[j].nav >= tempPeakNAV) {
            worstRecoveryDate = navs[j].date;
            recoveryFound = true;
            break;
          }
        }
        if (!recoveryFound) {
          worstRecoveryDate = 'Ongoing (Not Recovered)';
        }
      }
    }

    // 6. Tracking Error over the 3-Year period
    // trackingError = std(fund_return - benchmark_return) * sqrt(252)
    const activeReturnsN100_3Yr: number[] = [];
    const activeReturnsN50_3Yr: number[] = [];
    for (let i = start3YrIndex + 1; i < N; i++) {
      const rFund = navs[i].nav / navs[i - 1].nav - 1;
      const r100 = indices[i].nifty100 / indices[i - 1].nifty100 - 1;
      const r50 = indices[i].nifty50 / indices[i - 1].nifty50 - 1;
      activeReturnsN100_3Yr.push(rFund - r100);
      activeReturnsN50_3Yr.push(rFund - r50);
    }
    
    const trackingErrorNifty100 = std(activeReturnsN100_3Yr) * Math.sqrt(252);
    const trackingErrorNifty50 = std(activeReturnsN50_3Yr) * Math.sqrt(252);

    calculatedMetricsList.push({
      id: fund.id,
      name: fund.name,
      category: fund.category,
      expenseRatio: fund.expenseRatio,
      cagr1Yr,
      cagr3Yr,
      cagr5Yr,
      volatility,
      sharpeRatio,
      sortinoRatio,
      alpha,
      beta,
      rSquared,
      maxDrawdown,
      drawdownStartDate: worstPeakDate,
      drawdownTroughDate: worstTroughDate,
      drawdownEndDate: worstRecoveryDate,
      trackingErrorNifty100,
      trackingErrorNifty50,
    });
  }

  // 7. Rankings and Composite Scores (0-100 scale)
  // Dimensions for composite scoring:
  // - 3Yr Return (CAGR 3Yr) - higher is better (weight 30%)
  // - Sharpe Ratio - higher is better (weight 25%)
  // - Alpha - higher is better (weight 20%)
  // - Expense Ratio - lower is better (weight 15%)
  // - Max Drawdown - less negative is better (weight 10%)

  const sortedBy3Yr = [...calculatedMetricsList].sort((a, b) => a.cagr3Yr - b.cagr3Yr);
  const sortedBySharpe = [...calculatedMetricsList].sort((a, b) => a.sharpeRatio - b.sharpeRatio);
  const sortedByAlpha = [...calculatedMetricsList].sort((a, b) => a.alpha - b.alpha);
  const sortedByExpenseInverse = [...calculatedMetricsList].sort((a, b) => b.expenseRatio - a.expenseRatio); // Highest expense ratio at index 0 (worst rank = 1), lowest expense ratio at index 39 (best rank = 40)
  const sortedByMaxDDInverse = [...calculatedMetricsList].sort((a, b) => a.maxDrawdown - b.maxDrawdown); // Deepest negative drawdown at index 0 (worst rank = 1), smallest negative drawdown at index 39 (best rank = 40)

  // Mapping to retrieve ranks (1 to 40)
  const getRank = (sortedList: any[], id: string): number => {
    return sortedList.findIndex(item => item.id === id) + 1;
  };

  const finalMetricsList: FundMetrics[] = calculatedMetricsList.map(item => {
    const r3Yr = getRank(sortedBy3Yr, item.id);
    const rSharpe = getRank(sortedBySharpe, item.id);
    const rAlpha = getRank(sortedByAlpha, item.id);
    const rExpense = getRank(sortedByExpenseInverse, item.id);
    const rMaxDD = getRank(sortedByMaxDDInverse, item.id);

    // Convert ranks (1-40) to percentile scores (0-100)
    // Score = (Rank - 1) / (40 - 1) * 100
    const score3YrReturn = ((r3Yr - 1) / 39) * 100;
    const scoreSharpe = ((rSharpe - 1) / 39) * 100;
    const scoreAlpha = ((rAlpha - 1) / 39) * 100;
    const scoreExpense = ((rExpense - 1) / 39) * 100;
    const scoreMaxDD = ((rMaxDD - 1) / 39) * 100;

    // Composite Score = 30% * 3YrReturn + 25% * Sharpe + 20% * Alpha + 15% * Expense + 10% * MaxDD
    const compositeScore =
      0.30 * score3YrReturn +
      0.25 * scoreSharpe +
      0.20 * scoreAlpha +
      0.15 * scoreExpense +
      0.10 * scoreMaxDD;

    return {
      ...item,
      rank3YrReturn: r3Yr,
      rankSharpe: rSharpe,
      rankAlpha: rAlpha,
      rankExpenseInverse: rExpense,
      rankMaxDDInverse: rMaxDD,
      score3YrReturn,
      scoreSharpe,
      scoreAlpha,
      scoreExpense,
      scoreMaxDD,
      compositeScore,
      finalRank: 0, // Will set below after sorting all funds by compositeScore
    } as FundMetrics;
  });

  // Sort overall by composite score (descending) and set finalRank (1 = highest score, 40 = lowest score)
  const sortedByComposite = [...finalMetricsList].sort((a, b) => b.compositeScore - a.compositeScore);
  sortedByComposite.forEach((fund, index) => {
    fund.finalRank = index + 1;
  });

  // Map back to the original order of funds or keep the ranked list
  return sortedByComposite;
}
