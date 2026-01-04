'use client';

import React, { useState } from 'react';
import { Country } from '../types';

interface QueryPanelProps {
  onRun: (query: string, country: Country, topK: number) => void;
  isLoading: boolean;
}

export default function QueryPanel({ onRun, isLoading }: QueryPanelProps) {
  const [query, setQuery] = useState('');
  const [country, setCountry] = useState<Country>('Ghana');
  const [topK, setTopK] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onRun(query, country, topK);
      setQuery('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="fixed bottom-0 right-0 left-64 bg-gradient-to-t from-[#F8F9FA] via-[#F8F9FA] to-transparent pt-12 pb-6 px-6 z-30">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative group">
          <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-4 transition-all focus-within:border-slate-400 focus-within:ring-1 focus-within:ring-slate-400/20">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Query malaria research evidence..."
              className="w-full bg-transparent border-none outline-none resize-none text-slate-800 text-sm h-12 py-1 placeholder-slate-400"
            />

            <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-50">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-2 py-1 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Scope</span>
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value as Country)}
                    className="bg-transparent border-none outline-none text-xs font-semibold text-slate-600"
                  >
                    <option value="Ghana">Ghana</option>
                    <option value="Nigeria">Nigeria</option>
                    <option value="All">All Regions</option>
                  </select>
                </div>

                <div className="flex items-center gap-2 px-2 py-1 bg-slate-50 rounded-lg border border-slate-100">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Top-K</span>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                    className="w-8 bg-transparent border-none outline-none text-xs font-semibold text-slate-600"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading || !query.trim()}
                className={`p-2 rounded-xl transition-all ${isLoading || !query.trim()
                    ? 'bg-slate-100 text-slate-300'
                    : 'bg-slate-800 text-white hover:bg-slate-900 shadow-md active:scale-95'
                  }`}
              >
                {isLoading ? (
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                )}
              </button>
            </div>
          </div>
          <p className="text-center mt-3 text-[10px] text-slate-400 font-medium">
            Clinical Retrieval System • Ghana & Nigeria Literature Corpus
          </p>
        </form>
      </div>
    </div>
  );
}
