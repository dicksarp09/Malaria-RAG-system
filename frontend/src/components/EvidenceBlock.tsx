'use client';

import React from 'react';
import { ShieldAlert, BookOpen, Fingerprint, Activity, Quote } from 'lucide-react';
import { QueryResponse } from '../lib/api';

interface EvidenceBlockProps {
  query: string;
  response: QueryResponse;
}

export default function EvidenceBlock({ query, response }: EvidenceBlockProps) {
  const { answer, is_insufficient_evidence, retrieved_chunks, chunks_retrieved } = response;

  return (
    <div className="w-full space-y-8 animate-fade-in-up">
      {/* Primary Answer Block */}
      <div className={`
        relative overflow-hidden rounded-2xl border transition-all duration-500 shadow-sm
        ${is_insufficient_evidence
          ? 'bg-amber-50/40 border-amber-200/60 shadow-amber-900/5'
          : 'bg-white border-slate-200 shadow-slate-200/50'
        }
      `}>
        {is_insufficient_evidence && (
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-200/0 via-amber-400/40 to-amber-200/0"></div>
        )}

        <div className="p-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              {is_insufficient_evidence ? (
                <div className="flex items-center gap-2 px-3 py-1 bg-amber-100/80 rounded-full border border-amber-200">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
                  <span className="text-[10px] font-bold text-amber-800 uppercase tracking-widest">Insufficient Evidence</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 rounded-full border border-emerald-100">
                  <Activity className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-widest">Clinical Synthesis</span>
                </div>
              )}
            </div>
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-200"></div>
              <div className="w-1.5 h-1.5 rounded-full bg-slate-200"></div>
              <div className="w-1.5 h-1.5 rounded-full bg-slate-200"></div>
            </div>
          </div>

          <div className="prose prose-slate max-w-none">
            <div className="text-[15px] text-slate-800 leading-[1.7] font-normal whitespace-pre-wrap">
              {answer}
            </div>
          </div>
        </div>
      </div>

      {/* Evidence Panel */}
      <div className="space-y-4">
        <div className="flex items-center gap-3 px-2">
          <div className="bg-slate-900 p-1.5 rounded-lg">
            <BookOpen className="w-3.5 h-3.5 text-white" />
          </div>
          <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em]">Retrieved Evidence Panel</h3>
          <div className="flex-1 h-px bg-slate-100"></div>
          <div className="text-[10px] font-mono font-bold text-slate-400 bg-slate-50 px-2 py-1 rounded border border-slate-100">
            {chunks_retrieved} UNITS
          </div>
        </div>

        <div className="grid gap-4">
          {retrieved_chunks.map((chunk, idx) => (
            <div
              key={chunk.chunk_id}
              className="group relative bg-white border border-slate-200 rounded-xl p-5 transition-all duration-300 hover:border-slate-300 hover:shadow-md"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-900 rounded-lg shadow-sm">
                    <Quote className="w-3 h-3 text-slate-400" />
                    <span className="text-[10px] font-mono font-bold text-white uppercase tracking-tight">
                      {chunk.section}
                    </span>
                  </div>
                  {chunk.country && (
                    <div className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[10px] font-mono font-bold text-slate-600">
                      {chunk.country.toUpperCase()}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 rounded-lg border border-emerald-100">
                  <span className="text-[9px] font-mono font-black text-emerald-700">R-SCORE: {chunk.final_score.toFixed(4)}</span>
                </div>
              </div>

              <div className="pl-4 border-l-2 border-slate-100 group-hover:border-slate-300 transition-colors">
                <div className="font-mono text-[11px] text-slate-500 uppercase tracking-tighter mb-2 flex items-center gap-2">
                  <Fingerprint className="w-3 h-3 opacity-30" />
                  DOC_ID: {chunk.document_id.substring(0, 24)}...
                </div>

                <div className="flex flex-wrap gap-x-6 gap-y-2 mt-4 pt-4 border-t border-slate-50">
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Scale</span>
                    <span className="text-[10px] font-mono text-slate-600">CHARS_{chunk.char_count}</span>
                  </div>
                  <div className="flex flex-col border-l border-slate-100 pl-6">
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Semantic</span>
                    <span className="text-[10px] font-mono text-slate-600">{chunk.semantic_score.toFixed(4)}</span>
                  </div>
                  <div className="flex flex-col border-l border-slate-100 pl-6">
                    <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">BM25</span>
                    <span className="text-[10px] font-mono text-slate-600">{chunk.bm25_score.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
