import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, Sparkles } from 'lucide-react';
import { SourcePaper } from '../types';

interface PaperInputProps {
  onAnalyze: (papers: SourcePaper[]) => void;
  isLoading: boolean;
}

const SAMPLE_PAPERS: SourcePaper[] = [
  {
    id: 'p1',
    title: 'A Blockchain-Based Approach to Provenance and Reproducibility in Research Workflows',
    authors: 'Kevin Wittek et al. (2021)',
    year: 2021,
    content: 'This paper proposes a certification model using the Bloxberg blockchain to address the reproducibility crisis. It introduces Research Object Certification (ROC) and Chain Links (ROCL) to track the provenance of data, code, and experimental designs. A DeepLabCut animal study is used to demonstrate how blockchain can immutable timestamp research steps, ensuring data integrity without revealing content.',
    fileName: 'blockchain_provenance_2021.pdf'
  },
  {
    id: 'p2',
    title: 'Agentic AI for Scientific Discovery: A Survey of Progress, Challenges, and Future Directions',
    authors: 'Mourad Gridach et al. (2025)',
    year: 2025,
    content: 'A comprehensive survey of Agentic AI systems (autonomous & collaborative) in science. It discusses tools like Coscientist and ChemCrow that automate hypothesis generation and experimentation. The paper highlights critical challenges: hallucination, lack of reliability in literature reviews, and the need for ethical governance and human oversight in automated discovery pipelines.',
    fileName: 'agentic_ai_survey_2025.pdf'
  }
];

export const PaperInput: React.FC<PaperInputProps> = ({ onAnalyze, isLoading }) => {
  const [papers, setPapers] = useState<SourcePaper[]>([]);

  const handleLoadSample = () => {
    setPapers(SAMPLE_PAPERS);
  };

  const handleStartAnalysis = () => {
    if (papers.length === 2) {
      onAnalyze(papers);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-display font-bold text-white mb-3">
          Research Inputs
        </h2>
        <p className="text-slate-400">
          Upload two PDF papers or use sample data to generate a novel hypothesis.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {[0, 1].map((index) => (
          <div 
            key={index}
            className={`
              relative h-64 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center p-6 transition-all duration-300
              ${papers[index] 
                ? 'border-emerald-500/50 bg-emerald-900/10' 
                : 'border-slate-700 bg-slate-800/50 hover:border-blue-500/50 hover:bg-slate-800'}
            `}
          >
            {papers[index] ? (
              <div className="text-center animate-in fade-in zoom-in duration-300">
                <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-400">
                  <FileText size={32} />
                </div>
                <h3 className="text-sm font-semibold text-white line-clamp-2 mb-1">
                  {papers[index].title}
                </h3>
                <p className="text-xs text-emerald-400 flex items-center justify-center gap-1">
                  <CheckCircle size={12} /> Ready for analysis
                </p>
              </div>
            ) : (
              <div className="text-center text-slate-500">
                <div className="w-16 h-16 bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Upload size={24} />
                </div>
                <p className="text-sm font-medium">Drop Paper {index + 1} here</p>
                <p className="text-xs mt-2 opacity-60">or click to browse (PDF)</p>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="flex flex-col items-center gap-4">
        {papers.length < 2 && (
             <button
             onClick={handleLoadSample}
             className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-2"
           >
             <Sparkles size={16} /> Load Sample Papers (Blockchain & Agentic AI)
           </button>
        )}
     
        <button
          onClick={handleStartAnalysis}
          disabled={papers.length !== 2 || isLoading}
          className={`
            w-full md:w-auto px-8 py-4 rounded-xl font-bold text-lg tracking-wide transition-all transform hover:scale-105 active:scale-95
            flex items-center justify-center gap-3
            ${papers.length === 2 
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-900/20 hover:shadow-blue-900/40 cursor-pointer' 
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'}
          `}
        >
          {isLoading ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing Semantics...
            </>
          ) : (
            <>
              Generate Hypothesis <Sparkles size={20} />
            </>
          )}
        </button>
      </div>
    </div>
  );
};