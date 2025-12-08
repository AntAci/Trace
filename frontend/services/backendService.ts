import { HypothesisArtifact, SourcePaper } from "../types";

// Backend API URL - adjust if needed
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Generate hypothesis using the Trace backend pipeline
 */
export const generateHypothesis = async (papers: SourcePaper[]): Promise<HypothesisArtifact> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/process-papers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        paper_a: {
          title: papers[0].title,
          content: papers[0].content,
        },
        paper_b: {
          title: papers[1].title,
          content: papers[1].content,
        },
        author_wallet: "NXXXX...", // Default wallet, can be made configurable
        use_neofs: true,
        use_x402: false,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const artifact: HypothesisArtifact = await response.json();
    return artifact;
  } catch (error) {
    console.error("Error generating hypothesis from backend:", error);
    throw error;
  }
};




