import React, { useEffect, useState } from 'react';
import { SourcePaper } from '../types';
import { 
  FileText, 
  Database, 
  AlertCircle, 
  Search, 
  Microscope, 
  Zap, 
  Scale, 
  Link as LinkIcon,
  Hexagon,
  BrainCircuit,
  Info,
  XCircle,
  ArrowRight
} from 'lucide-react';

interface AnalysisVisualizationProps {
  papers: SourcePaper[];
  step: number; // 0-5
  showStatus?: boolean;
}

// Node types and positions
type NodeType = 'paper' | 'claim' | 'method' | 'data' | 'limitation' | 'contradiction' | 'gap' | 'synthesis';

interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  details: string; // Added details for hover/click
  x: number; // Percentage 0-100
  y: number; // Percentage 0-100
  icon: React.ElementType;
  color: string;
  sourcePaperIndex?: number; // 0 or 1, or undefined for shared
  appearsAtStep: number;
}

interface GraphEdge {
  id: string;
  from: string;
  to: string;
  label: string;
  details: string;
  type: 'solid' | 'dashed' | 'dotted';
  color: string;
  appearsAtStep: number;
}

export const AnalysisVisualization: React.FC<AnalysisVisualizationProps> = ({ papers, step, showStatus = true }) => {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  
  // Interaction State
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredEdgeId, setHoveredEdgeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  // Initialize graph data structure
  useEffect(() => {
    // Helper to extract keywords for simulated details
    const getKeywords = (text: string) => text.split(' ').filter(w => w.length > 5).slice(0, 3).join(', ');
    
    // Simulate content extraction based on inputs
    // We check if it matches our demo papers to provide rich, specific context
    const isDemo = papers.some(p => p.title.includes('Blockchain'));

    const newNodes: GraphNode[] = [
      // Step 1: Source Papers
      { 
        id: 'p1', type: 'paper', label: 'Paper A', details: papers[0].title, 
        x: 20, y: 50, icon: FileText, color: 'text-blue-400', sourcePaperIndex: 0, appearsAtStep: 0 
      },
      { 
        id: 'p2', type: 'paper', label: 'Paper B', details: papers[1].title, 
        x: 80, y: 50, icon: FileText, color: 'text-purple-400', sourcePaperIndex: 1, appearsAtStep: 0 
      },
      
      // Step 2: Extraction (Claims & Methods)
      { 
        id: 'p1_m', type: 'method', label: 'Methodology', 
        details: isDemo ? 'Bloxberg PoA Blockchain & Research Object Chains (ROC).' : 'Extracted experimental setup and control variables.', 
        x: 15, y: 25, icon: Microscope, color: 'text-emerald-400', sourcePaperIndex: 0, appearsAtStep: 1 
      },
      { 
        id: 'p1_c', type: 'claim', label: 'Core Claim', 
        details: isDemo ? 'Blockchain ensures immutable provenance of research steps.' : `Primary assertion: ${getKeywords(papers[0].content)}`, 
        x: 25, y: 75, icon: Zap, color: 'text-amber-400', sourcePaperIndex: 0, appearsAtStep: 1 
      },
      { 
        id: 'p2_m', type: 'method', label: 'Methodology', 
        details: isDemo ? 'Autonomous LLM Agents (Coscientist, ChemCrow).' : 'Identified statistical models and sampling techniques.', 
        x: 85, y: 25, icon: Microscope, color: 'text-emerald-400', sourcePaperIndex: 1, appearsAtStep: 1 
      },
      { 
        id: 'p2_c', type: 'claim', label: 'Core Claim', 
        details: isDemo ? 'Agents automate discovery but suffer from hallucination.' : `Primary assertion: ${getKeywords(papers[1].content)}`, 
        x: 75, y: 75, icon: Zap, color: 'text-amber-400', sourcePaperIndex: 1, appearsAtStep: 1 
      },

      // Step 3: Deep Dive (Data & Limitations)
      { 
        id: 'p1_d', type: 'data', label: 'Datasets', 
        details: isDemo ? 'DeepLabCut animal pose estimation artifacts (HDF5).' : 'N=150 samples processed via regression analysis.', 
        x: 10, y: 50, icon: Database, color: 'text-cyan-400', sourcePaperIndex: 0, appearsAtStep: 2 
      },
      { 
        id: 'p1_l', type: 'limitation', label: 'Limitations', 
        details: isDemo ? 'Verifies existence/integrity but not semantic quality.' : 'Potential bias in sample selection noted.', 
        x: 30, y: 35, icon: Scale, color: 'text-rose-400', sourcePaperIndex: 0, appearsAtStep: 2 
      },
      { 
        id: 'p2_d', type: 'data', label: 'Datasets', 
        details: isDemo ? 'Agent benchmarks (LitSearch, SciLitLLM).' : 'Longitudinal data spanning 5 years.', 
        x: 90, y: 50, icon: Database, color: 'text-cyan-400', sourcePaperIndex: 1, appearsAtStep: 2 
      },
      { 
        id: 'p2_l', type: 'limitation', label: 'Limitations', 
        details: isDemo ? 'Trustworthiness & reliability issues in auto-reviews.' : 'Environmental factors not fully isolated.', 
        x: 70, y: 35, icon: Scale, color: 'text-rose-400', sourcePaperIndex: 1, appearsAtStep: 2 
      },

      // Step 4: Connections (Contradictions & Links)
      { 
        id: 'conflict', type: 'contradiction', label: 'Gap Detected', 
        details: isDemo ? 'Agents create fast, untrusted science vs Blockchain slow, trusted records.' : 'Direct conflict found in experimental outcomes.', 
        x: 50, y: 30, icon: AlertCircle, color: 'text-red-500', appearsAtStep: 3 
      },
      { 
        id: 'link', type: 'synthesis', label: 'Semantic Link', 
        details: isDemo ? 'Both operate on digital research artifacts and workflows.' : 'Both papers utilize similar underlying theoretical frameworks.', 
        x: 50, y: 65, icon: LinkIcon, color: 'text-blue-300', appearsAtStep: 3 
      },

      // Step 5: The Gap
      { 
        id: 'gap', type: 'gap', label: 'Trust Gap', 
        details: isDemo ? 'Need for automated, trustless verification of AI Agent outputs.' : 'Unexplored intersection of methodologies identified.', 
        x: 50, y: 42, icon: Search, color: 'text-white', appearsAtStep: 4 
      },
      
      // Step 6: Synthesis
      { 
        id: 'hypo', type: 'synthesis', label: 'Hypothesis', 
        details: 'Novel hypothesis generated filling the identified gap.', 
        x: 50, y: 88, icon: BrainCircuit, color: 'text-fuchsia-400', appearsAtStep: 5 
      },
    ];

    const newEdges: GraphEdge[] = [
      // Internal Structure P1
      { id: 'e1', from: 'p1', to: 'p1_m', label: 'Extracts', details: 'Identifying specific experimental protocols.', color: '#10b981', type: 'solid', appearsAtStep: 1 },
      { id: 'e2', from: 'p1', to: 'p1_c', label: 'Asserts', details: 'Extracting primary scientific claims.', color: '#fbbf24', type: 'solid', appearsAtStep: 1 },
      { id: 'e3', from: 'p1', to: 'p1_d', label: 'Utilizes', details: 'Referencing source datasets.', color: '#06b6d4', type: 'solid', appearsAtStep: 2 },
      { id: 'e4', from: 'p1', to: 'p1_l', label: 'Self-Reports', details: 'Extracting author-reported limitations.', color: '#fb7185', type: 'dashed', appearsAtStep: 2 },

      // Internal Structure P2
      { id: 'e5', from: 'p2', to: 'p2_m', label: 'Extracts', details: 'Identifying statistical methods.', color: '#10b981', type: 'solid', appearsAtStep: 1 },
      { id: 'e6', from: 'p2', to: 'p2_c', label: 'Asserts', details: 'Extracting key findings.', color: '#fbbf24', type: 'solid', appearsAtStep: 1 },
      { id: 'e7', from: 'p2', to: 'p2_d', label: 'Utilizes', details: 'Referencing longitudinal data.', color: '#06b6d4', type: 'solid', appearsAtStep: 2 },
      { id: 'e8', from: 'p2', to: 'p2_l', label: 'Self-Reports', details: 'Extracting environmental constraints.', color: '#fb7185', type: 'dashed', appearsAtStep: 2 },

      // Cross Connections
      { id: 'e9', from: 'p1_c', to: 'conflict', label: 'Conflicts With', details: 'Found opposing conclusion on core metric.', color: '#ef4444', type: 'dashed', appearsAtStep: 3 },
      { id: 'e10', from: 'p2_c', to: 'conflict', label: 'Conflicts With', details: 'Found opposing conclusion on core metric.', color: '#ef4444', type: 'dashed', appearsAtStep: 3 },
      { id: 'e11', from: 'p1_m', to: 'link', label: 'Resembles', details: 'High similarity in experimental setup.', color: '#60a5fa', type: 'dotted', appearsAtStep: 3 },
      { id: 'e12', from: 'p2_m', to: 'link', label: 'Resembles', details: 'High similarity in experimental setup.', color: '#60a5fa', type: 'dotted', appearsAtStep: 3 },

      // Synthesis
      { id: 'e13', from: 'conflict', to: 'gap', label: 'Informs', details: 'Contradiction suggests unexplored variable.', color: '#ffffff', type: 'solid', appearsAtStep: 4 },
      { id: 'e14', from: 'link', to: 'hypo', label: 'Supports', details: 'Semantic link strengthens hypothesis foundation.', color: '#60a5fa', type: 'solid', appearsAtStep: 4 },
      { id: 'e15', from: 'p1', to: 'gap', label: 'Context', details: 'Paper A provides baseline context.', color: '#ffffff', type: 'dashed', appearsAtStep: 4 },
      { id: 'e16', from: 'p2', to: 'gap', label: 'Context', details: 'Paper B provides comparative context.', color: '#ffffff', type: 'dashed', appearsAtStep: 4 },
      
      // Final Synthesis
      { id: 'e17', from: 'gap', to: 'hypo', label: 'Generates', details: 'Hypothesis emerges from the identified gap.', color: '#f0abfc', type: 'solid', appearsAtStep: 5 },
    ];

    setNodes(newNodes);
    setEdges(newEdges);
  }, [papers]);

  const getEdgeStyle = (edge: GraphEdge) => {
    const isVisible = step >= edge.appearsAtStep;
    const isHidden = step >= 5 && (edge.to === 'gap' || edge.from === 'gap');
    
    // Interaction logic
    let opacity = 0.6;
    let width = 1.5;
    
    // If a node or edge is selected/hovered
    const activeNodeId = hoveredNodeId || selectedNodeId;
    const activeEdgeId = hoveredEdgeId || selectedEdgeId;

    if (activeEdgeId === edge.id) {
        opacity = 1;
        width = 3;
    } else if (activeNodeId) {
      // If a node is active, highlight connected edges
      const isConnected = edge.from === activeNodeId || edge.to === activeNodeId;
      if (isConnected) {
        opacity = 1;
        width = 2.5;
      } else {
        opacity = 0.1; // Dim unrelated edges
      }
    } else if (activeEdgeId && activeEdgeId !== edge.id) {
        // If another edge is selected, dim this one
        opacity = 0.1;
    }

    if (!isVisible) return { display: 'none' };
    // Keep gap edges visible for context in step 5, but maybe dim them
    if (isHidden && edge.to !== 'hypo' && edge.from !== 'hypo') return { display: 'none' }; 

    return { opacity, width };
  };

  const getNodeState = (node: GraphNode) => {
    const isVisible = step >= node.appearsAtStep;
    const isGapHidden = node.id === 'gap' && step >= 5; // Maybe keep Gap visible as it feeds Hypothesis
    const isHypothesis = node.id === 'hypo';
    
    // If something is selected/hovered
    const activeNodeId = hoveredNodeId || selectedNodeId;
    const activeEdgeId = hoveredEdgeId || selectedEdgeId;
    
    // Default opacity
    let opacity = isVisible ? 1 : 0;
    
    // Dimming logic
    if (activeNodeId && opacity > 0) {
      // Find connections
      const isConnected = edges.some(e => 
        (e.from === activeNodeId && e.to === node.id) || 
        (e.to === activeNodeId && e.from === node.id)
      );
      const isSelf = node.id === activeNodeId;
      
      if (!isSelf && !isConnected) {
        opacity = 0.2;
      }
    } else if (activeEdgeId && opacity > 0) {
        // If an edge is active, only show connected nodes
        const activeEdge = edges.find(e => e.id === activeEdgeId);
        if (activeEdge) {
            if (activeEdge.from !== node.id && activeEdge.to !== node.id) {
                opacity = 0.2;
            }
        }
    }

    let scale = isVisible ? 1 : 0;
    if (isHypothesis) scale = step >= 5 ? 1.5 : 0;
    
    // Hover scale effect
    if (node.id === activeNodeId) scale *= 1.1;

    return { opacity, scale };
  };

  const handleContainerClick = () => {
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
  };

  return (
    <div 
        className="w-full h-[400px] md:h-[500px] relative bg-slate-900/50 rounded-3xl border border-slate-800 overflow-hidden backdrop-blur-sm shadow-inner select-none"
        onClick={handleContainerClick}
    >
      {/* Grid Background */}
      <div 
        className="absolute inset-0 opacity-20 pointer-events-none transition-transform duration-700"
        style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, #475569 1px, transparent 0)`,
            backgroundSize: '40px 40px',
            transform: selectedNodeId ? 'scale(1.05)' : 'scale(1)'
        }}
      />
      
      {/* Edges Layer (SVG) */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
            </marker>
        </defs>
        {edges.map((edge) => {
            const fromNode = nodes.find(n => n.id === edge.from);
            const toNode = nodes.find(n => n.id === edge.to);
            if (!fromNode || !toNode) return null;

            const { opacity, width, display } = getEdgeStyle(edge);
            if (display === 'none') return null;

            const isActive = hoveredEdgeId === edge.id || selectedEdgeId === edge.id;

            return (
                <g key={edge.id} className="transition-all duration-300 ease-out">
                     {/* Visual Line */}
                    <line
                        x1={`${fromNode.x}%`}
                        y1={`${fromNode.y}%`}
                        x2={`${toNode.x}%`}
                        y2={`${toNode.y}%`}
                        stroke={edge.color}
                        strokeWidth={width}
                        strokeDasharray={edge.type === 'dashed' ? '5,5' : edge.type === 'dotted' ? '2,2' : '0'}
                        opacity={opacity}
                        className="transition-all duration-300"
                    />
                    
                    {/* Invisible Hit Area Line for interaction */}
                    <line
                        x1={`${fromNode.x}%`}
                        y1={`${fromNode.y}%`}
                        x2={`${toNode.x}%`}
                        y2={`${toNode.y}%`}
                        stroke="transparent"
                        strokeWidth={20}
                        style={{ pointerEvents: 'auto', cursor: 'pointer' }}
                        onMouseEnter={() => setHoveredEdgeId(edge.id)}
                        onMouseLeave={() => setHoveredEdgeId(null)}
                        onClick={(e) => {
                            e.stopPropagation();
                            setSelectedEdgeId(isActive ? null : edge.id);
                            setSelectedNodeId(null); // Deselect node if edge is clicked
                        }}
                    />
                </g>
            );
        })}
      </svg>
      
      {/* Edge Tooltips */}
      {edges.map((edge) => {
         const fromNode = nodes.find(n => n.id === edge.from);
         const toNode = nodes.find(n => n.id === edge.to);
         if (!fromNode || !toNode) return null;
         
         const isHovered = hoveredEdgeId === edge.id;
         const isSelected = selectedEdgeId === edge.id;
         
         if (!isHovered && !isSelected) return null;
         const { display } = getEdgeStyle(edge);
         if (display === 'none') return null;

         // Calculate midpoint
         const mx = (fromNode.x + toNode.x) / 2;
         const my = (fromNode.y + toNode.y) / 2;

         return (
             <div
                 key={`tooltip-${edge.id}`}
                 className="absolute z-30 pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
                 style={{ left: `${mx}%`, top: `${my}%` }}
             >
                 <div className="bg-slate-900/95 border border-slate-600 backdrop-blur-xl rounded-lg p-2 shadow-2xl animate-in zoom-in-90 fade-in duration-200">
                     <div className="flex items-center gap-2 mb-1">
                         <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Relationship</span>
                         {isSelected && <XCircle size={10} className="text-slate-500" />}
                     </div>
                     <div className="flex items-center gap-1 text-xs font-semibold text-white mb-1">
                         <span style={{ color: edge.color }}>{edge.label}</span>
                         <ArrowRight size={10} className="text-slate-600" />
                     </div>
                     <p className="text-[10px] text-slate-300 w-32 leading-tight">
                         {edge.details}
                     </p>
                 </div>
             </div>
         );
      })}

      {/* Nodes Layer */}
      {nodes.map((node) => {
         const { opacity, scale } = getNodeState(node);
         const isPulsing = (step === node.appearsAtStep) || node.id === 'hypo';
         const isSelected = selectedNodeId === node.id;

         return (
            <div
                key={node.id}
                className="graph-node absolute z-20 flex flex-col items-center justify-center w-32 cursor-pointer transition-all duration-500 ease-out"
                style={{
                    left: `${node.x}%`,
                    top: `${node.y}%`,
                    opacity,
                    transform: `translate(-50%, -50%) scale(${scale})`,
                    pointerEvents: opacity < 0.1 ? 'none' : 'auto'
                }}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId(isSelected ? null : node.id);
                  setSelectedEdgeId(null); // Deselect edge if node is clicked
                }}
            >
                <div className="relative flex items-center justify-center group">
                    {/* Hexagon Background */}
                    <Hexagon 
                        className={`
                          transition-all duration-300
                          ${node.id === 'hypo' ? 'w-24 h-24 text-purple-600 fill-purple-900/50' : 'w-14 h-14 text-slate-800 fill-slate-900'} 
                          ${isSelected ? 'stroke-white stroke-2 drop-shadow-glow' : ''}
                        `} 
                        strokeWidth={isSelected ? 2 : 1.5}
                    />
                    
                    {/* Icon */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        <node.icon 
                            className={`
                              ${node.color} 
                              ${node.id === 'hypo' ? 'w-10 h-10' : 'w-6 h-6'}
                              transition-transform duration-300 group-hover:scale-110
                            `} 
                        />
                    </div>

                    {/* Glowing effect for active nodes */}
                    {(isPulsing || isSelected) && (
                         <div className={`absolute inset-0 rounded-full blur-xl opacity-40 bg-current ${node.color} animate-pulse`} />
                    )}

                    {/* Info Indicator on Hover */}
                    <div className="absolute -top-1 -right-1 bg-slate-800 rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity border border-slate-600">
                      <Info size={10} className="text-white" />
                    </div>
                </div>
                
                {/* Label */}
                <div className={`
                  mt-2 px-2 py-1 rounded bg-slate-950/90 backdrop-blur text-[10px] font-mono border border-slate-800 
                  ${node.color} text-center shadow-lg transition-all duration-300
                  ${isSelected ? 'scale-110 border-white/30 bg-slate-900' : ''}
                `}>
                    {node.label}
                </div>

                {/* Detailed Tooltip - Shows on Hover or Select */}
                {((hoveredNodeId === node.id) || (selectedNodeId === node.id)) && (
                  <div className={`
                    absolute top-full mt-3 w-48 p-3 rounded-xl bg-slate-900/95 border border-slate-700 backdrop-blur-xl shadow-2xl z-50
                    animate-in fade-in zoom-in-95 duration-200 flex flex-col gap-1
                  `}>
                    <div className="flex justify-between items-start mb-1">
                      <span className={`text-[10px] font-bold uppercase tracking-wider ${node.color}`}>{node.type}</span>
                      {selectedNodeId === node.id && <XCircle size={12} className="text-slate-500" />}
                    </div>
                    <p className="text-xs text-slate-300 leading-snug">
                      {node.details}
                    </p>
                    {node.sourcePaperIndex !== undefined && (
                       <div className="mt-2 text-[9px] text-slate-500 font-mono border-t border-slate-800 pt-1">
                          Ref: Paper {node.sourcePaperIndex + 1}
                       </div>
                    )}
                  </div>
                )}
            </div>
         );
      })}

      {/* Helper Text */}
      <div className="absolute top-4 left-4 text-[10px] text-slate-500 font-mono opacity-60">
        Hover nodes or lines for details • Click to focus
      </div>

      {/* Status Overlay */}
      {showStatus && (
        <div className="absolute bottom-4 left-0 right-0 flex justify-center z-20 pointer-events-none">
            <div className="bg-slate-900/90 backdrop-blur border border-slate-700 rounded-full px-4 py-2 flex items-center gap-3 shadow-xl">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-slate-300 font-mono uppercase tracking-wider">
                  {step === 0 && "Parsing Knowledge Graph..."}
                  {step === 1 && "Extracting Claims & Methods..."}
                  {step === 2 && "Analyzing Datasets & Evidence..."}
                  {step === 3 && "Identifying Cross-Paper Connections..."}
                  {step === 4 && "Locating Research Gap..."}
                  {step === 5 && "Synthesizing Artifact..."}
              </span>
            </div>
        </div>
      )}
    </div>
  );
};