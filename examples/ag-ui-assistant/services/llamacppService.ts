// services/geminiService.ts
// 原本是直接 import { GoogleGenAI } ...

export const generateAGUIResponse = async (prompt: string, history: any[]) => {
  // 改成呼叫您的 Python 後端
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: prompt, history: history })
  });

  const data = await response.json();
  return data; // Python 後端會回傳符合 AG-UI 格式的 JSON
};