import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, MessageSquare, Settings, X, Moon, Sun, Check, RefreshCw } from 'lucide-react';
import { AGUIRenderer } from './components/AGUIRenderer';
import { generateAGUIResponse } from './services/llamacppService';
import { ChatMessage } from './types';

// Greeting default questions
const DEFAULT_QUESTIONS = [
  "如何使用 Google ADK 進行開發？",
  "請解釋 AG-UI 的運作原理。",
  "什麼是結構化輸出 (Structured Output)？"
];

// Full palette of available colors
const ALL_COLORS = [
  'indigo', 'blue', 'sky', 'cyan', 'teal', 
  'emerald', 'green', 'lime', 'yellow', 'amber', 
  'orange', 'red', 'rose', 'pink', 'fuchsia', 
  'purple', 'violet', 'slate', 'zinc', 'neutral', 'stone'
];

const SkeletonLoader = ({ themeColor = 'indigo' }) => (
  <div className="flex gap-4 animate-pulse w-full">
    {/* Avatar Skeleton */}
    <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-app-card shrink-0 border border-slate-100 dark:border-app-border shadow-sm" />
    
    {/* Content Skeleton */}
    <div className="flex flex-col w-full max-w-[85%] items-start">
      <div className="bg-white dark:bg-app-card border border-slate-200 dark:border-app-border rounded-2xl rounded-tl-sm p-6 shadow-sm w-full space-y-6">
        
        {/* Paragraph Skeleton */}
        <div className="space-y-3">
          <div className="h-4 bg-slate-100 dark:bg-zinc-700/50 rounded-md w-[92%]"></div>
          <div className="h-4 bg-slate-100 dark:bg-zinc-700/50 rounded-md w-[98%]"></div>
          <div className="h-4 bg-slate-100 dark:bg-zinc-700/50 rounded-md w-[85%]"></div>
        </div>

        {/* Info Card Skeleton */}
        <div className="border border-slate-100 dark:border-app-border rounded-xl p-4 bg-slate-50/80 dark:bg-zinc-800/30 flex gap-4">
          <div className="w-5 h-5 bg-slate-200 dark:bg-zinc-700 rounded-full shrink-0 mt-1"></div>
          <div className="flex-1 space-y-2">
             <div className="h-4 bg-slate-200 dark:bg-zinc-700 rounded-md w-1/3"></div>
             <div className="h-3 bg-slate-200/70 dark:bg-zinc-700/50 rounded-md w-full"></div>
             <div className="h-3 bg-slate-200/70 dark:bg-zinc-700/50 rounded-md w-5/6"></div>
          </div>
        </div>
      </div>
      
      {/* Suggestions Skeleton */}
      <div className="mt-4 w-full">
         <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 bg-slate-200 dark:bg-zinc-700 rounded-full"></div>
            <div className="h-3 w-16 bg-slate-200 dark:bg-zinc-700 rounded"></div>
         </div>
         <div className="flex flex-wrap gap-2">
            <div className="h-9 bg-white dark:bg-app-card border border-slate-200 dark:border-app-border rounded-full w-48"></div>
         </div>
      </div>
    </div>
  </div>
);

const SettingsModal = ({ 
  isOpen, 
  onClose, 
  isDarkMode, 
  toggleDarkMode, 
  themeColor, 
  setThemeColor 
}: { 
  isOpen: boolean; 
  onClose: () => void;
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  themeColor: string;
  setThemeColor: (color: string) => void;
}) => {
  const [displayColors, setDisplayColors] = useState<string[]>([]);

  // Randomize colors when modal opens
  useEffect(() => {
    if (isOpen) {
      // Shuffle array
      const shuffled = [...ALL_COLORS].sort(() => 0.5 - Math.random());
      // Pick top 12
      setDisplayColors(shuffled.slice(0, 12));
    }
  }, [isOpen]);

  // Refresh colors manually
  const refreshColors = () => {
    const shuffled = [...ALL_COLORS].sort(() => 0.5 - Math.random());
    setDisplayColors(shuffled.slice(0, 12));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative w-full max-w-md bg-white dark:bg-app-card rounded-2xl shadow-xl border border-slate-200 dark:border-app-border overflow-hidden animate-fadeIn">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-app-border flex justify-between items-center bg-slate-50/50 dark:bg-[#2a2a2b]">
          <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Settings className="w-5 h-5 text-slate-500" />
            外觀設定
          </h3>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-700 text-slate-500 dark:text-slate-400 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-8">
          {/* Dark Mode Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-slate-900 dark:text-slate-100 mb-1">深色模式</div>
              <div className="text-sm text-slate-500 dark:text-slate-400">切換應用程式的明暗主題</div>
            </div>
            <button 
              onClick={toggleDarkMode}
              className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-${themeColor}-500 focus:ring-offset-2 ${isDarkMode ? `bg-${themeColor}-600` : 'bg-slate-200'}`}
            >
              <span className={`inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform ${isDarkMode ? 'translate-x-7' : 'translate-x-1'}`}>
                {isDarkMode ? (
                  <Moon className={`w-3.5 h-3.5 absolute top-1.5 left-1.5 text-${themeColor}-600`} />
                ) : (
                  <Sun className="w-3.5 h-3.5 absolute top-1.5 left-1.5 text-amber-500" />
                )}
              </span>
            </button>
          </div>

          {/* Color Picker */}
          <div>
            <div className="flex items-center justify-between mb-3">
               <div className="font-medium text-slate-900 dark:text-slate-100">主題顏色</div>
               <button onClick={refreshColors} className="text-xs flex items-center gap-1 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors">
                 <RefreshCw className="w-3 h-3" /> 隨機更換
               </button>
            </div>
            
            <div className="grid grid-cols-6 gap-3">
              {displayColors.map((color) => (
                <button
                  key={color}
                  onClick={() => setThemeColor(color)}
                  className={`w-10 h-10 rounded-full bg-${color}-500 hover:bg-${color}-400 flex items-center justify-center transition-all hover:scale-110 shadow-sm ring-offset-2 dark:ring-offset-[#252526] ${themeColor === color ? `ring-2 ring-${color}-600` : ''}`}
                  aria-label={`Select ${color} theme`}
                >
                  {themeColor === color && <Check className="w-5 h-5 text-white" />}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-slate-50 dark:bg-[#2a2a2b] px-6 py-4 flex justify-end">
          <button 
            onClick={onClose}
            className={`px-4 py-2 bg-${themeColor}-600 hover:bg-${themeColor}-700 text-white rounded-lg font-medium transition-colors shadow-sm`}
          >
            完成
          </button>
        </div>
      </div>
    </div>
  );
};

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
          建議提問
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
              <h1 className="font-bold text-slate-900 dark:text-slate-100 leading-tight">AG-UI 問答助手</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Powered by Google Gemini & ADK</p>
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
              <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-3">歡迎使用智能問答</h2>
              <p className="text-slate-600 dark:text-slate-400 mb-8">
                我是您的 AI 助手。我會使用 AG-UI 協議，以結構化的方式（圖表、列表、卡片）回答您的問題。請嘗試以下問題：
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
            placeholder="請輸入您的問題..."
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