import React, { useState } from 'react';
import { Copy, Eye, Code, FileJson } from 'lucide-react';
import { SurfaceComponent, SurfaceKind } from '../types';

interface SurfaceRendererProps {
  data: SurfaceComponent;
  themeColor?: string;
}

type TabType = 'preview' | 'html' | 'css' | 'payload';

export const SurfaceRenderer: React.FC<SurfaceRendererProps> = ({ data, themeColor = 'indigo' }) => {
  const [activeTab, setActiveTab] = useState<TabType>('preview');
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string | undefined) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderPreview = () => {
    if (data.kind === SurfaceKind.HTML && data.html) {
      return (
        <div className="w-full h-full overflow-auto bg-white">
          <iframe
            srcDoc={data.html}
            className="w-full h-full border-0"
            title="HTML Preview"
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      );
    }

    if (data.kind === SurfaceKind.SVG && data.svg) {
      return (
        <div className="w-full h-full flex items-center justify-center bg-white overflow-auto p-8">
          <div dangerouslySetInnerHTML={{ __html: data.svg }} />
        </div>
      );
    }

    if (data.kind === SurfaceKind.MARKDOWN && data.markdown) {
      return (
        <div className="w-full h-full overflow-auto p-8 bg-white prose max-w-none">
          {/* Markdown would be rendered by ReactMarkdown in a real implementation */}
          <pre className="whitespace-pre-wrap break-words">{data.markdown}</pre>
        </div>
      );
    }

    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50 text-slate-400">
        No preview available
      </div>
    );
  };

  const renderCodeView = (code: string | undefined, language: string) => {
    if (!code) {
      return <div className="text-slate-400 p-4">No {language} content</div>;
    }

    return (
      <pre className="bg-slate-950 text-slate-100 p-4 overflow-x-auto text-sm font-mono rounded-lg">
        <code>{code}</code>
      </pre>
    );
  };

  return (
    <div className="flex flex-col h-full rounded-2xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card shadow-sm">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-app-border px-5 py-4 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-800 dark:text-slate-100 text-base">
            {data.title || 'Surface Render'}
          </h3>
          {data.description && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{data.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className={`px-2 py-1 rounded-full bg-${themeColor}-50 dark:bg-${themeColor}-900/20 text-${themeColor}-700 dark:text-${themeColor}-300 font-medium`}>
            {data.kind}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-app-border px-4 py-3 flex gap-2 overflow-x-auto bg-slate-50/50 dark:bg-zinc-800/30">
        <button
          onClick={() => setActiveTab('preview')}
          className={`px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-colors flex items-center gap-1 ${
            activeTab === 'preview'
              ? `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-700 dark:text-${themeColor}-300`
              : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-zinc-700'
          }`}
        >
          <Eye className="w-4 h-4" />
          Preview
        </button>
        {data.html && (
          <button
            onClick={() => setActiveTab('html')}
            className={`px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-colors flex items-center gap-1 ${
              activeTab === 'html'
                ? `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-700 dark:text-${themeColor}-300`
                : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-zinc-700'
            }`}
          >
            <Code className="w-4 h-4" />
            HTML
          </button>
        )}
        {data.css && (
          <button
            onClick={() => setActiveTab('css')}
            className={`px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-colors flex items-center gap-1 ${
              activeTab === 'css'
                ? `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-700 dark:text-${themeColor}-300`
                : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-zinc-700'
            }`}
          >
            <Code className="w-4 h-4" />
            CSS
          </button>
        )}
        <button
          onClick={() => setActiveTab('payload')}
          className={`px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-colors flex items-center gap-1 ${
            activeTab === 'payload'
              ? `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-700 dark:text-${themeColor}-300`
              : 'text-slate-600 dark:text-slate-400 hover:bg-white dark:hover:bg-zinc-700'
          }`}
        >
          <FileJson className="w-4 h-4" />
          Payload
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'preview' && renderPreview()}

        {activeTab === 'html' && (
          <div className="h-full overflow-auto p-4 relative">
            <button
              onClick={() => copyToClipboard(data.html)}
              className={`absolute top-4 right-4 p-2 rounded-lg text-sm font-medium transition-all z-10 ${
                copied
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                  : `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-600 dark:text-${themeColor}-400 hover:bg-${themeColor}-200 dark:hover:bg-${themeColor}-900/50`
              }`}
            >
              <Copy className="w-4 h-4 inline mr-1" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {renderCodeView(data.html, 'html')}
          </div>
        )}

        {activeTab === 'css' && (
          <div className="h-full overflow-auto p-4 relative">
            <button
              onClick={() => copyToClipboard(data.css)}
              className={`absolute top-4 right-4 p-2 rounded-lg text-sm font-medium transition-all z-10 ${
                copied
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                  : `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-600 dark:text-${themeColor}-400 hover:bg-${themeColor}-200 dark:hover:bg-${themeColor}-900/50`
              }`}
            >
              <Copy className="w-4 h-4 inline mr-1" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {renderCodeView(data.css, 'css')}
          </div>
        )}

        {activeTab === 'payload' && (
          <div className="h-full overflow-auto p-4 relative">
            <button
              onClick={() => copyToClipboard(JSON.stringify(data, null, 2))}
              className={`absolute top-4 right-4 p-2 rounded-lg text-sm font-medium transition-all z-10 ${
                copied
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                  : `bg-${themeColor}-100 dark:bg-${themeColor}-900/30 text-${themeColor}-600 dark:text-${themeColor}-400 hover:bg-${themeColor}-200 dark:hover:bg-${themeColor}-900/50`
              }`}
            >
              <Copy className="w-4 h-4 inline mr-1" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {renderCodeView(JSON.stringify(data, null, 2), 'json')}
          </div>
        )}
      </div>
    </div>
  );
};
