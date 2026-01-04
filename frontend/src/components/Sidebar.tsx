'use client';

import React from 'react';
import { QueryResult } from '../types';

interface SidebarProps {
  history: QueryResult[];
  onSelectHistory: (result: QueryResult) => void;
  activeId?: string;
}

export default function Sidebar({ history, onSelectHistory, activeId }: SidebarProps) {
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 text-slate-300 z-20">
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <div className="bg-teal-600 p-1 rounded">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
            </svg>
          </div>
          <h1 className="text-xs font-bold tracking-tight text-white uppercase">Evidence Portal</h1>
        </div>
        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-medium">Research Environment</p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 px-2">Analysis History</div>
        {history.length === 0 ? (
          <div className="px-2 py-4 text-xs text-slate-600 italic">No recent analyses.</div>
        ) : (
          history.map((item, idx) => (
            <button
              key={idx}
              onClick={() => onSelectHistory(item)}
              className={`w-full text-left px-3 py-2 rounded-md text-xs transition-colors truncate ${activeId === item.timestamp ? 'bg-slate-800 text-white' : 'hover:bg-slate-800/50'
                }`}
            >
              {item.metadata.query}
            </button>
          ))
        )}
      </div>

      <div className="p-4 bg-slate-950 border-t border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
          <span className="text-[10px] font-mono text-slate-400">CORPUS_SYNC: ACTIVE</span>
        </div>
        <div className="text-[10px] font-mono text-slate-500 uppercase tracking-tighter">
          v2.4.0-stable
        </div>
      </div>
    </div>
  );
}
