import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, MessageSquare, Settings } from 'lucide-react';
import { AGUIRenderer } from './components/AGUIRenderer';
import { SkeletonLoader } from './components/SkeletonLoader';
import { SettingsModal } from './components/SettingsModal';
import { generateAGUIResponse } from './services/llamacppService';
import { AGUIResponse, ChatMessage, ComponentType } from './types';

// Greeting default questions
const DEFAULT_QUESTIONS = [
  "請使用 Markdown 介紹 AG-UI",
  "顯示一個關於系統維護的警告卡片",
  "列出使用到的技術棧清單",
  "說明如何啟動開發伺服器的步驟",
  "請用表格比較 React 和 Vue 的差異"
];

/** One-click prompts for exercising each AG-UI component shape returned via emit_agui_response (tool call). */
const TOOL_FORMAT_TEST_PROMPTS: { label: string; prompt: string }[] = [
  {
    label: 'Markdown',
    prompt:
      '請透過 emit_agui_response 回覆：components 至少含一個 type 為 markdown，繁體中文簡述 AG-UI，並在 markdown 內含 ```mermaid 流程圖程式碼區塊。suggestions 給 0～2 則。'
  },
  {
    label: 'InfoCard',
    prompt:
      '請透過 emit_agui_response：僅使用一個 info_card，variant 為 warning，標題與 description 為繁體中文的系統維護公告。suggestions 可為空。'
  },
  {
    label: 'DataList',
    prompt:
      '請透過 emit_agui_response：使用 data_list，列出至少四項「標籤／值」的繁體中文技術棧或相依套件範例（title 可選）。'
  },
  {
    label: 'StepProcess',
    prompt:
      '請透過 emit_agui_response：使用 step_process，以繁體中文列出在本機啟動此專案（npm install、後端、前端）的三個以上步驟。'
  },
  {
    label: 'Table',
    prompt:
      '請透過 emit_agui_response：使用 table，繁體中文表頭與至少兩列，比較 React 與 Vue（或任意兩項前端框架）。'
  },
  {
    label: 'StatGrid',
    prompt:
      '請透過 emit_agui_response：使用 stat_grid，title 為繁體中文營運摘要，至少三個 StatItem（含 label、value、description）。'
  },
  {
    label: 'CodeBlock',
    prompt:
      '請透過 emit_agui_response：使用 code_block，language 為 typescript，content 為一段簡短的 fetch 呼叫 /chat 的範例程式碼（字串即可）。'
  },
  {
    label: 'ActionGroup',
    prompt:
      '請透過 emit_agui_response：使用 action_group，至少兩個項目（label、action、description 皆繁體中文），title 說明後續可執行動作。'
  },
  {
    label: '混合',
    prompt:
      '請透過 emit_agui_response：components 依序包含 markdown（簡短前言）、data_list（兩項）、info_card（variant success），suggestions 給兩則繁體中文追問。'
  }
];

const SAMPLE_MODEL_DATA: AGUIResponse = {
  components: [
    {
      type: ComponentType.MARKDOWN,
      content: [
        '已建立客服儀表板首頁草稿。',
        '',
        '```mermaid',
        'flowchart LR',
        '  U[User] --> A[Agent]',
        '  A --> J[Structured JSON]',
        '  J --> C[Chat Components]',
        '```'
      ].join('\n')
    },
    {
      type: ComponentType.STAT_GRID,
      title: '今日營運摘要',
      items: [
        { label: '今日案件', value: '184', description: '較昨日增加 12%' },
        { label: '平均首響時間', value: '4m', description: '維持在 SLA 內' },
        { label: '自動解決率', value: '62%', description: '知識庫與自動回覆生效中' }
      ]
    },
    {
      type: ComponentType.CODE_BLOCK,
      title: 'Surface HTML 範例',
      language: 'html',
      content: '<section class="dashboard-shell">...</section>'
    },
    {
      type: ComponentType.ACTION_GROUP,
      title: '你可以接著做',
      items: [
        { label: '改成管理員視角', action: 'switch-admin-view', description: '調整資訊層級與指標內容' },
        { label: '加入案件趨勢圖', action: 'add-trend-chart', description: '補上 7 日流量與分類走勢' }
      ]
    }
  ],
  suggestions: ['改成管理員視角', '加入案件趨勢圖']
};

const SAMPLE_MODEL_RESPONSE: ChatMessage = {
  id: 'sample-model-response',
  role: 'model',
  timestamp: Date.now(),
  data: SAMPLE_MODEL_DATA
};

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([SAMPLE_MODEL_RESPONSE]);
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
      const history = [...messages, userMsg].map(m => ({
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
        <div className="max-w-3xl mx-auto mb-3">
          <p className="text-[10px] font-medium uppercase tracking-wide text-slate-400 mb-2 px-1">
            Tool 格式測試（emit_agui_response）
          </p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {TOOL_FORMAT_TEST_PROMPTS.map(({ label, prompt }) => (
              <button
                key={label}
                type="button"
                disabled={isLoading}
                onClick={() => handleSendMessage(prompt)}
                className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 disabled:pointer-events-none border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 hover:border-${themeColor}-300 dark:border-app-border dark:bg-zinc-800/80 dark:text-slate-200 dark:hover:bg-zinc-700`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
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
