import { AIRecommendation } from '../types/analysis';
import { Sparkles, Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface RecommendationCardProps {
  recommendation: AIRecommendation;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const [copiedCss, setCopiedCss] = useState(false);
  const [copiedTw, setCopiedTw] = useState(false);

  const handleCopy = (text: string, isCss: boolean) => {
    navigator.clipboard.writeText(text);
    if (isCss) {
      setCopiedCss(true);
      setTimeout(() => setCopiedCss(false), 2000);
    } else {
      setCopiedTw(true);
      setTimeout(() => setCopiedTw(false), 2000);
    }
  };

  return (
    <div className="bg-gradient-to-r from-surface to-background border border-primary/20 rounded-xl overflow-hidden shadow-inner">
      <div className="bg-primary/10 px-4 py-3 border-b border-primary/20 flex items-center gap-2">
        <Sparkles size={16} className="text-primary" />
        <h4 className="font-semibold text-primary text-sm">AI Recommendation</h4>
      </div>
      
      <div className="p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h5 className="text-xs uppercase font-bold text-textMuted tracking-wider mb-2">Why it matters</h5>
            <p className="text-sm text-text">{recommendation.explanation}</p>
          </div>
          <div>
            <h5 className="text-xs uppercase font-bold text-textMuted tracking-wider mb-2">Visual Impact</h5>
            <p className="text-sm text-text">{recommendation.visual_impact}</p>
          </div>
        </div>

        <div className="mb-6 bg-surface/50 p-4 rounded-lg border border-border">
          <h5 className="text-xs uppercase font-bold text-textMuted tracking-wider mb-2">Recommendation</h5>
          <p className="text-base text-text font-medium">{recommendation.recommendation}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendation.css_fix && (
            <div className="relative group">
              <div className="flex justify-between items-center bg-background px-4 py-2 border border-border rounded-t-lg border-b-0">
                <span className="text-xs font-mono text-textMuted">CSS Fix</span>
                <button 
                  onClick={() => handleCopy(recommendation.css_fix!, true)}
                  className="text-textMuted hover:text-text transition-colors p-1"
                  title="Copy to clipboard"
                >
                  {copiedCss ? <Check size={14} className="text-success" /> : <Copy size={14} />}
                </button>
              </div>
              <pre className="bg-[#0d1117] p-4 rounded-b-lg border border-border overflow-x-auto text-sm text-[#c9d1d9] font-mono leading-relaxed">
                <code>{recommendation.css_fix}</code>
              </pre>
            </div>
          )}

          {recommendation.tailwind_fix && (
            <div className="relative group">
              <div className="flex justify-between items-center bg-background px-4 py-2 border border-border rounded-t-lg border-b-0">
                <span className="text-xs font-mono text-textMuted">Tailwind Fix</span>
                <button 
                  onClick={() => handleCopy(recommendation.tailwind_fix!, false)}
                  className="text-textMuted hover:text-text transition-colors p-1"
                  title="Copy to clipboard"
                >
                  {copiedTw ? <Check size={14} className="text-success" /> : <Copy size={14} />}
                </button>
              </div>
              <pre className="bg-[#0d1117] p-4 rounded-b-lg border border-border overflow-x-auto text-sm text-[#a5d6ff] font-mono leading-relaxed h-[calc(100%-34px)] flex items-center">
                <code>{recommendation.tailwind_fix}</code>
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
