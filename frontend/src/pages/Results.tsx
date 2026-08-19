import { useState, useEffect } from 'react';
import { getReport } from '../services/api';
import { AnalysisResult, IssueSeverity } from '../types/analysis';
import { ScoreCard } from '../components/ScoreCard';
import { CategoryScore } from '../components/CategoryScore';
import { IssueCard } from '../components/IssueCard';
import { ArrowLeft, RefreshCw, AlertTriangle, Info } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

interface ResultsProps {
  analysisId: string;
  onBack: () => void;
  onNewAnalysis: () => void;
}

export function Results({ analysisId, onBack, onNewAnalysis }: ResultsProps) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSeverity, setActiveSeverity] = useState<IssueSeverity | 'ALL'>('ALL');

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setIsLoading(true);
        const data = await getReport(analysisId);
        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [analysisId]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <RefreshCw size={40} className="animate-spin text-primary mb-4" />
        <p className="text-xl">Loading your report...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="container mx-auto p-6 max-w-3xl text-center">
        <div className="bg-error/10 text-error p-6 rounded-xl border border-error/20 mb-8 inline-block">
          <AlertTriangle size={48} className="mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Report</h2>
          <p>{error}</p>
        </div>
        <div>
          <button className="btn-primary" onClick={onBack}>Go Back</button>
        </div>
      </div>
    );
  }

  const { overall_score, category_scores, issues_with_recommendations } = result;

  const filteredIssues = activeSeverity === 'ALL' 
    ? issues_with_recommendations 
    : issues_with_recommendations.filter(i => i.issue.severity === activeSeverity);

  // Group issues for rendering if showing ALL
  const highIssues = issues_with_recommendations.filter(i => i.issue.severity === IssueSeverity.HIGH);
  const mediumIssues = issues_with_recommendations.filter(i => i.issue.severity === IssueSeverity.MEDIUM);
  const lowIssues = issues_with_recommendations.filter(i => i.issue.severity === IssueSeverity.LOW);

  // Prepare radar chart data
  const radarData = category_scores.map(cat => ({
    subject: cat.category,
    A: cat.score,
    fullMark: 100,
  }));

  return (
    <div className="container mx-auto p-4 md:p-6 max-w-6xl pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div>
          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-textMuted hover:text-text transition-colors mb-2 text-sm"
          >
            <ArrowLeft size={16} /> Back to dashboard
          </button>
          <h1 className="text-3xl font-bold">UI Consistency Report</h1>
          <p className="text-textMuted mt-1">Project: <span className="text-text font-medium">{result.project_name}</span></p>
        </div>
        
        <button className="btn-primary flex-shrink-0" onClick={onNewAnalysis}>
          New Analysis
        </button>
      </div>

      {overall_score && (
        <div className="mb-10">
          <ScoreCard score={overall_score} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        <div className="lg:col-span-2">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            Category Breakdown
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {category_scores.map(category => (
              <CategoryScore key={category.category} category={category} />
            ))}
          </div>
        </div>
        
        <div className="card bg-surface/50 flex flex-col justify-center items-center">
          <h3 className="text-lg font-bold w-full text-left mb-2">Consistency Radar</h3>
          <div className="w-full h-[250px] sm:h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="A" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="border-t border-border pt-10">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
          <h2 className="text-2xl font-bold">Detected Issues</h2>
          
          <div className="flex bg-surface rounded-lg p-1 border border-border">
            <button 
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeSeverity === 'ALL' ? 'bg-border text-text' : 'text-textMuted hover:text-text'}`}
              onClick={() => setActiveSeverity('ALL')}
            >
              All ({issues_with_recommendations.length})
            </button>
            <button 
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeSeverity === IssueSeverity.HIGH ? 'bg-error/20 text-error' : 'text-textMuted hover:text-text'}`}
              onClick={() => setActiveSeverity(IssueSeverity.HIGH)}
            >
              High ({highIssues.length})
            </button>
            <button 
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeSeverity === IssueSeverity.MEDIUM ? 'bg-warning/20 text-warning' : 'text-textMuted hover:text-text'}`}
              onClick={() => setActiveSeverity(IssueSeverity.MEDIUM)}
            >
              Medium ({mediumIssues.length})
            </button>
            <button 
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeSeverity === IssueSeverity.LOW ? 'bg-primary/20 text-primary' : 'text-textMuted hover:text-text'}`}
              onClick={() => setActiveSeverity(IssueSeverity.LOW)}
            >
              Low ({lowIssues.length})
            </button>
          </div>
        </div>

        {issues_with_recommendations.length === 0 ? (
          <div className="card p-12 text-center text-success flex flex-col items-center">
            <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mb-4">
              <Check size={32} />
            </div>
            <h3 className="text-xl font-bold">No issues found!</h3>
            <p className="mt-2 text-text">Your UI is perfectly consistent across all analyzed pages.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {activeSeverity !== 'ALL' ? (
              filteredIssues.map((item) => (
                <IssueCard key={item.issue.id} data={item} />
              ))
            ) : (
              <>
                {highIssues.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-error flex items-center gap-2 border-b border-error/20 pb-2">
                      <AlertTriangle size={18} /> High Priority
                    </h3>
                    {highIssues.map((item) => <IssueCard key={item.issue.id} data={item} />)}
                  </div>
                )}
                
                {mediumIssues.length > 0 && (
                  <div className="space-y-4 mt-8">
                    <h3 className="text-lg font-bold text-warning flex items-center gap-2 border-b border-warning/20 pb-2">
                      <Info size={18} /> Medium Priority
                    </h3>
                    {mediumIssues.map((item) => <IssueCard key={item.issue.id} data={item} />)}
                  </div>
                )}
                
                {lowIssues.length > 0 && (
                  <div className="space-y-4 mt-8">
                    <h3 className="text-lg font-bold text-primary flex items-center gap-2 border-b border-primary/20 pb-2">
                      <Info size={18} /> Low Priority (Cosmetic)
                    </h3>
                    {lowIssues.map((item) => <IssueCard key={item.issue.id} data={item} />)}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Internal import missing in this file scope context
import { Check } from 'lucide-react';
