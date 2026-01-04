'use client';

import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import QueryPanel from '../components/QueryPanel';
import ResultsView from '../components/ResultsView';
import { AppState, Country, QueryResult } from '../types';
import { runResearchQuery } from '../lib/queryService';

export default function HomePage() {
  const [state, setState] = useState<AppState & { history: QueryResult[] }>({
    isSearching: false,
    result: null,
    history: [],
  });

  const scrollRef = useRef<HTMLDivElement>(null);

  const handleRunQuery = async (query: string, country: Country, topK: number) => {
    setState(prev => ({ ...prev, isSearching: true }));
    try {
      const result = await runResearchQuery(query, country, topK);
      setState(prev => ({
        ...prev,
        isSearching: false,
        result,
        history: [result, ...prev.history],
      }));
    } catch (error) {
      console.error('Retrieval error:', error);
      setState(prev => ({ ...prev, isSearching: false }));
    }
  };

  const selectHistory = (res: QueryResult) => {
    setState(prev => ({ ...prev, result: res }));
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [state.result]);

  return (
    <div className="flex h-screen bg-[#F8F9FA] overflow-hidden">
      <Sidebar
        history={state.history}
        onSelectHistory={selectHistory}
        activeId={state.result?.timestamp}
      />

      <div className="flex-1 flex flex-col relative">
        <main
          ref={scrollRef}
          className="flex-1 overflow-y-auto pt-10 pb-48 custom-scrollbar"
        >
          <div className="max-w-4xl mx-auto px-6 w-full">
            {!state.result && !state.isSearching && (
              <div className="h-[60vh] flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 bg-white border border-slate-200 rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                  <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h2 className="text-lg font-bold text-slate-800 mb-1 uppercase tracking-tight">Research Analysis Interface</h2>
                <p className="text-sm text-slate-500 max-w-xs leading-relaxed">
                  Enter a research query below to perform granular evidence retrieval from the Malaria Research Corpus.
                </p>
                <div className="mt-8 grid grid-cols-1 gap-2 w-full max-w-sm">
                  {['Malaria prevention in Ghana', 'Artemisinin resistance in Nigeria', 'Rapid diagnostic testing protocols'].map(s => (
                    <button
                      key={s}
                      onClick={() => handleRunQuery(s, 'All', 5)}
                      className="text-[11px] text-left px-4 py-2 bg-white border border-slate-100 rounded-lg text-slate-500 hover:border-slate-300 transition-all font-medium uppercase tracking-tight"
                    >
                      Analyze: {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {state.isSearching && (
              <div className="animate-pulse space-y-12">
                <div className="space-y-4">
                  <div className="h-4 w-32 bg-slate-200 rounded"></div>
                  <div className="h-8 w-2/3 bg-slate-200 rounded"></div>
                </div>
                <div className="h-48 bg-slate-200 rounded-2xl"></div>
                <div className="h-96 bg-slate-200 rounded-2xl"></div>
              </div>
            )}

            {state.result && !state.isSearching && (
              <ResultsView result={state.result} />
            )}
          </div>
        </main>

        <QueryPanel onRun={handleRunQuery} isLoading={state.isSearching} />
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.4s ease-out forwards;
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #E2E8F0;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #CBD5E1;
        }
      `}</style>
    </div>
  );
}
