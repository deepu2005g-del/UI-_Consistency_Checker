import { useState } from 'react';
import { IssueWithRecommendation, IssueSeverity } from '../types/analysis';
import { ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { RecommendationCard } from './RecommendationCard';

interface IssueCardProps {
  data: IssueWithRecommendation;
}

export function IssueCard({ data }: IssueCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { issue, recommendation } = data;

  const getSeverityColors = (severity: IssueSeverity) => {
    switch (severity) {
      case IssueSeverity.HIGH:
        return 'bg-error/10 text-error border-error/30';
      case IssueSeverity.MEDIUM:
        return 'bg-warning/10 text-warning border-warning/30';
      case IssueSeverity.LOW:
        return 'bg-primary/10 text-primary border-primary/30';
      default:
        return 'bg-surface text-text border-border';
    }
  };

  return (
    <div className={`card overflow-hidden transition-all duration-300 ${isExpanded ? 'border-primary/50 ring-1 ring-primary/20' : ''}`}>
      <div 
        className="flex items-start md:items-center justify-between cursor-pointer group"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex flex-col md:flex-row md:items-center gap-3 md:gap-4 flex-1">
          <div className={`px-2.5 py-1 rounded-md text-xs font-bold border ${getSeverityColors(issue.severity)} flex items-center gap-1.5 whitespace-nowrap self-start md:self-auto`}>
            {issue.severity === IssueSeverity.HIGH && <AlertTriangle size={12} />}
            {issue.severity}
          </div>
          
          <div className="flex flex-col">
            <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">{issue.title}</h3>
            <div className="flex items-center gap-2 text-sm text-textMuted mt-1">
              <span className="bg-background px-2 py-0.5 rounded text-xs border border-border">{issue.category}</span>
              <span>•</span>
              <span>Affects {issue.affected_pages.length} pages</span>
            </div>
          </div>
        </div>
        
        <div className="text-textMuted ml-4 self-center">
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-6 pt-6 border-t border-border animate-in fade-in slide-in-from-top-2 duration-200">
          <p className="text-text mb-6">{issue.description}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-background border border-border rounded-lg p-4">
              <h4 className="text-sm font-semibold text-textMuted mb-3 uppercase tracking-wider">Detected Variations</h4>
              <ul className="space-y-2">
                {Object.entries(issue.detected_values).map(([page, value]) => (
                  <li key={page} className="flex justify-between items-center text-sm border-b border-border/50 pb-2 last:border-0 last:pb-0">
                    <span className="text-text">{page}</span>
                    <code className="bg-surface px-2 py-0.5 rounded text-primary font-mono">{value}</code>
                  </li>
                ))}
              </ul>
            </div>
            
            {issue.recommended_standard && (
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 flex flex-col justify-center items-center text-center">
                <h4 className="text-sm font-semibold text-primary mb-2 uppercase tracking-wider">Recommended Standard</h4>
                <code className="text-xl font-mono text-text bg-surface px-4 py-2 rounded-lg border border-border shadow-sm">
                  {issue.recommended_standard}
                </code>
              </div>
            )}
          </div>

          {recommendation && <RecommendationCard recommendation={recommendation} />}
          {!recommendation && (
            <div className="text-sm text-textMuted italic text-center p-4">
              No AI recommendation generated for this issue.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
