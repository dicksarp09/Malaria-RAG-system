'use client';

import React, { useState, FormEvent, useRef, useEffect } from 'react';
import { Send, Globe, Filter, ChevronUp } from 'lucide-react';

interface InputBarProps {
  onSubmit: (query: string, country: string | undefined, topK: number) => void;
  loading: boolean;
}

export default function InputBar({ onSubmit, loading }: InputBarProps) {
  const [query, setQuery] = useState('');
  const [country, setCountry] = useState<string | undefined>('All');
  const [topK, setTopK] = useState(10);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query, country === 'All' ? undefined : country, topK);
      setQuery('');
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [query]);

  return (
    <div className="fixed bottom-0 left-64 right-0 pb-8 pt-4 bg-gradient-to-t from-white via-white/95 to-transparent z-10 transition-all duration-300">
      <div className="max-w-3xl mx-auto px-6">
        <form
          onSubmit={handleSubmit}
          className="relative bg-white border border-slate-200 rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 overflow-hidden"
        >
          <div className="p-4 flex flex-col gap-3">
            <textarea
              ref={textareaRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Query malaria research evidence..."
              disabled={loading}
              rows={1}
              className="w-full px-2 py-1 bg-transparent border-none focus:ring-0 resize-none text-[13px] text-slate-800 placeholder:text-slate-400 disabled:cursor-not-allowed min-h-[40px] max-h-[120px] scrollbar-hide"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />

            <div className="flex items-center justify-between pt-2 border-t border-slate-50">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 rounded-lg border border-slate-100 transition-colors hover:border-slate-200">
                  <Globe className="w-3 h-3 text-slate-400" />
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    disabled={loading}
                    className="bg-transparent text-[10px] font-bold text-slate-600 uppercase tracking-tighter focus:ring-0 border-none p-0 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <option value="All">Scope: Global</option>
                    <option value="Ghana">Scope: Ghana</option>
                    <option value="Nigeria">Scope: Nigeria</option>
                  </select>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 rounded-lg border border-slate-100 transition-colors hover:border-slate-200">
                  <Filter className="w-3 h-3 text-slate-400" />
                  <select
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value))}
                    disabled={loading}
                    className="bg-transparent text-[10px] font-bold text-slate-600 uppercase tracking-tighter focus:ring-0 border-none p-0 cursor-pointer disabled:cursor-not-allowed"
                  >
                    <option value={5}>Top-K: 5</option>
                    <option value={10}>Top-K: 10</option>
                    <option value={15}>Top-K: 15</option>
                    <option value={20}>Top-K: 20</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !query.trim()}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl text-[11px] font-bold uppercase tracking-wider transition-all duration-300
                  ${loading || !query.trim()
                    ? 'bg-slate-100 text-slate-300 cursor-not-allowed'
                    : 'bg-slate-900 text-white hover:bg-slate-800 hover:-translate-y-0.5 shadow-md hover:shadow-lg active:translate-y-0'}
                `}
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-slate-400/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
                <span>Analyze</span>
              </button>
            </div>
          </div>
        </form>
        <p className="mt-3 text-[10px] text-center text-slate-400 font-medium uppercase tracking-widest opacity-60">
          Clinical Retrieval System • Ghana & Nigeria Literature Corpus
        </p>
      </div>
    </div>
  );
}
