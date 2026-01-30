import React from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  AGUIComponent, 
  ComponentType, 
  MarkdownComponent, 
  InfoCardComponent, 
  DataListComponent, 
  StepProcessComponent,
  TableComponent
} from '../types';
import { 
  Info, 
  AlertTriangle, 
  CheckCircle2, 
  Ban, 
  ListChecks,
  LayoutList
} from 'lucide-react';

/**
 * Deeply extracts text from any object/array/primitive structure.
 */
const extractText = (val: any): string => {
  if (val === null || val === undefined) return "";
  if (typeof val === 'string') return val;
  if (typeof val === 'number' || typeof val === 'boolean') return String(val);
  if (Array.isArray(val)) {
    return val.map(extractText).filter(s => s.trim() !== "").join('\n');
  }
  if (typeof val === 'object') {
    if (val.text) return extractText(val.text);
    if (val.content) return extractText(val.content);
    if (val.value) return extractText(val.value);
    if (val.description) return extractText(val.description);
    if (val.message) return extractText(val.message);
    if (val.label && !val.value) return extractText(val.label);
    if (val.title && !val.description) return extractText(val.title);
    const values = Object.values(val);
    if (values.length > 0) {
      const extracted = values.map(v => extractText(v)).filter(s => s.trim() !== "");
      if (extracted.length > 0) return extracted.join(', ');
    }
    return "";
  }
  return String(val);
};

interface RendererProps {
  data: any;
  themeColor: string;
}

