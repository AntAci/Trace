
import React, { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

export const MintCelebration: React.FC = () => {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    // Sequence the animation stages
    const t1 = setTimeout(() => setStage(1), 100); // Explode
    const t2 = setTimeout(() => setStage(2), 1200); // Ray burst
    const t3 = setTimeout(() => setStage(3), 2500); // Fade out overlay
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, []);

  if (stage === 3) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none overflow-hidden">
      {/* Background Dimmer */}
      <div className={`absolute inset-0 bg-slate-950 transition-opacity duration-1000 ${stage >= 2 ? 'opacity-0' : 'opacity-80'}`} />

      {/* Shockwave */}
      <div 
        className={`absolute w-[100px] h-[100px] rounded-full border-4 border-white opacity-0 transition-all duration-1000 ease-out
        ${stage === 1 ? 'scale-[20] opacity-0 border-width-0' : 'scale-0 opacity-100'}`} 
      />

      {/* Light Rays */}
      <div className={`absolute inset-0 flex items-center justify-center transition-all duration-700 ${stage >= 1 ? 'opacity-100' : 'opacity-0'}`}>
         <div className="relative w-full h-full animate-[spin_10s_linear_infinite]">
            {[...Array(12)].map((_, i) => (
                <div 
                    key={i}
                    className="absolute top-1/2 left-1/2 w-[200vw] h-[100px] bg-gradient-to-r from-transparent via-purple-500/30 to-transparent transform origin-left"
                    style={{ transform: `rotate(${i * 30}deg) translateY(-50%)` }}
                />
            ))}
         </div>
      </div>

      {/* Central Burst */}
      <div className={`relative flex flex-col items-center justify-center transition-all duration-700 transform ${stage === 1 ? 'scale-150' : 'scale-100'}`}>
         <div className={`text-6xl font-display font-bold text-white drop-shadow-[0_0_30px_rgba(255,255,255,0.8)] ${stage >= 1 ? 'animate-bounce' : 'opacity-0'}`}>
            MINTED
         </div>
         <div className="flex gap-2 mt-4">
             <Sparkles className="text-yellow-400 w-8 h-8 animate-pulse" />
             <Sparkles className="text-purple-400 w-8 h-8 animate-pulse delay-100" />
             <Sparkles className="text-emerald-400 w-8 h-8 animate-pulse delay-200" />
         </div>
      </div>

      {/* Particles */}
      {stage >= 1 && [...Array(20)].map((_, i) => (
          <div 
            key={i}
            className="absolute w-2 h-2 bg-white rounded-full animate-[ping_1s_ease-out_infinite]"
            style={{
                top: `${50 + (Math.random() - 0.5) * 50}%`,
                left: `${50 + (Math.random() - 0.5) * 50}%`,
                animationDelay: `${Math.random()}s`
            }}
          />
      ))}
    </div>
  );
};
