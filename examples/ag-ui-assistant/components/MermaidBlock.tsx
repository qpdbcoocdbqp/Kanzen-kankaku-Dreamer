import React, { useEffect, useId, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  securityLevel: 'strict',
  theme: 'default',
});

interface MermaidBlockProps {
  chart: string;
  fallback?: React.ReactNode;
}

export const MermaidBlock: React.FC<MermaidBlockProps> = ({ chart, fallback }) => {
  const reactId = useId();
  const [svg, setSvg] = useState<string | null>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const renderChart = async () => {
      try {
        setHasError(false);
        const renderId = `mermaid-${reactId.replace(/[:]/g, '-')}`;
        const result = await mermaid.render(renderId, chart);
        if (!cancelled) {
          setSvg(result.svg);
        }
      } catch (error) {
        console.error('Failed to render mermaid diagram', error);
        if (!cancelled) {
          setHasError(true);
          setSvg(null);
        }
      }
    };

    void renderChart();

    return () => {
      cancelled = true;
    };
  }, [chart, reactId]);

  if (hasError) {
    return <>{fallback ?? null}</>;
  }

  if (!svg) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
        Rendering diagram...
      </div>
    );
  }

  return (
    <div
      className="rounded-xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
