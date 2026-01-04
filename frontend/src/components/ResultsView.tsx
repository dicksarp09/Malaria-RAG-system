'use client';

import React from 'react';
import { QueryResult } from '../types';
import CitationCard from './CitationCard';
import Disclaimer from './Disclaimer';

interface ResultsViewProps {
  result: QueryResult;
}

export default function ResultsView({ result }: ResultsViewProps) {
  const isRefusal = !result.hasSufficientEvidence || result.answer.toUpperCase().includes('INSUFFICIENT EVIDENCE');

  return (
    <div className="w-full animate-fadeIn mb-12">
      <div className="mb-6 opacity-60">
        <div className="flex items-center gap-3 text-xs mono text-slate-500 mb-2 uppercase tracking-widest font-bold">
          <span className="bg-slate-200 px-2 py-0.5 rounded">{result.metadata.country}</span>
          <span>QUERY_ID: {result.timestamp.split('T')[1].substring(0, 8)}</span>
        </div>
        <h3 className="text-xl font-medium text-slate-800 leading-tight">
          {result.metadata.query}
        </h3>
      </div>

      <div className="space-y-8">
        <section>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Analysis</span>
          </div>
          {isRefusal ? (
            <div className="bg-[#FEF9E7] border border-[#F1C40F]/50 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3 text-[#9A7D0A]">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="font-bold uppercase tracking-wide text-xs">Insufficient Evidence</span>
              </div>
              <p className="text-slate-800 text-lg font-medium leading-relaxed">
                {result.answer}
              </p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
              <p className="text-slate-800 text-lg leading-relaxed font-medium">
                {result.answer}
              </p>
            </div>
          )}
        </section>

        <section className="bg-slate-50 border border-slate-200 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Supporting Citations</span>
              <span className="bg-slate-200 text-slate-600 text-[10px] font-mono px-2 py-0.5 rounded-full">
                {result.citations.length} SOURCE{result.citations.length === 1 ? '' : 'S'}
              </span>
            </div>
            <div className="text-[10px] mono text-slate-400 font-bold uppercase">Strict Retrieval Mode</div>
          </div>

          <div className="space-y-4">
            {result.citations.map((cit) => (
              <CitationCard key={cit.id} citation={cit} />
            ))}
          </div>
        </section>

        <Disclaimer />
      </div>
    </div>
  );
}
