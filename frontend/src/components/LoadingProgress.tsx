import { AnalysisProgress, AnalysisStatus } from '../types/analysis';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface LoadingProgressProps {
  progress: AnalysisProgress;
}

export function LoadingProgress({ progress }: LoadingProgressProps) {
  const isComplete = progress.status === AnalysisStatus.COMPLETE;
  const isFailed = progress.status === AnalysisStatus.FAILED;
  const percent = progress.progress_percent || 0;

  return (
    <div className="w-full max-w-xl mx-auto card flex flex-col items-center py-12">
      <div className="mb-8 relative">
        {isComplete ? (
          <div className="w-20 h-20 bg-success/10 text-success rounded-full flex items-center justify-center">
            <CheckCircle size={40} />
          </div>
        ) : isFailed ? (
          <div className="w-20 h-20 bg-error/10 text-error rounded-full flex items-center justify-center">
            <AlertCircle size={40} />
          </div>
        ) : (
          <div className="relative flex items-center justify-center">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="44"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-border"
              />
              <circle
                cx="48"
                cy="48"
                r="44"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-primary transition-all duration-500 ease-out"
                strokeDasharray="276"
                strokeDashoffset={276 - (276 * percent) / 100}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <span className="text-xl font-bold">{Math.round(percent)}%</span>
            </div>
          </div>
        )}
      </div>

      <h3 className="text-xl font-bold mb-2">
        {isComplete ? 'Analysis Complete' : 
         isFailed ? 'Analysis Failed' : 
         progress.current_step || 'Processing...'}
      </h3>
      
      <p className={`text-center max-w-md ${isFailed ? 'text-error' : 'text-textMuted'}`}>
        {progress.message || 'Please wait while we analyze your UI...'}
      </p>

      {!isComplete && !isFailed && (
        <div className="mt-8 flex items-center gap-2 text-sm text-primary">
          <Loader2 size={16} className="animate-spin" />
          This may take a minute or two depending on AI processing...
        </div>
      )}
    </div>
  );
}
