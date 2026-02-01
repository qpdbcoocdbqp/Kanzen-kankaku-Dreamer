import { AgentState } from "@/lib/types";
import { useState } from "react";

export interface StructuredOutputPreviewProps {
  state: AgentState;
  setState: (state: AgentState) => void;
  themeColor: string;
}

export function StructuredOutputPreview({ 
  state, 
  setState, 
  themeColor 
}: StructuredOutputPreviewProps) {
  const [viewMode, setViewMode] = useState<'json' | 'formatted'>('formatted');

  const renderStructuredData = (data: any) => {
    if (!data) return null;

    if (viewMode === 'json') {
      return (
        <pre className="text-sm text-white bg-black/20 p-4 rounded-lg overflow-auto max-h-96">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
    }

    // Formatted view
    if (typeof data === 'object' && data !== null) {
      return (
        <div className="space-y-3">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="bg-white/15 p-3 rounded-lg">
              <div className="font-semibold text-white capitalize mb-1">
                {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
              </div>
              <div className="text-gray-200">
                {typeof value === 'object' ? 
                  JSON.stringify(value, null, 2) : 
                  String(value)
                }
              </div>
            </div>
          ))}
        </div>
      );
    }

    return (
      <div className="text-white">
        {String(data)}
      </div>
    );
  };

  return (
    <div className="bg-white/20 backdrop-blur-md p-6 rounded-2xl shadow-xl w-full h-full overflow-hidden flex flex-col m-4">
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <h1 className="text-3xl font-bold text-white">Structured Output Preview</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('formatted')}
            className={`px-3 py-1 rounded-lg text-sm transition-all ${
              viewMode === 'formatted' 
                ? 'bg-white text-gray-800' 
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            Formatted
          </button>
          <button
            onClick={() => setViewMode('json')}
            className={`px-3 py-1 rounded-lg text-sm transition-all ${
              viewMode === 'json' 
                ? 'bg-white text-gray-800' 
                : 'bg-white/20 text-white hover:bg-white/30'
            }`}
          >
            JSON
          </button>
        </div>
      </div>
      
      <hr className="border-white/20 mb-4 flex-shrink-0" />
      
      <div className="flex-1 overflow-auto min-h-0">
        {state.structuredData || state.lastOutput ? (
          <div className="space-y-4">
            {state.structuredData && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Current Data</h3>
                {renderStructuredData(state.structuredData)}
              </div>
            )}
            {state.lastOutput && state.lastOutput !== state.structuredData && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Last Output</h3>
                {renderStructuredData(state.lastOutput)}
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-white/80">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-lg mb-2">No structured data yet</p>
              <p className="text-sm">Ask the assistant to generate some structured data!</p>
            </div>
          </div>
        )}
      </div>
      
      {(state.structuredData || state.lastOutput) && (
        <div className="mt-4 pt-4 border-t border-white/20 flex-shrink-0">
          <button
            onClick={() => setState({
              ...state,
              structuredData: null,
              lastOutput: null,
            })}
            className="bg-red-500/80 hover:bg-red-600/80 text-white px-4 py-2 rounded-lg transition-all"
          >
            Clear All Data
          </button>
        </div>
      )}
    </div>
  );
}