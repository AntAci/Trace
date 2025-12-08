
import React, { useState, useRef, useEffect } from 'react';
import { HypothesisArtifact, MintingStatus } from '../types';
import { Beaker, Brain, Award, ExternalLink, ShieldCheck, RotateCcw, Link, User, Clock, BadgeCheck, Dna, Sparkles, Copy, Twitter, Mail, Share2, RefreshCw, List } from 'lucide-react';

interface HypothesisCardProps {
  artifact: HypothesisArtifact;
  mintingStatus: MintingStatus;
  onMint: () => void;
  isStandalone?: boolean;
  onCreateAnother?: () => void;
}

export const HypothesisCard: React.FC<HypothesisCardProps> = ({ artifact, mintingStatus, onMint, isStandalone = false, onCreateAnother }) => {
  const [isFlipped, setIsFlipped] = useState(false);
  const [rotate, setRotate] = useState({ x: 0, y: 0 });
  const cardRef = useRef<HTMLDivElement>(null);
  const [score, setScore] = useState(0);

  // Confidence score count-up animation
  useEffect(() => {
    let start = 0;
    const end = artifact.confidence.overall;
    const duration = 1200;
    const incrementTime = 20;
    const step = (end / duration) * incrementTime;

    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setScore(end);
        clearInterval(timer);
      } else {
        setScore(Math.floor(start));
      }
    }, incrementTime);

    return () => clearInterval(timer);
  }, [artifact.confidence.overall]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    // Disable tilt interaction when flipped to ensure stable scrolling
    if (isFlipped || !cardRef.current) return;
    
    const { left, top, width, height } = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - left - width / 2) / 25; // Sensitivity
    const y = -(e.clientY - top - height / 2) / 25;
    setRotate({ x, y });
  };

  const handleMouseLeave = () => {
    setRotate({ x: 0, y: 0 });
  };

  // Determine gradient based on score
  const getGradient = (score: number) => {
    if (score >= 70) return 'from-purple-600 to-blue-600';
    if (score >= 40) return 'from-blue-600 to-teal-500';
    return 'from-orange-500 to-red-500';
  };

  const scoreColor = getGradient(artifact.confidence.overall);

  // Formatting helpers
  const getQualityLabel = (score: number) => {
      if (score >= 90) return "LEGENDARY";
      if (score >= 75) return "EPIC";
      if (score >= 50) return "RARE";
      return "COMMON";
  };
  
  const formatDate = (dateStr: string) => {
      return new Date(dateStr).toLocaleString('en-US', { 
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
  };

  return (
    <div className={`relative w-full max-w-[380px] h-[600px] group perspective-1000 mx-auto ${isStandalone ? 'scale-110 md:scale-125 transition-transform duration-700' : 'my-8'}`}>
      {/* 3D Container */}
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="w-full h-full relative preserve-3d transition-transform duration-500 cubic-bezier(0.23, 1, 0.32, 1)"
        style={{
          transform: `rotateY(${isFlipped ? 180 : rotate.x}deg) rotateX(${isFlipped ? 0 : rotate.y}deg)`,
        }}
      >
        {/* Rainbow Border Layer (Behind) */}
        <div className="absolute -inset-[2px] rounded-[26px] overflow-hidden pointer-events-none transform translateZ(-10px)">
           <div className={`absolute top-[-50%] left-[-50%] w-[200%] h-[200%] bg-conic-rainbow opacity-60 blur-md ${mintingStatus === 'minted' ? 'animate-spin' : 'animate-spin-slow'}`} />
        </div>

        {/* --- FRONT FACE --- */}
        <div 
            onClick={() => setIsFlipped(true)}
            className={`
                absolute inset-[2px] backface-hidden rounded-[24px] overflow-hidden shadow-2xl bg-slate-900 border border-slate-700/50 cursor-pointer 
                ${isFlipped ? 'pointer-events-none' : 'pointer-events-auto'}
            `}
        >
            {/* Background Image */}
            <div className="absolute inset-0 bg-slate-900 z-0">
               {artifact.imageUrl ? (
                   <img src={artifact.imageUrl} alt="Scientific Illustration" className="w-full h-full object-cover opacity-80" />
               ) : (
                   <div className={`w-full h-full bg-gradient-to-br ${scoreColor} opacity-20`} />
               )}
               <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-transparent" />
            </div>

            {/* Holographic Foil Overlay */}
             <div 
                className="absolute inset-0 z-10 opacity-30 mix-blend-color-dodge pointer-events-none transition-all duration-100"
                style={{
                    background: `linear-gradient(${115 + rotate.x * 2}deg, transparent 30%, rgba(255,255,255,0.4) 45%, rgba(255,0,255,0.2) 50%, rgba(255,255,255,0.4) 55%, transparent 70%)`,
                    transform: `translateX(${rotate.x * -2}px) translateY(${rotate.y * -2}px)`
                }}
            />

            {/* Content Overlay */}
            <div className="absolute inset-0 p-6 flex flex-col justify-between z-20">
                {/* Header */}
                <div className="flex justify-between items-start">
                    <div className="bg-slate-950/40 backdrop-blur-md border border-white/10 px-3 py-1 rounded-full">
                        <span className="text-xs font-mono text-emerald-400 tracking-wider">HYPOTHESIS #{artifact.id}</span>
                    </div>
                    
                    <div onClick={(e) => e.stopPropagation()}>
                        {mintingStatus === 'idle' && (
                            <button
                                onClick={onMint}
                                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-bold px-4 py-2 rounded-full shadow-lg shadow-purple-900/20 flex items-center gap-1.5 transition-all hover:scale-105 active:scale-95"
                            >
                                <Beaker size={14} /> <span>Mint</span>
                            </button>
                        )}
                        {mintingStatus === 'minting' && (
                             <div className="bg-slate-900/80 backdrop-blur border border-slate-700 px-3 py-1.5 rounded-full flex items-center gap-2">
                                <div className="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                                <span className="text-xs text-purple-200 font-medium">Minting...</span>
                             </div>
                        )}
                        {mintingStatus === 'minted' && (
                            <div className="bg-purple-500/20 backdrop-blur-md border border-purple-500/50 p-2 rounded-full text-purple-300 animate-pulse">
                                <ShieldCheck size={20} />
                            </div>
                        )}
                    </div>
                </div>

                {/* Middle - Title (Fades out when minted to make room for Slab) */}
                <div className={`mt-8 transition-opacity duration-500 ${mintingStatus === 'minted' ? 'opacity-0' : 'opacity-100'}`}>
                    <h2 className="text-2xl font-display font-bold text-white leading-tight drop-shadow-lg">
                        {artifact.title}
                    </h2>
                    <div className="flex items-center gap-2 mt-2">
                        <span className={`h-2 w-2 rounded-full bg-gradient-to-r ${scoreColor}`}></span>
                        <span className="text-sm text-slate-300 font-medium bg-slate-900/60 px-2 py-0.5 rounded backdrop-blur-sm">
                            Novelty: {artifact.confidence.novelty}%
                        </span>
                    </div>
                </div>

                {/* Finalized Metadata Slab (Only shows when Minted) */}
                {mintingStatus === 'minted' && (
                    <div 
                        className="absolute top-16 left-0 w-full px-5 animate-in slide-in-from-bottom-8 fade-in duration-700 z-30"
                        onClick={(e) => e.stopPropagation()} // Prevent card flip when interacting with the receipt
                    >
                        <div className="bg-slate-950/90 backdrop-blur-xl border border-amber-500/30 rounded-2xl overflow-hidden shadow-2xl">
                            
                            {/* Receipt Header */}
                            <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-3 border-b border-white/5 flex items-center justify-center gap-2">
                                <Sparkles size={12} className="text-amber-400" />
                                <span className="text-[10px] font-display font-bold text-amber-400 tracking-[0.2em] uppercase">
                                    Hypothesis Immortalized
                                </span>
                                <Dna size={12} className="text-amber-400" />
                            </div>

                            <div className="p-4 space-y-4">
                                {/* Summary Section */}
                                <div className="space-y-1">
                                    <h3 className="text-sm font-bold text-white line-clamp-1">{artifact.title}</h3>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-slate-400">Confidence:</span>
                                        <span className={`text-xs font-bold ${score >= 70 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                            {artifact.confidence.overall}%
                                        </span>
                                    </div>
                                </div>

                                <div className="h-px bg-white/10 w-full" />

                                {/* Blockchain Details */}
                                <div className="space-y-2">
                                    <div className="flex justify-between text-[11px] font-mono">
                                        <span className="text-slate-500">Transaction</span>
                                        <span className="text-slate-300 truncate w-24">{artifact.blockchain?.transactionHash}</span>
                                    </div>
                                    <div className="flex justify-between text-[11px] font-mono">
                                        <span className="text-slate-500">Block</span>
                                        <span className="text-blue-300">#{artifact.blockchain?.blockNumber.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between text-[11px] font-mono">
                                        <span className="text-slate-500">Network</span>
                                        <span className="text-emerald-400">Neo N3 Mainnet</span>
                                    </div>
                                </div>

                                {/* Link Buttons */}
                                <div className="flex gap-2">
                                    <a 
                                        href={artifact.blockchain?.explorerUrl} 
                                        target="_blank" 
                                        rel="noreferrer"
                                        className="flex-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 text-[10px] font-bold py-2 rounded-lg flex items-center justify-center gap-1.5 border border-amber-500/40 transition-colors"
                                    >
                                        <ExternalLink size={12} /> View on Dora
                                    </a>
                                    <button className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold py-2 rounded-lg flex items-center justify-center gap-1.5 border border-slate-600 transition-colors">
                                        <Copy size={12} /> Copy Hash
                                    </button>
                                </div>

                                <div className="h-px bg-white/10 w-full" />

                                {/* Share Section */}
                                <div className="space-y-2 text-center">
                                    <div className="text-[10px] text-slate-500 uppercase tracking-widest">Share your discovery</div>
                                    <div className="flex justify-center gap-3">
                                        <button className="p-2 bg-slate-800 rounded-full hover:bg-blue-500 hover:text-white text-slate-400 border border-slate-700 transition-colors">
                                            <Twitter size={14} />
                                        </button>
                                        <button className="p-2 bg-slate-800 rounded-full hover:bg-purple-500 hover:text-white text-slate-400 border border-slate-700 transition-colors">
                                            <Link size={14} />
                                        </button>
                                        <button className="p-2 bg-slate-800 rounded-full hover:bg-emerald-500 hover:text-white text-slate-400 border border-slate-700 transition-colors">
                                            <Mail size={14} />
                                        </button>
                                    </div>
                                </div>
                                
                                <div className="h-px bg-white/10 w-full" />

                                {/* Bottom Nav */}
                                <div className="flex justify-between items-center pt-1">
                                    {onCreateAnother && (
                                        <button 
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onCreateAnother();
                                            }}
                                            className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
                                        >
                                            <RefreshCw size={10} /> Create Another
                                        </button>
                                    )}
                                    <button className="text-[10px] text-amber-500 hover:text-amber-400 flex items-center gap-1 transition-colors">
                                        <List size={10} /> Discovery Feed
                                    </button>
                                </div>

                            </div>
                        </div>
                    </div>
                )}

                {/* Bottom - Stats Card (Only shows when NOT minted) */}
                <div className={`mt-auto bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-4 transform transition-all duration-500 shadow-2xl ${mintingStatus === 'minted' ? 'translate-y-full opacity-0 pointer-events-none' : ''}`}>
                    <div className="flex items-end justify-between mb-2">
                        <span className="text-sm text-slate-400 font-medium uppercase tracking-wider">Confidence Score</span>
                        <span className={`text-4xl font-display font-bold bg-clip-text text-transparent bg-gradient-to-r ${scoreColor}`}>
                            {score}%
                        </span>
                    </div>
                    <div className="w-full bg-slate-700/50 h-1.5 rounded-full overflow-hidden">
                        <div 
                            className={`h-full bg-gradient-to-r ${scoreColor} transition-all duration-1000 ease-out`}
                            style={{ width: `${score}%` }}
                        />
                    </div>
                    <p className="text-xs text-slate-300 mt-3 line-clamp-2 leading-relaxed">
                        {artifact.statement}
                    </p>
                    <div className="mt-3 text-center text-[10px] text-slate-500 flex items-center justify-center gap-1 opacity-80 uppercase tracking-widest font-mono">
                         Click card to flip
                    </div>
                </div>

            </div>
            
            {/* Glass Shine */}
            <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/5 to-white/0 pointer-events-none z-30" />
        </div>

        {/* --- BACK FACE --- */}
        <div className={`absolute inset-[2px] backface-hidden rotate-y-180 rounded-[24px] bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden flex flex-col ${isFlipped ? 'pointer-events-auto' : 'pointer-events-none'}`}>
            
            {/* Flip Back Button */}
            <button 
                onClick={(e) => {
                    e.stopPropagation();
                    setIsFlipped(false);
                }}
                className="absolute top-4 right-4 z-20 p-2 bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white rounded-full backdrop-blur-md transition-colors border border-slate-700"
                title="Flip back"
            >
                <RotateCcw size={16} />
            </button>

            <div className="p-6 pt-12 flex-1 overflow-y-auto custom-scrollbar relative z-10 cursor-auto text-left">
                <div className="flex items-center gap-2 mb-6 text-slate-400">
                    <Brain size={18} />
                    <span className="text-xs font-bold tracking-widest uppercase">Research Analysis</span>
                </div>

                <div className="space-y-6">
                    {/* Statement */}
                    <div>
                        <h3 className="text-sm font-semibold text-white mb-2">Hypothesis Statement</h3>
                        <p className="text-sm text-slate-300 leading-relaxed border-l-2 border-purple-500 pl-3">
                            {artifact.statement}
                        </p>
                    </div>

                    {/* Reasoning */}
                    <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700">
                        <h3 className="text-xs font-semibold text-emerald-400 mb-1 flex items-center gap-2">
                            <Award size={14} /> Novelty Assessment
                        </h3>
                        <p className="text-xs text-slate-300">
                            {artifact.noveltyAssessment.reasoning}
                        </p>
                    </div>

                    {/* Evidence Chain */}
                    <div>
                        <h3 className="text-sm font-semibold text-white mb-3">Evidence Chain</h3>
                        <div className="space-y-3">
                            {artifact.evidence.map((ev, i) => (
                                <div key={i} className="text-xs bg-slate-800/30 p-3 rounded border border-slate-800">
                                    <div className="flex justify-between text-slate-500 mb-1">
                                        <span>{ev.paper.substring(0, 20)}...</span>
                                        <span className={
                                            ev.confidenceLevel === 'High' ? 'text-emerald-400' : 
                                            ev.confidenceLevel === 'Medium' ? 'text-blue-400' : 'text-orange-400'
                                        }>{ev.confidenceLevel} Conf.</span>
                                    </div>
                                    <p className="italic text-slate-400">"{ev.quote}"</p>
                                </div>
                            ))}
                        </div>
                    </div>

                     {/* Proposed Experiment */}
                     <div>
                        <h3 className="text-sm font-semibold text-white mb-2">Experimental Design</h3>
                        <div className="text-xs text-slate-300 space-y-1">
                            {artifact.proposedExperiment.procedure.map((step, idx) => (
                                <div key={idx} className="flex gap-2">
                                    <span className="text-purple-400">{idx + 1}.</span>
                                    <span>{step}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Actions (Back) */}
            <div className="p-4 bg-slate-950 border-t border-slate-800 z-20">
                {mintingStatus === 'idle' ? (
                     <button 
                     onClick={(e) => {
                         e.stopPropagation();
                         onMint();
                     }}
                     className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-900/20"
                 >
                     Mint on Neo N3 <Beaker size={18} />
                 </button>
                ) : mintingStatus === 'minting' ? (
                    <div className="w-full py-3 bg-slate-800 text-slate-300 rounded-xl font-medium flex items-center justify-center gap-2">
                         <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                         Minting Artifact...
                    </div>
                ) : (
                    <div className="w-full py-2">
                         <div className="flex flex-col gap-2">
                            <div className="flex items-center justify-between text-xs text-slate-400">
                                <span>Network</span>
                                <span className="text-purple-400">Neo N3 Mainnet</span>
                            </div>
                            <div className="flex items-center justify-between text-xs text-slate-400">
                                <span>Token ID</span>
                                <span className="text-white font-mono">#{artifact.blockchain?.nftId}</span>
                            </div>
                            <a 
                                href={artifact.blockchain?.explorerUrl}
                                onClick={(e) => e.stopPropagation()} 
                                target="_blank"
                                rel="noreferrer"
                                className="mt-2 w-full py-2 bg-slate-800 hover:bg-slate-700 text-emerald-400 text-xs font-bold rounded-lg flex items-center justify-center gap-2 transition-colors"
                            >
                                View on NeoTube <ExternalLink size={12} />
                            </a>
                         </div>
                    </div>
                )}
            </div>
        </div>
      </div>
    </div>
  );
};
