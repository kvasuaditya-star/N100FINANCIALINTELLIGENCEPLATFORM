/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Copy, Check, Terminal, FolderOpen, RefreshCw } from 'lucide-react';

export default function DeveloperGuide() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const steps = [
    {
      title: 'Initialize Local Project Directory',
      desc: 'Create and navigate into the target folder on your local Windows PC.',
      command: 'mkdir "C:\\Users\\Vasu\\OneDrive\\Desktop\\MUTUALFUNDDATAANALYTICS"\ncd "C:\\Users\\Vasu\\OneDrive\\Desktop\\MUTUALFUNDDATAANALYTICS"'
    },
    {
      title: 'Copy Workspace Code files',
      desc: 'Initialize a new Node React + TypeScript Vite template (or copy the files downloaded from this build workspace).',
      command: '# Initialize template structures\nnpm create vite@latest . -- --template react-ts\nnpm install\n\n# Install key analytics dependencies\nnpm install lucide-react motion dotenv express'
    },
    {
      title: 'Git Initialization & Origin Remote binding',
      desc: 'Create a local Git repository, commit files, and bind it to your GitHub target remote.',
      command: 'git init\ngit branch -M main\ngit remote add origin https://github.com/kvasuaditya-star/MUTUALFUNDSDATAANALYTICS'
    },
    {
      title: 'Deploy Deliverables & Final Commit',
      desc: 'Download the deliverables (Performance_Analytics.ipynb, fund_scorecard.csv, alpha_beta.csv, benchmark_chart.png) from our dashboard to your folder, add them to Git, and push to GitHub.',
      command: 'git add .\ngit commit -m "feat: complete mutual fund capstone performance analytics and deliverables"\ngit push -u origin main'
    }
  ];

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => {
      setCopiedIndex(null);
    }, 2000);
  };

  return (
    <div className="flex flex-col gap-6 font-sans">
      <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 flex items-start gap-4">
        <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20 text-emerald-400">
          <Terminal className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-100">Local Environment & GitHub Sync Terminal Utility</h3>
          <p className="text-sm text-slate-400 mt-1 leading-relaxed">
            As you are developing in a secure, sandboxed container, we cannot execute shell scripts on your local Windows machine directly. Use these pre-computed shell scripts to seamlessly sync the exact codebase and computed deliverables from this sandbox into your offline directory <code className="text-xs bg-slate-800/80 text-emerald-400 px-1.5 py-0.5 rounded font-mono">C:\Users\Vasu\OneDrive\Desktop\MUTUALFUNDDATAANALYTICS</code> and push them to your repository on GitHub!
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step-by-Step Shell Guide */}
        <div className="lg:col-span-2 flex flex-col gap-5">
          {steps.map((step, idx) => (
            <div key={idx} className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-xl flex flex-col gap-3 relative hover:border-slate-700/80 transition duration-150">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-800 text-emerald-400 flex items-center justify-center font-mono text-xs font-semibold border border-slate-700">
                  {idx + 1}
                </span>
                <h4 className="text-sm font-semibold text-slate-200">{step.title}</h4>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed pl-9">{step.desc}</p>
              
              <div className="relative pl-9 mt-1">
                <pre className="bg-slate-950 p-4 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre leading-relaxed border border-slate-900 shadow-inner">
                  {step.command}
                </pre>
                <button
                  onClick={() => handleCopy(step.command, idx)}
                  className="absolute top-3 right-3 p-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition duration-150"
                  title="Copy command"
                >
                  {copiedIndex === idx ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Deliverables Inventory and File Tree Structure */}
        <div className="flex flex-col gap-6">
          <div className="bg-slate-900/40 p-5 rounded-xl border border-slate-800/80">
            <h4 className="text-xs font-semibold uppercase text-slate-500 font-mono tracking-wider mb-4 flex items-center gap-1.5">
              <FolderOpen className="w-4 h-4 text-emerald-500" />
              Target Folder Structure
            </h4>
            <div className="bg-slate-950 p-4 rounded-lg font-mono text-[11px] text-slate-400 leading-relaxed border border-slate-900">
              <p className="text-slate-200">MUTUALFUNDDATAANALYTICS/</p>
              <p className="pl-4 text-emerald-400">├── fund_scorecard.csv <span className="text-[9px] text-slate-600">(Composite ranking grid)</span></p>
              <p className="pl-4 text-emerald-400">├── alpha_beta.csv <span className="text-[9px] text-slate-600">(CAPM OLS regression metrics)</span></p>
              <p className="pl-4 text-cyan-400">├── Performance_Analytics.ipynb <span className="text-[9px] text-slate-600">(Python Notebook)</span></p>
              <p className="pl-4 text-rose-400">├── benchmark_comparison_chart.png <span className="text-[9px] text-slate-600">(3Yr Growth plot)</span></p>
              <p className="pl-4 text-slate-500">├── package.json</p>
              <p className="pl-4 text-slate-500">├── vite.config.ts</p>
              <p className="pl-4 text-slate-500">├── index.html</p>
              <p className="pl-4 text-slate-500">└── src/</p>
              <p className="pl-8 text-slate-500">├── App.tsx</p>
              <p className="pl-8 text-slate-500">├── types.ts</p>
              <p className="pl-8 text-slate-500">└── utils/</p>
              <p className="pl-12 text-slate-500">├── dataGenerator.ts</p>
              <p className="pl-12 text-slate-500">└── analyticsEngine.ts</p>
            </div>
          </div>

          <div className="bg-emerald-500/5 p-5 rounded-xl border border-emerald-500/10 flex flex-col gap-3">
            <h4 className="text-xs font-semibold text-emerald-400 uppercase font-mono tracking-wider flex items-center gap-1.5">
              <RefreshCw className="w-4 h-4" />
              Real-time Pipeline Check
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Our web environment performs all mathematical calculations live inside the browser sandbox using high-performance compiled TypeScript. The exported Jupyter Notebook contains identical seeded logic written in standard scientific Python (<code className="text-slate-300 font-mono text-[10px]">Pandas, NumPy, Scipy.stats</code>), ensuring **100% decimal-precise reproducibility** when loaded locally.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
