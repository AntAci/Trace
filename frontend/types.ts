
export type MintingStatus = 'idle' | 'minting' | 'minted';

export interface SourcePaper {
  id: string;
  title: string;
  authors: string;
  year: number;
  content: string; // Simulated content for the demo
  fileName?: string;
}

export interface HypothesisArtifact {
  id: number;
  timestamp: string;
  title: string; // Added title for the card header
  statement: string;
  summary: string;
  
  confidence: {
    overall: number;    // 0-100
    novelty: number;
    plausibility: number;
    testability: number;
  };
  
  evidence: Array<{
    paper: string;
    page: number; // Simulated page number
    quote: string;
    confidenceLevel: 'High' | 'Medium' | 'Low';
  }>;
  
  noveltyAssessment: {
    isNovel: boolean;
    reasoning: string;
  };
  
  proposedExperiment: {
    procedure: string[];
    expectedOutcome: string;
  };
  
  imageUrl?: string; // AI-generated illustration
  
  blockchain?: {
    network: "Neo N3";
    transactionHash: string;
    nftId: number;
    explorerUrl: string;
    blockNumber: number;
  };
  
  sourcePapers: SourcePaper[];
}

export enum AppState {
  UPLOAD = 'UPLOAD',
  ANALYZING = 'ANALYZING',
  GENERATED = 'GENERATED',
  MINT_SUCCESS = 'MINT_SUCCESS',
}
