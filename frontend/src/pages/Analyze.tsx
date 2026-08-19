import { useState, useEffect, useRef, useCallback } from 'react';
import { UploadZone } from '../components/UploadZone';
import { UrlInput } from '../components/UrlInput';
import { LoadingProgress } from '../components/LoadingProgress';
import { analyzeScreenshots, analyzeUrl, getAnalysis } from '../services/api';
import { AnalysisStatus, AnalysisProgress } from '../types/analysis';

interface AnalyzeProps {
  onComplete: (analysisId: string) => void;
  onBack: () => void;
}

export function Analyze({ onComplete, onBack }: AnalyzeProps) {
  const [activeTab, setActiveTab] = useState<'screenshots' | 'url'>('screenshots');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);

  // Use refs to keep the latest values accessible from the polling callback
  // without causing the useEffect to re-run on every state change
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;
  const analysisIdRef = useRef(analysisId);
  analysisIdRef.current = analysisId;

  // Poll for progress when analyzing
  useEffect(() => {
    if (!isAnalyzing || !analysisId) return;

    let intervalId: number;
    let cancelled = false;

    const pollProgress = async () => {
      const currentId = analysisIdRef.current;
      if (!currentId || cancelled) return;

      try {
        const response = await getAnalysis(currentId);
        if (cancelled) return;

        if (response.progress) {
          setProgress(response.progress);
        }

        if (response.status === AnalysisStatus.COMPLETE) {
          if (intervalId) window.clearInterval(intervalId);
          setIsAnalyzing(false);
          onCompleteRef.current(currentId);
        } else if (response.status === AnalysisStatus.FAILED) {
          if (intervalId) window.clearInterval(intervalId);
          setIsAnalyzing(false);
        }
      } catch (error) {
        console.error('Error polling analysis:', error);
      }
    };

    // Poll immediately on first run, then every 1.5 seconds
    pollProgress();
    intervalId = window.setInterval(pollProgress, 1500);

    return () => {
      cancelled = true;
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [isAnalyzing, analysisId]);

  const handleScreenshotAnalyze = useCallback(async (files: File[]) => {
    try {
      setIsAnalyzing(true);
      setProgress({
        status: AnalysisStatus.UPLOADING,
        current_step: 'Uploading',
        progress_percent: 5,
        message: 'Uploading screenshots...',
      });

      const response = await analyzeScreenshots(files);

      // Check if analysis already completed during the POST (unlikely but handle it)
      if (response.status === AnalysisStatus.COMPLETE) {
        setIsAnalyzing(false);
        onCompleteRef.current(response.analysis_id);
        return;
      }

      if (response.progress) {
        setProgress(response.progress);
      }

      setAnalysisId(response.analysis_id);
    } catch (error) {
      console.error(error);
      setIsAnalyzing(false);
      setProgress({
        status: AnalysisStatus.FAILED,
        current_step: 'Failed',
        progress_percent: 0,
        message: error instanceof Error ? error.message : 'Upload failed',
      });
    }
  }, []);

  const handleUrlAnalyze = useCallback(async (url: string) => {
    try {
      setIsAnalyzing(true);
      setProgress({
        status: AnalysisStatus.PENDING,
        current_step: 'Starting',
        progress_percent: 5,
        message: 'Starting URL analysis...',
      });

      const response = await analyzeUrl(url);

      // Check if analysis already completed during the POST (unlikely but handle it)
      if (response.status === AnalysisStatus.COMPLETE) {
        setIsAnalyzing(false);
        onCompleteRef.current(response.analysis_id);
        return;
      }

      if (response.progress) {
        setProgress(response.progress);
      }

      setAnalysisId(response.analysis_id);
    } catch (error) {
      console.error(error);
      setIsAnalyzing(false);
      setProgress({
        status: AnalysisStatus.FAILED,
        current_step: 'Failed',
        progress_percent: 0,
        message: error instanceof Error ? error.message : 'Failed to start analysis',
      });
    }
  }, []);

  if (isAnalyzing || progress?.status === AnalysisStatus.FAILED) {
    return (
      <div className="container mx-auto p-6 flex flex-col items-center justify-center min-h-[60vh]">
        {progress && <LoadingProgress progress={progress} />}
        
        {progress?.status === AnalysisStatus.FAILED && (
          <button 
            className="mt-8 btn-secondary"
            onClick={() => {
              setIsAnalyzing(false);
              setProgress(null);
              setAnalysisId(null);
            }}
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Start Analysis</h1>
          <p className="text-textMuted">Choose how you want to provide your UI for consistency checking.</p>
        </div>
        <button className="btn-secondary" onClick={onBack}>Cancel</button>
      </div>

      <div className="bg-surface/50 rounded-xl p-2 mb-8 flex border border-border">
        <button
          className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
            activeTab === 'screenshots' 
              ? 'bg-primary text-white shadow-md' 
              : 'text-textMuted hover:text-text hover:bg-surface'
          }`}
          onClick={() => setActiveTab('screenshots')}
        >
          Upload Screenshots
        </button>
        <button
          className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all ${
            activeTab === 'url' 
              ? 'bg-primary text-white shadow-md' 
              : 'text-textMuted hover:text-text hover:bg-surface'
          }`}
          onClick={() => setActiveTab('url')}
        >
          Website URL
        </button>
      </div>

      <div className="py-8 animate-in fade-in duration-300">
        {activeTab === 'screenshots' ? (
          <UploadZone onAnalyze={handleScreenshotAnalyze} isLoading={isAnalyzing} />
        ) : (
          <UrlInput onAnalyze={handleUrlAnalyze} isLoading={isAnalyzing} />
        )}
      </div>
    </div>
  );
}
