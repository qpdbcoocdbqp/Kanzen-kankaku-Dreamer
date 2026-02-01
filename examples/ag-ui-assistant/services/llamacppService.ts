// services/geminiService.ts
// Originally it was direct import { GoogleGenAI } ...

export const generateAGUIResponse = async (prompt: string, history: any[]) => {
  // Changed to call your Python backend
  const response = await fetch(import.meta.env.VITE_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: prompt, history: history })
  });

  const data = await response.json();
  return data; // Python backend will return JSON conforming to the AG-UI format
};