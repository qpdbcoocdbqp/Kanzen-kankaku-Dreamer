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
import { Info, AlertTriangle, CheckCircle, XCircle, ChevronRight } from 'lucide-react';

const MarkdownBlock: React.FC<{ data: MarkdownComponent }> = ({ data }) => {
  // Fallback if model puts text in description or just 'text' field by mistake
  const content = data.content || (data as any).description || (data as any).text || "";
  return (
    <div className="prose prose-slate prose-sm max-w-none text-slate-700 leading-relaxed">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};

const InfoCard: React.FC<{ data: InfoCardComponent }> = ({ data }) => {
  const styles = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    danger: 'bg-red-50 border-red-200 text-red-800',
  };

  const icons = {
    info: <Info className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    success: <CheckCircle className="w-5 h-5" />,
    danger: <XCircle className="w-5 h-5" />,
  };
  
  // Default to info if variant is invalid or missing
  const variant = data.variant && styles[data.variant] ? data.variant : 'info';
  // Fallback for description if missing
  const description = data.description || (data as any).content || "";

  if (!description && !data.title) return null;

  return (
    <div className={`p-4 rounded-xl border ${styles[variant]} flex items-start gap-3 my-2`}>
      <div className="mt-0.5 shrink-0">{icons[variant]}</div>
      <div>
        <h4 className="font-semibold text-sm mb-1">{data.title}</h4>
        <p className="text-sm opacity-90">{description}</p>
      </div>
    </div>
  );
};

const DataList: React.FC<{ data: DataListComponent }> = ({ data }) => (
  <div className="bg-white rounded-xl border border-slate-200 overflow-hidden my-2 shadow-sm">
    {data.title && (
      <div className="bg-slate-50 px-4 py-2 border-b border-slate-200">
        <h4 className="font-semibold text-sm text-slate-700">{data.title}</h4>
      </div>
    )}
    <div className="divide-y divide-slate-100">
      {data.items?.map((item, idx) => (
        <div key={idx} className="px-4 py-3 flex justify-between items-center text-sm">
          <span className="text-slate-500">{item.label}</span>
          <span className="font-medium text-slate-900">{item.value}</span>
        </div>
      ))}
    </div>
  </div>
);

const StepProcess: React.FC<{ data: StepProcessComponent }> = ({ data }) => (
  <div className="my-4">
    {data.steps?.map((step, idx) => (
      <div key={idx} className="flex gap-4 relative">
        {/* Connector Line */}
        {idx !== data.steps.length - 1 && (
          <div className="absolute left-[15px] top-8 bottom-[-16px] w-0.5 bg-slate-200" />
        )}
        
        <div className="w-8 h-8 shrink-0 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm border-2 border-white shadow-sm z-10">
          {idx + 1}
        </div>
        <div className="pb-6">
          <h5 className="font-semibold text-slate-900 text-sm">{step.title}</h5>
          <p className="text-slate-600 text-sm mt-1">{step.description}</p>
        </div>
      </div>
    ))}
  </div>
);

const Table: React.FC<{ data: TableComponent }> = ({ data }) => {
  if (!data.rows || data.rows.length === 0) return null;

  return (
    <div className="my-4 overflow-hidden rounded-xl border border-slate-200 shadow-sm bg-white">
      {data.title && (
         <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 font-semibold text-sm text-slate-700">
           {data.title}
         </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
            <tr>
              {data.headers?.map((h, i) => <th key={i} className="px-4 py-3 whitespace-nowrap">{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.rows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-50/50 transition-colors">
                 {row.map((cell, cIdx) => (
                   <td key={cIdx} className="px-4 py-3 text-slate-700">{cell}</td>
                 ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const AGUIRenderer: React.FC<{ components: AGUIComponent[] }> = ({ components }) => {
  if (!components || !Array.isArray(components)) return null;
  
  return (
    <div className="space-y-4">
      {components.map((component, index) => {
        if (!component || !component.type) return null;
        
        switch (component.type) {
          case ComponentType.MARKDOWN:
            return <MarkdownBlock key={index} data={component as MarkdownComponent} />;
          case ComponentType.INFO_CARD:
            return <InfoCard key={index} data={component as InfoCardComponent} />;
          case ComponentType.DATA_LIST:
            return <DataList key={index} data={component as DataListComponent} />;
          case ComponentType.STEP_PROCESS:
            return <StepProcess key={index} data={component as StepProcessComponent} />;
          case ComponentType.TABLE:
            return <Table key={index} data={component as TableComponent} />;
          default:
            return null;
        }
      })}
    </div>
  );
};