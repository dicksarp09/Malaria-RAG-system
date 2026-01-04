'use client';

import React from 'react';

export default function Disclaimer() {
  return (
    <div className="mt-8 pt-6 border-t border-slate-200">
      <div className="bg-slate-100 rounded-md p-4 flex gap-3 items-start">
        <svg className="w-5 h-5 text-slate-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
            Clinical Guidance Notice
          </p>
          <p className="text-xs text-slate-600 leading-normal">
            This system provides evidence-based summaries generated from a specific research corpus. These results are intended for audit and informational purposes for clinicians and researchers. They do not constitute professional medical advice, diagnosis, or treatment recommendations.
          </p>
        </div>
      </div>
    </div>
  );
}
