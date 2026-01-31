import React, { useState, useEffect } from 'react';
import { Settings, X, Moon, Sun, Check, RefreshCw } from 'lucide-react';

// Full palette of available colors
const ALL_COLORS = [
    'indigo', 'blue', 'sky', 'cyan', 'teal',
    'emerald', 'green', 'lime', 'yellow', 'amber',
    'orange', 'red', 'rose', 'pink', 'fuchsia',
    'purple', 'violet', 'slate', 'zinc', 'neutral', 'stone'
];

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    isDarkMode: boolean;
    toggleDarkMode: () => void;
    themeColor: string;
    setThemeColor: (color: string) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
    isOpen,
    onClose,
    isDarkMode,
    toggleDarkMode,
    themeColor,
    setThemeColor
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