const MarkdownBlock: React.FC<RendererProps> = ({ data, themeColor }) => {
  const content = extractText(data.content || (data as any).description || (data as any).text || (data as any).value);
  if (!content) return null;
  
  return (
    <div className={`prose prose-slate dark:prose-invert max-w-none text-slate-700 dark:text-slate-300 leading-relaxed
      prose-headings:font-bold prose-headings:text-slate-800 dark:prose-headings:text-slate-100
      prose-p:my-3 prose-strong:text-slate-900 dark:prose-strong:text-slate-100 prose-strong:font-semibold
      prose-ul:list-disc prose-ul:pl-5
      prose-code:text-${themeColor}-600 dark:prose-code:text-${themeColor}-400 
      prose-code:bg-${themeColor}-50 dark:prose-code:bg-${themeColor}-900/30 
      prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md prose-code:font-mono prose-code:text-sm`}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};

const InfoCard: React.FC<RendererProps> = ({ data }) => {
  const variantStyles = {
    info: {
      container: 'bg-sky-50 dark:bg-sky-900/20 border-sky-100 dark:border-sky-800',
      iconBg: 'bg-sky-100 dark:bg-sky-800 text-sky-600 dark:text-sky-300',
      title: 'text-sky-900 dark:text-sky-100',
      text: 'text-sky-800 dark:text-sky-200',
      border: 'border-l-sky-500',
      icon: Info
    },
    warning: {
      container: 'bg-amber-50 dark:bg-amber-900/20 border-amber-100 dark:border-amber-800',
      iconBg: 'bg-amber-100 dark:bg-amber-800 text-amber-600 dark:text-amber-300',
      title: 'text-amber-900 dark:text-amber-100',
      text: 'text-amber-800 dark:text-amber-200',
      border: 'border-l-amber-500',
      icon: AlertTriangle
    },
    success: {
      container: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-100 dark:border-emerald-800',
      iconBg: 'bg-emerald-100 dark:bg-emerald-800 text-emerald-600 dark:text-emerald-300',
      title: 'text-emerald-900 dark:text-emerald-100',
      text: 'text-emerald-800 dark:text-emerald-200',
      border: 'border-l-emerald-500',
      icon: CheckCircle2
    },
    danger: {
      container: 'bg-rose-50 dark:bg-rose-900/20 border-rose-100 dark:border-rose-800',
      iconBg: 'bg-rose-100 dark:bg-rose-800 text-rose-600 dark:text-rose-300',
      title: 'text-rose-900 dark:text-rose-100',
      text: 'text-rose-800 dark:text-rose-200',
      border: 'border-l-rose-500',
      icon: Ban
    },
  };
  
  const v = data.variant && variantStyles[data.variant as keyof typeof variantStyles] ? data.variant as keyof typeof variantStyles : 'info';
  const style = variantStyles[v];
  const Icon = style.icon;
  
  const title = extractText(data.title);
  const rawDesc = data.description || (data as any).content || (data as any).text;
  const description = extractText(rawDesc);

  if (!description && !title) return null;

  return (
    <div className={`relative overflow-hidden rounded-r-xl rounded-l-md border-y border-r border-l-[4px] ${style.container} ${style.border} p-4 my-4 shadow-sm transition-transform hover:scale-[1.01] duration-300`}>
      <div className="flex items-start gap-4">
        <div className={`shrink-0 w-10 h-10 rounded-full ${style.iconBg} flex items-center justify-center shadow-sm ring-2 ring-white dark:ring-transparent`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          {title && <h4 className={`font-bold text-base mb-1 ${style.title}`}>{title}</h4>}
          <div className={`text-sm leading-relaxed opacity-90 ${style.text}`}>
            <ReactMarkdown>{description}</ReactMarkdown>
          </div>
        </div>
      </div>
      <Icon className="absolute -right-4 -bottom-4 w-24 h-24 opacity-5 pointer-events-none" />
    </div>
  );
};

const DataList: React.FC<RendererProps> = ({ data, themeColor }) => {
  const title = extractText(data.title);
  
  return (
    <div className="my-4 rounded-xl border border-slate-200 dark:border-app-border bg-white dark:bg-app-card shadow-sm overflow-hidden">
      {title && (
        <div className="bg-slate-50/80 dark:bg-zinc-800/50 px-5 py-3 border-b border-slate-200 dark:border-app-border flex items-center gap-2">
          <ListChecks className="w-4 h-4 text-slate-500 dark:text-slate-400" />
          <h4 className="font-semibold text-sm text-slate-700 dark:text-slate-200">{title}</h4>
        </div>
      )}
      <div className="divide-y divide-slate-100 dark:divide-app-border">
        {data.items?.map((item: any, idx: number) => {
          let label = "";
          let value = "";

          if (typeof item === 'string') {
            value = item;
          } else if (typeof item === 'object' && item !== null) {
            if (item.label || item.value) {
               label = extractText(item.label);
               value = extractText(item.value);
            } else {
               const keys = Object.keys(item).filter(k => k !== 'type');
               if (keys.length === 1) {
                 label = keys[0];
                 value = extractText(item[keys[0]]);
               } else if (keys.length > 1) {
                 const labelKey = keys.find(k => /name|label|key|title/i.test(k));
                 const valueKey = keys.find(k => k !== labelKey);
                 if (labelKey) {
                   label = extractText(item[labelKey]);
                   value = valueKey ? extractText(item[valueKey]) : "";
                 } else {
                   value = extractText(item);
                 }
               } else {
                 value = extractText(item);
               }
            }
          }

          if (!label && !value) return null;

          return (
            <div 
              key={idx} 
              className={`group flex flex-col sm:flex-row sm:justify-between sm:items-center px-5 py-3 hover:bg-slate-50 dark:hover:bg-zinc-800/50 transition-colors gap-1 sm:gap-4`}
            >
              {label && (
                <span className={`text-sm font-medium text-slate-500 dark:text-slate-400 shrink-0 group-hover:text-${themeColor}-600 dark:group-hover:text-${themeColor}-400 transition-colors`}>
                  {label}
                </span>
              )}
              <span className={`text-sm text-slate-900 dark:text-slate-100 font-medium break-words ${label ? 'text-left sm:text-right' : 'text-left'}`}>
                {value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const StepProcess: React.FC<RendererProps> = ({ data, themeColor }) => {
  const title = extractText(data.title);
  
  return (
    <div className="my-6 relative pl-2">
      {title && (
        <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-6 pl-2 flex items-center gap-2">
          <span className={`bg-${themeColor}-100 dark:bg-${themeColor}-900/40 text-${themeColor}-700 dark:text-${themeColor}-300 py-1 px-2 rounded text-xs uppercase tracking-wider`}>Process</span>
          {title}
        </h4>
      )}
      <div className="space-y-0">
        {data.steps?.map((step: any, idx: number) => {
          const isLast = idx === (data.steps.length - 1);
          
          let stepTitle = "";
          let stepDesc = "";
          
          if (typeof step === 'string') {
             stepDesc = step;
          } else if (typeof step === 'object') {
             stepTitle = extractText(step.title || step.name || step.step);
             stepDesc = extractText(step.description || step.instruction || step.content || step.details || step.text);
             if (!stepDesc && stepTitle) {
               stepDesc = stepTitle;
               stepTitle = "";
             }
          }

          if (!stepTitle && !stepDesc) return null;

          return (
            <div key={idx} className="flex gap-4 relative group">
              {!isLast && (
                <div className={`absolute left-[19px] top-10 bottom-0 w-0.5 bg-gradient-to-b from-${themeColor}-200 to-slate-200 dark:from-${themeColor}-800 dark:to-zinc-700 group-hover:from-${themeColor}-400 group-hover:to-slate-300 transition-colors`} />
              )}
              
              <div className={`relative z-10 w-10 h-10 shrink-0 rounded-full bg-white dark:bg-app-card border-2 border-${themeColor}-100 dark:border-${themeColor}-900 text-${themeColor}-600 dark:text-${themeColor}-400 flex items-center justify-center font-bold text-sm shadow-sm group-hover:border-${themeColor}-400 group-hover:text-${themeColor}-700 dark:group-hover:text-${themeColor}-300 group-hover:scale-110 transition-all duration-300`}>
                {idx + 1}
              </div>
              
              <div className="pb-8 flex-1 min-w-0 pt-1">
                <div className={`bg-white dark:bg-app-card border border-slate-100 dark:border-app-border rounded-lg p-4 shadow-sm hover:shadow-md hover:border-${themeColor}-200 dark:hover:border-${themeColor}-700 transition-all duration-300 relative`}>
                  <div className={`absolute top-4 -left-[7px] w-3 h-3 bg-white dark:bg-app-card border-l border-b border-slate-100 dark:border-app-border transform rotate-45 group-hover:border-${themeColor}-200 dark:group-hover:border-${themeColor}-700 transition-colors`} />
                  
                  {stepTitle && <h5 className="font-bold text-slate-900 dark:text-slate-100 text-sm mb-1">{stepTitle}</h5>}
                  <div className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                     <ReactMarkdown>{stepDesc}</ReactMarkdown>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Table: React.FC<RendererProps> = ({ data }) => {
  if (!data.rows || data.rows.length === 0) return null;
  const title = extractText(data.title);

  return (
    <div className="my-5 overflow-hidden rounded-xl border border-slate-200 dark:border-app-border shadow-sm bg-white dark:bg-app-card ring-1 ring-slate-100 dark:ring-app-border">
      {title && (
         <div className="bg-slate-50/80 dark:bg-zinc-800/50 backdrop-blur-sm px-5 py-3 border-b border-slate-200 dark:border-app-border font-bold text-sm text-slate-700 dark:text-slate-200 flex items-center gap-2">
           <LayoutList className="w-4 h-4 text-slate-400" />
           {title}
         </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 dark:bg-zinc-800/30 border-b border-slate-200 dark:border-app-border">
              {data.headers?.map((h: any, i: number) => (
                <th key={i} className="px-5 py-3 font-semibold text-slate-600 dark:text-slate-300 whitespace-nowrap first:pl-6 last:pr-6">
                  {extractText(h)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-app-border">
            {data.rows.map((row: any[], rIdx: number) => (
              <tr 
                key={rIdx} 
                className="hover:bg-slate-50 dark:hover:bg-zinc-800/30 transition-colors even:bg-slate-50/30 dark:even:bg-zinc-800/10"
              >
                 {row.map((cell, cIdx) => (
                   <td 
                     key={cIdx} 
                     className="px-5 py-3 text-slate-700 dark:text-slate-300 first:pl-6 last:pr-6 first:font-medium first:text-slate-900 dark:first:text-slate-100"
                   >
                     {extractText(cell)}
                   </td>
                 ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const AGUIRenderer: React.FC<{ components: AGUIComponent[], themeColor?: string }> = ({ components, themeColor = 'indigo' }) => {
  if (!components || !Array.isArray(components)) return null;
  
  return (
    <div className="flex flex-col gap-2 w-full">
      {components.map((component, index) => {
        if (!component || !component.type) return null;
        
        const props = { data: component as any, themeColor };

        return (
          <div key={index} className="w-full animate-fadeIn" style={{ animationDelay: `${index * 100}ms` }}>
            {(() => {
              try {
                switch (component.type) {
                  case ComponentType.MARKDOWN:
                    return <MarkdownBlock {...props} />;
                  case ComponentType.INFO_CARD:
                    return <InfoCard {...props} />;
                  case ComponentType.DATA_LIST:
                    return <DataList {...props} />;
                  case ComponentType.STEP_PROCESS:
                    return <StepProcess {...props} />;
                  case ComponentType.TABLE:
                    return <Table {...props} />;
                  default:
                    return null;
                }
              } catch (e) {
                console.error("Error rendering component:", component, e);
                return (
                   <div className="p-2 border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded text-xs">
                     Component Rendering Error
                   </div>
                );
              }
            })()}
          </div>
        );
      })}
    </div>
  );
};