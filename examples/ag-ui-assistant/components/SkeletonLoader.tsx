import React from 'react';

export const SkeletonLoader = ({ themeColor = 'indigo' }: { themeColor?: string }) => (
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
