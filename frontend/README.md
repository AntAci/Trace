<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1xG2c6tQudtitutP86YPYoinIVaET9tDw

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key (for image generation only)
3. Set `VITE_API_URL` in `.env.local` to your Trace backend API URL (default: `http://localhost:8000`)
4. **Start the backend API server first:**
   ```bash
   # From project root (../)
   python api_server.py
   # Or: uvicorn api_server:app --reload --port 8000
   ```
5. Run the app:
   `npm run dev`

## Backend Integration

This frontend now uses the **Trace backend pipeline** (Python) for hypothesis generation instead of Gemini. The backend API is located at `../api_server.py`.

- **Hypothesis Generation:** Calls Trace backend API (`POST /api/process-papers`)
- **Image Generation:** Still uses Gemini API (optional)

Make sure the backend server is running before using the frontend!
