import { GoogleGenAI } from "@google/genai";

// Initialize the API client for image generation only
// CRITICAL: process.env.API_KEY is guaranteed to be available.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const generateScientificIllustration = async (hypothesisSummary: string): Promise<string | undefined> => {
  const prompt = `
    Create a premium, abstract scientific illustration representing this hypothesis: "${hypothesisSummary}".
    Style: Futuristic, data-driven, ethereal.
    Color Palette: Deep Blue (#1e3a8a), Emerald Green (#10b981), and White glowing accents.
    Composition: Center-focused, 3:4 aspect ratio suitable for a trading card.
    No text in the image. High quality, 3D render style.
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-image", // Nano Banana
      contents: {
        parts: [{ text: prompt }],
      },
      config: {
        // Nano Banana doesn't support advanced imageConfig like size/aspectRatio in the same way Pro does via config object usually,
        // but we can try to guide via prompt. The response format is inlineData.
      },
    });

    // Iterate to find image part
    const parts = response.candidates?.[0]?.content?.parts;
    if (parts) {
      for (const part of parts) {
        if (part.inlineData) {
            return `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`;
        }
      }
    }
    return undefined;
  } catch (error) {
    console.error("Error generating illustration:", error);
    // Return a placeholder if generation fails to keep the UI intact
    return "https://picsum.photos/360/580"; 
  }
};