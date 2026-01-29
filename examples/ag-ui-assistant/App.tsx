import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, MessageSquare } from 'lucide-react';
import { AGUIRenderer } from './components/AGUIRenderer';
import { generateAGUIResponse } from './services/llamacppService';
import { ChatMessage } from './types';

// Greeting default questions
const DEFAULT_QUESTIONS = [
  "如何使用 Google ADK 進行開發？",
  "請解釋 AG-UI 的運作原理。",
  "什麼是結構化輸出 (Structured Output)？"
];

const SkeletonLoader = () => (
  <div className="flex gap-4 animate-pulse w-full">
    {/* Avatar Skeleton */}
    <div className="w-10 h-10 rounded-full bg-slate-200 shrink-0 border border-slate-100 shadow-sm" />

    {/* Content Skeleton */}
    <div className="flex flex-col w-full max-w-[85%] items-start">
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-6 shadow-sm w-full space-y-6">

        {/* Paragraph Skeleton */}
        <div className="space-y-3">
          <div className="h-4 bg-slate-100 rounded-md w-[92%]"></div>
          <div className="h-4 bg-slate-100 rounded-md w-[98%]"></div>
          <div className="h-4 bg-slate-100 rounded-md w-[85%]"></div>
        </div>

        {/* Info Card Skeleton */}
        <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/80 flex gap-4">
          <div className="w-5 h-5 bg-slate-200 rounded-full shrink-0 mt-1"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-slate-200 rounded-md w-1/3"></div>
            <div className="h-3 bg-slate-200/70 rounded-md w-full"></div>
            <div className="h-3 bg-slate-200/70 rounded-md w-5/6"></div>
          </div>
        </div>

        {/* Data List Skeleton */}
        <div className="border border-slate-100 rounded-xl overflow-hidden bg-white">
          <div className="bg-slate-50 px-4 py-3 border-b border-slate-100">
            <div className="h-3 bg-slate-200 rounded w-1/4"></div>
          </div>
          <div className="p-4 space-y-4">
            <div className="flex justify-between items-center">
              <div className="h-3 bg-slate-100 rounded w-1/3"></div>
              <div className="h-3 bg-slate-100 rounded w-1/4"></div>
            </div>
            <div className="h-px bg-slate-50"></div>
            <div className="flex justify-between items-center">
              <div className="h-3 bg-slate-100 rounded w-1/4"></div>
              <div className="h-3 bg-slate-100 rounded w-1/3"></div>
            </div>
          </div>
        </div>
      </div>

      {/* Suggestions Skeleton */}
      <div className="mt-4 w-full">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-3 h-3 bg-slate-200 rounded-full"></div>
          <div className="h-3 w-16 bg-slate-200 rounded"></div>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="h-9 bg-white border border-slate-200 rounded-full w-48"></div>
          <div className="h-9 bg-white border border-slate-200 rounded-full w-36"></div>
        </div>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Prepare history for API (simplified for this demo)
      const history = messages.map(m => ({
        role: m.role,
        parts: [{ text: m.role === 'user' ? m.content! : JSON.stringify(m.data) }]
      }));

      const agUiResponse = await generateAGUIResponse(text, history);

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        data: agUiResponse,
        timestamp: Date.now()
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      console.error("Failed to generate response", error);
    } finally {
      setIsLoading(false);
    }
  };

  const onQuestionClick = (q: string) => {
    setInputValue(q);
    // Optional: Auto send immediately
    // handleSendMessage(q);
  };

  const renderSuggestions = (suggestions: string[]) => {
    if (!suggestions || suggestions.length === 0) return null;

    return (
      <div className="mt-4 flex flex-wrap gap-2 animate-fadeIn">
        <div className="w-full text-xs font-medium text-slate-400 mb-1 flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          建議提問
        </div>
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onQuestionClick(s)}
            className="text-sm px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-full border border-indigo-200 transition-colors duration-200 text-left"
          >
            {s}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white shadow-md">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-slate-900 leading-tight">AG-UI 問答助手</h1>
            <p className="text-xs text-slate-500">Powered by Google Gemini & ADK</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-3xl mx-auto p-4 pb-32">
        {messages.length === 0 ? (
          // Greeting Page
          <div className="h-full flex flex-col items-center justify-center py-20 animate-fadeIn">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 max-w-lg text-center">
              <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-8 h-8" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-3">歡迎使用智能問答</h2>
              <p className="text-slate-600 mb-8">
                我是您的 AI 助手。我會使用 AG-UI 協議，以結構化的方式（圖表、列表、卡片）回答您的問題。請嘗試以下問題：
              </p>

              <div className="flex flex-col gap-3">
                {DEFAULT_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => onQuestionClick(q)}
                    className="w-full text-left px-5 py-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 hover:border-indigo-300 hover:text-indigo-700 transition-all duration-200 group flex justify-between items-center"
                  >
                    <span>{q}</span>
                    <Sparkles className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-indigo-500" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Chat Stream
          <div className="space-y-8">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-full shrink-0 flex items-center justify-center shadow-sm border ${msg.role === 'user' ? 'bg-white border-slate-200' : 'bg-gradient-to-br from-indigo-500 to-purple-600 border-transparent text-white'}`}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-slate-600" /> : <Sparkles className="w-5 h-5" />}
                </div>

                {/* Content Bubble */}
                <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`rounded-2xl px-6 py-4 shadow-sm ${msg.role === 'user' ? 'bg-white border border-slate-200 text-slate-800 rounded-tr-sm' : 'bg-white border border-slate-200 rounded-tl-sm'}`}>
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    ) : (
                      msg.data && <AGUIRenderer components={msg.data.components} />
                    )}
                  </div>

                  {/* Suggestions (Only for bot messages) */}
                  {msg.role === 'model' && msg.data?.suggestions && (
                    renderSuggestions(msg.data.suggestions)
                  )}

                  <span className="text-xs text-slate-400 mt-2 px-1">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && <SkeletonLoader />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Area */}
      <div className="sticky bottom-0 bg-white/80 backdrop-blur-md border-t border-slate-200 p-4 shadow-lg z-40">
        <div className="max-w-3xl mx-auto relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSendMessage(inputValue)}
            placeholder="請輸入您的問題..."
            className="w-full pl-6 pr-14 py-4 rounded-full border border-slate-300 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm transition-all"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            className="absolute right-2 top-2 p-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-full transition-colors duration-200 shadow-md"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="max-w-3xl mx-auto mt-2 text-center">
          <p className="text-[10px] text-slate-400">AG-UI Demo Interface • Generated by Gemini</p>
        </div>
      </div>
    </div>
  );
};

export default App;