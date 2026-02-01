import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, MessageSquare, Settings } from 'lucide-react';
import { AGUIRenderer } from './components/AGUIRenderer';
import { SkeletonLoader } from './components/SkeletonLoader';
import { SettingsModal } from './components/SettingsModal';
import { generateAGUIResponse } from './services/llamacppService';
import { ChatMessage } from './types';

// Greeting default questions
const DEFAULT_QUESTIONS = [
  "請使用 Markdown 介紹 AG-UI (Markdown)",
  "顯示一個關於系統維護的警告卡片 (InfoCard)",
  "列出使用到的技術棧清單 (DataList)",
  "說明如何啟動開發伺服器的步驟 (StepProcess)",
  "請用表格比較 React 和 Vue 的差異 (Table)"
];

// Full palette of available colors




const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Persistence State
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('agui_theme_mode') === 'dark';
    }
    return false;
  });

  const [themeColor, setThemeColor] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('agui_theme_color') || 'indigo';
    }
    return 'indigo';
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Apply Dark Mode Class
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('agui_theme_mode', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  useEffect(() => {
    localStorage.setItem('agui_theme_color', themeColor);
  }, [themeColor]);

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
  };

  const renderSuggestions = (suggestions: string[]) => {
    if (!suggestions || suggestions.length === 0) return null;

    return (
      <div className="mt-4 flex flex-wrap gap-2 animate-fadeIn">
        <div className="w-full text-xs font-medium text-slate-400 mb-1 flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          Suggested Questions
        </div>
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onQuestionClick(s)}
            className={`text-sm px-4 py-2 bg-${themeColor}-50 hover:bg-${themeColor}-100 dark:bg-${themeColor}-900/20 dark:hover:bg-${themeColor}-900/30 text-${themeColor}-700 dark:text-${themeColor}-300 rounded-full border border-${themeColor}-200 dark:border-${themeColor}-800 transition-colors duration-200 text-left`}
          >
            {s}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-app-dark flex flex-col transition-colors duration-300">
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        isDarkMode={isDarkMode}
        toggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        themeColor={themeColor}
        setThemeColor={setThemeColor}
      />

      {/* Header */}
      <header className="bg-white dark:bg-app-card border-b border-slate-200 dark:border-app-border sticky top-0 z-30 shadow-sm transition-colors duration-300">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 bg-gradient-to-br from-${themeColor}-500 to-${themeColor}-700 rounded-xl flex items-center justify-center text-white shadow-md`}>
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 dark:text-slate-100 leading-tight">AG-UI Q&A Assistant</h1>
              {/* <p className="text-xs text-slate-500 dark:text-slate-400">Powered by Google Gemini & ADK</p> */}
            </div>
          </div>
          <button
            onClick={() => setShowSettings(true)}
            className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-700 text-slate-500 dark:text-slate-400 transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-3xl mx-auto p-4 pb-32">
        {messages.length === 0 ? (
          // Greeting Page
          <div className="h-full flex flex-col items-center justify-center py-20 animate-fadeIn">
            <div className="bg-white dark:bg-app-card p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-app-border max-w-lg text-center transition-colors duration-300">
              <div className={`w-16 h-16 bg-${themeColor}-50 dark:bg-${themeColor}-900/20 text-${themeColor}-600 dark:text-${themeColor}-400 rounded-2xl flex items-center justify-center mx-auto mb-6`}>
                <MessageSquare className="w-8 h-8" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-3">Welcome to Smart Q&A</h2>
              <p className="text-slate-600 dark:text-slate-400 mb-8">
                I am your AI assistant. I will use the AG-UI protocol to answer your questions in a structured way (charts, lists, cards). Try these questions:
              </p>

              <div className="flex flex-col gap-3">
                {DEFAULT_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => onQuestionClick(q)}
                    className={`w-full text-left px-5 py-3 rounded-xl bg-slate-50 dark:bg-zinc-800/50 hover:bg-slate-100 dark:hover:bg-zinc-700 border border-slate-200 dark:border-app-border text-slate-700 dark:text-slate-200 hover:border-${themeColor}-300 hover:text-${themeColor}-700 dark:hover:text-${themeColor}-300 transition-all duration-200 group flex justify-between items-center`}
                  >
                    <span>{q}</span>
                    <Sparkles className={`w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-${themeColor}-500`} />
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
                <div className={`w-10 h-10 rounded-full shrink-0 flex items-center justify-center shadow-sm border ${msg.role === 'user' ? 'bg-white dark:bg-app-card border-slate-200 dark:border-app-border' : `bg-gradient-to-br from-${themeColor}-500 to-${themeColor}-700 border-transparent text-white`}`}>
                  {msg.role === 'user' ? <User className="w-5 h-5 text-slate-600 dark:text-slate-400" /> : <Sparkles className="w-5 h-5" />}
                </div>

                {/* Content Bubble */}
                <div className={`flex flex-col max-w-[85%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`rounded-2xl px-6 py-4 shadow-sm ${msg.role === 'user' ? 'bg-white dark:bg-app-card border border-slate-200 dark:border-app-border text-slate-800 dark:text-slate-200 rounded-tr-sm' : 'bg-white dark:bg-app-card border border-slate-200 dark:border-app-border rounded-tl-sm'} transition-colors duration-300`}>
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    ) : (
                      msg.data && <AGUIRenderer components={msg.data.components} themeColor={themeColor} />
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

            {isLoading && <SkeletonLoader themeColor={themeColor} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Area */}
      <div className="sticky bottom-0 bg-white/80 dark:bg-[#1e1e1e]/80 backdrop-blur-md border-t border-slate-200 dark:border-app-border p-4 shadow-lg z-40 transition-colors duration-300">
        <div className="max-w-3xl mx-auto relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSendMessage(inputValue)}
            placeholder="Type your question here..."
            className={`w-full pl-6 pr-14 py-4 rounded-full border border-slate-300 dark:border-app-border bg-white dark:bg-app-card text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-${themeColor}-500 focus:border-transparent shadow-sm transition-all`}
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            className={`absolute right-2 top-2 p-2 bg-${themeColor}-600 hover:bg-${themeColor}-700 disabled:bg-slate-300 dark:disabled:bg-zinc-700 text-white rounded-full transition-colors duration-200 shadow-md`}
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