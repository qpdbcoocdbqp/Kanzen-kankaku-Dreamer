import React from 'react';
import { SurfaceComponent } from '../types';
import { SurfaceRenderer } from './SurfaceRenderer';

interface StagePanelProps {
  surface: SurfaceComponent;
  onClose?: () => void;
  themeColor?: string;
}

export const StagePanel: React.FC<StagePanelProps> = ({ surface, onClose, themeColor = 'indigo' }) => {
  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-slate-50/50 to-slate-50 dark:from-zinc-800/50 dark:to-zinc-800/30 rounded-2xl border border-slate-200 dark:border-app-border overflow-hidden">
      {/* Stage Header */}
      <div className="border-b border-slate-200 dark:border-app-border px-6 py-4 flex items-center justify-between bg-white/50 dark:bg-zinc-800/30">
        <div className="flex-1 pr-4">
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">
            {surface.title || 'Visual Output'}
          </h2>
          {surface.description && (
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              {surface.description}
            </p>
          )}
        </div>
      </div>

      {/* Surface Renderer */}
      <div className="flex-1 overflow-hidden p-4">
        <SurfaceRenderer data={surface} themeColor={themeColor} />
      </div>
    </div>
  );
};
