export type Country = 'Ghana' | 'Nigeria' | 'All';

export interface Citation {
  id: string;
  sourceId: string;
  section: 'Abstract' | 'Methods' | 'Results' | 'Discussion' | 'Conclusion' | 'Policy';
  content: string;
  relevanceScore: number;
}

export interface QueryResult {
  answer: string;
  citations: Citation[];
  hasSufficientEvidence: boolean;
  timestamp: string;
  metadata: {
    query: string;
    country: Country;
    topK: number;
  };
}

export interface AppState {
  isSearching: boolean;
  result: QueryResult | null;
}
