import React, { useEffect, useState } from 'react';
import { Hexagon, Zap, Database, BrainCircuit, Sparkles, FileText, Layers, GitMerge } from 'lucide-react';

interface IsometricAssemblyProps {
  step: number; // 0-5 mapping to the assembly stages
}

// Cube definitions for the scene
interface CubeData {
  id: number;
  type: 'purple' | 'pink' | 'white' | 'emerald';
  x: number;
  y: number;
  z: number;
  delay: number;
  label: string;
}

export const IsometricAssembly: React.FC<IsometricAssemblyProps> = ({ step }) => {
  const [activeLayers, setActiveLayers] = useState<number>(0);
  const [cubes, setCubes] = useState<CubeData[]>([]);
  const [narrative, setNarrative] = useState("Initializing TRACE protocol...");
  const [progress, setProgress] = useState(0);

  // Generate random concept cubes
  useEffect(() => {
    const newCubes: CubeData[] = [];
    const positions = [
      {x: -120, y: -120}, {x: -120, y: 0}, {x: -120, y: 120},
      {x: 0, y: -120}, {x: 0, y: 120},
      {x: 120, y: -120}, {x: 120, y: 0}, {x: 120, y: 120}
    ];

    // Create 12 concept cubes
    for (let i = 0; i < 12; i++) {
        const type = i < 4 ? 'purple' : i < 8 ? 'pink' : i < 10 ? 'white' : 'emerald';
        const pos = positions[i % positions.length];
        // Add some random jitter
        const x = pos.x + (Math.random() * 40 - 20);
        const y = pos.y + (Math.random() * 40 - 20);
        
        newCubes.push({
            id: i,
            type: type as any,
            x,
            y,
            z: 150 + Math.random() * 50,
            delay: i * 0.2,
            label: type === 'purple' ? 'Paper A' : type === 'pink' ? 'Paper B' : type === 'white' ? 'Shared' : 'Novelty'
        });
    }
    setCubes(newCubes);
  }, []);

  // Sync animation state with app step
  useEffect(() => {
    switch (step) {
        case 0:
            setNarrative("Materializing concept workspace...");
            setProgress(10);
            setActiveLayers(0);
            break;
        case 1:
            setNarrative("Constructing artifact foundation...");
            setProgress(25);
            setActiveLayers(1);
            break;
        case 2:
            setNarrative("Extracting and stacking data layers...");
            setProgress(45);
            setActiveLayers(3);
            break;
        case 3:
            setNarrative("Processing shared semantic links...");
            setProgress(65);
            setActiveLayers(5);
            break;
        case 4:
            setNarrative("Identifying novel research gap...");
            setProgress(85);
            setActiveLayers(6);
            break;
        case 5:
            setNarrative("Synthesizing final NFT artifact...");
            setProgress(100);
            setActiveLayers(7);
            break;
    }
  }, [step]);

  return (
    <div className="w-full h-[600px] bg-slate-900 relative overflow-hidden flex flex-col items-center justify-center">
      {/* Background Ambience */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(30,41,59,0.5),#0f172a)]" />
      
      {/* --- UI OVERLAYS --- */}
      
      {/* Top Left: Progress & Logs Container */}
      <div className="absolute top-8 left-8 z-20 flex flex-col gap-3 w-72 animate-in slide-in-from-left duration-500">
        
        {/* Progress Box */}
        <div className="bg-slate-800/80 backdrop-blur border border-slate-700 p-4 rounded-xl shadow-xl">
            <div className="flex items-center gap-2 mb-2 text-purple-400">
                <Hexagon size={16} className="animate-pulse" />
                <span className="text-xs font-bold tracking-widest uppercase">Card Assembly</span>
            </div>
            <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden mb-2">
                <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-emerald-400 transition-all duration-1000"
                    style={{ width: `${progress}%` }}
                />
            </div>
            <div className="flex justify-between text-xs text-slate-400">
                <span>Layers: {activeLayers}/7</span>
                <span>{progress}%</span>
            </div>
        </div>

        {/* Formation Log */}
        <div className="bg-slate-900/80 border border-slate-700 rounded-xl p-3 font-mono text-[10px] text-slate-400 h-32 overflow-hidden flex flex-col justify-end shadow-xl backdrop-blur-sm">
            <div className="opacity-40 mb-1">{'>'} Connecting to Bloxberg chain...</div>
            {step >= 1 && <div className="opacity-60 mb-1">{'>'} Foundation layer established.</div>}
            {step >= 2 && <div className="opacity-70 mb-1">{'>'} Ingesting 14 citations from Paper A...</div>}
            {step >= 3 && <div className="opacity-80 mb-1 text-purple-300">{'>'} Cross-reference check: 89% match.</div>}
            {step >= 4 && <div className="opacity-90 mb-1 text-emerald-300">{'>'} NOVEL INSIGHT DETECTED: Trust Gap Verification.</div>}
            {step >= 5 && <div className="text-white animate-pulse">{'>'} Finalizing Artifact assembly...</div>}
         </div>

      </div>

      {/* Top Right: Narrator */}
      <div className="absolute top-8 right-8 bg-slate-800/80 backdrop-blur border border-slate-700 p-4 rounded-xl w-64 z-20 shadow-xl animate-in slide-in-from-right duration-500">
        <div className="flex items-center gap-2 mb-2 text-emerald-400">
            <BrainCircuit size={16} />
            <span className="text-xs font-bold tracking-widest uppercase">TRACE ENGINE</span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed font-mono">
            {narrative}
        </p>
      </div>

      {/* --- 3D SCENE --- */}
      <div className="relative w-[600px] h-[600px] flex items-center justify-center scale-75 md:scale-100">
        <div className="iso-scene relative w-full h-full flex items-center justify-center">
            
            {/* 1. Crafting Platform */}
            <div className="absolute w-[400px] h-[400px] rounded-full border-2 border-slate-700/50 flex items-center justify-center animate-spin-platform shadow-[0_0_50px_rgba(0,0,0,0.5)] bg-slate-900/80 backdrop-blur-sm transform translateZ(-20px)">
                 <div className="absolute w-[300px] h-[300px] rounded-full border border-slate-600/30" />
                 <div className="absolute w-[200px] h-[200px] rounded-full border border-slate-500/30" />
                 <div className="font-serif-display text-9xl text-slate-800 opacity-20 select-none">Λ</div>
                 
                 {/* Ripple effect on impact */}
                 {activeLayers > 0 && (
                     <div className="absolute inset-0 rounded-full border-2 border-emerald-500/30 animate-ripple" />
                 )}
            </div>

            {/* 2. Floating Concept Cubes */}
            {step < 5 && cubes.map((cube) => (
                <div 
                    key={cube.id}
                    className="absolute animate-float transition-all duration-1000"
                    style={{
                        transform: `translate3d(${cube.x}px, ${cube.y}px, ${cube.z}px)`,
                        animationDelay: `${cube.delay}s`,
                        opacity: step > 3 && cube.type !== 'emerald' ? 0.2 : 1
                    }}
                >
                    <div className="w-10 h-10 cube-wrap relative">
                        <div className="cube text-[8px] flex items-center justify-center font-bold">
                            <div className={`face face-front ${getCubeColor(cube.type)} border border-white/10 opacity-90`} />
                            <div className={`face face-back ${getCubeColor(cube.type)} border border-white/10 opacity-90`} />
                            <div className={`face face-right ${getCubeColor(cube.type)} border border-white/10 opacity-80`} />
                            <div className={`face face-left ${getCubeColor(cube.type)} border border-white/10 opacity-80`} />
                            <div className={`face face-top ${getCubeColor(cube.type)} border border-white/10 opacity-100`} />
                            <div className={`face face-bottom ${getCubeColor(cube.type)} border border-white/10 opacity-60`} />
                        </div>
                    </div>
                    {/* Label */}
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap bg-slate-900 text-white text-[8px] px-1 rounded opacity-60">
                        {cube.label}
                    </div>
                </div>
            ))}

            {/* 3. The Artifact Card Assembly - Exploded View */}
            <div className="absolute transition-all duration-700" style={{ transform: 'translateZ(0px)' }}>
                {/* Base Layer (Foundation) */}
                <div 
                    className={`
                        w-[200px] h-[280px] bg-slate-950 border-2 border-slate-700 rounded-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] transition-all duration-700
                        ${activeLayers >= 1 ? 'opacity-100' : 'opacity-0 scale-90'}
                        flex items-center justify-center
                    `}
                    style={{ transform: 'translateZ(0px)' }}
                >
                     <div className="text-slate-800 font-bold text-6xl opacity-20">#</div>
                </div>

                {/* Content Layers Stacking */}
                {[
                    { color: 'border-purple-500/40 bg-purple-900/20', icon: FileText, label: 'Raw Data' },
                    { color: 'border-blue-500/40 bg-blue-900/20', icon: Database, label: 'Metadata' },
                    { color: 'border-emerald-500/40 bg-emerald-900/20', icon: Layers, label: 'Evidence' },
                    { color: 'border-amber-500/40 bg-amber-900/20', icon: GitMerge, label: 'Logic' },
                    { color: 'border-slate-400/40 bg-slate-800/40', icon: BrainCircuit, label: 'Synthesis' },
                ].map((layer, i) => (
                    <div 
                        key={i}
                        className={`
                            absolute inset-0 w-[200px] h-[280px] rounded-xl border-2 backdrop-blur-sm transition-all duration-500
                            flex flex-col items-center justify-center gap-2 shadow-lg
                            ${layer.color}
                        `}
                        style={{ 
                            // Significant spacing for separation (35px steps)
                            transform: `translateZ(${(i + 1) * 35}px)`, 
                            opacity: activeLayers > i + 1 ? 1 : 0,
                            scale: activeLayers > i + 1 ? 1 : 0.8
                        }}
                    >
                        <layer.icon size={24} className="text-white/80" />
                        <span className="text-[10px] font-mono uppercase tracking-widest text-white/60">{layer.label}</span>
                        
                        {/* Corner markers for tech feel */}
                        <div className="absolute top-1 left-1 w-1 h-1 bg-white/40 rounded-full" />
                        <div className="absolute bottom-1 right-1 w-1 h-1 bg-white/40 rounded-full" />
                    </div>
                ))}

                {/* Top Holographic Layer (Breakthrough) */}
                <div 
                    className={`
                        absolute inset-0 w-[200px] h-[280px] bg-gradient-to-br from-purple-500/30 to-emerald-500/30 rounded-xl border-2 border-white/40 backdrop-blur-md
                        flex flex-col items-center justify-center gap-4 transition-all duration-1000 shadow-[0_0_30px_rgba(16,185,129,0.3)]
                    `}
                    style={{ 
                        transform: `translateZ(210px)`, // Matches stack height
                        opacity: activeLayers >= 7 ? 1 : 0
                    }}
                >
                    <div className="w-16 h-16 rounded-full bg-gradient-to-r from-purple-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 animate-pulse">
                        <Sparkles className="text-white" />
                    </div>
                    <div className="text-center">
                        <div className="text-[10px] text-emerald-300 font-mono tracking-widest uppercase mb-1">Generated</div>
                        <div className="text-white font-serif-display text-2xl font-bold">Artifact #427</div>
                    </div>
                    
                    {/* Corner accents */}
                    <div className="absolute top-2 left-2 w-2 h-2 border-t border-l border-white/50" />
                    <div className="absolute top-2 right-2 w-2 h-2 border-t border-r border-white/50" />
                    <div className="absolute bottom-2 left-2 w-2 h-2 border-b border-l border-white/50" />
                    <div className="absolute bottom-2 right-2 w-2 h-2 border-b border-r border-white/50" />
                </div>
            </div>

        </div>
      </div>

    </div>
  );
};

// Helper for cube colors
const getCubeColor = (type: string) => {
    switch(type) {
        case 'purple': return 'bg-purple-600';
        case 'pink': return 'bg-pink-600';
        case 'white': return 'bg-slate-100';
        case 'emerald': return 'bg-emerald-500';
        default: return 'bg-slate-500';
    }
}