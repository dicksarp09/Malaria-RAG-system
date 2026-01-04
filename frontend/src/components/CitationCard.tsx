'use client';

import React, { useState } from 'react';
import { Citation } from '../types';

interface CitationCardProps {
  citation: Citation;
}

export default function CitationCard({ citation }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div
        className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200 cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="mono text-[10px] font-bold bg-slate-800 text-white px-2 py-0.5 rounded uppercase">
            ID: {citation.sourceId}
          </span>
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
            {citation.section}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-teal-600"
                style={{ width: `${citation.relevanceScore * 100}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              {(citation.relevanceScore * 100).toFixed(0)}% Match
            </span>
          </div>
          <svg
            className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <div className={`transition-all duration-300 ease-in-out ${isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'} overflow-hidden`}>
        <div className="p-4 text-sm leading-relaxed text-slate-800 bg-white italic border-l-4 border-slate-300 ml-4 my-2">
          "{citation.content}"
        </div>
      </div>

      {!isExpanded && (
        <div className="px-4 py-3 text-xs text-slate-500 truncate italic">
          "{citation.content.substring(0, 120)}..."
        </div>
      )}
    </div>
  );
}
