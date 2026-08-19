export enum AnalysisStatus {
  PENDING = 'pending',
  UPLOADING = 'uploading',
  PROCESSING = 'processing',
  EXTRACTING = 'extracting',
  COMPARING = 'comparing',
  AI_ANALYSIS = 'ai_analysis',
  GENERATING = 'generating',
  COMPLETE = 'complete',
  FAILED = 'failed',
}

export enum AnalysisInputType {
  SCREENSHOTS = 'screenshots',
  URL = 'url',
}

export interface AnalysisProgress {
  status: AnalysisStatus;
  current_step: string;
  progress_percent: number;
  message: string;
}

export interface CategoryScore {
  category: string;
  score: number;
  label: string;
  issue_count: number;
  details?: string;
}

export interface OverallScore {
  score: number;
  label: string;
  total_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
}

export enum IssueSeverity {
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW',
}

export interface Issue {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: IssueSeverity;
  affected_pages: string[];
  detected_values: Record<string, string>;
  recommended_standard?: string;
  confidence: number;
}

export interface AIRecommendation {
  issue_id: string;
  issue_title: string;
  category: string;
  explanation: string;
  visual_impact: string;
  recommendation: string;
  css_fix?: string;
  tailwind_fix?: string;
  priority: number;
}

export interface IssueWithRecommendation {
  issue: Issue;
  recommendation?: AIRecommendation;
}

export interface AnalysisResult {
  analysis_id: string;
  input_type: AnalysisInputType;
  source_url?: string;
  project_name: string;
  status: AnalysisStatus;
  progress: AnalysisProgress;
  overall_score?: OverallScore;
  category_scores: CategoryScore[];
  issues: Issue[];
  recommendations: AIRecommendation[];
  issues_with_recommendations: IssueWithRecommendation[];
  pages_analyzed: string[];
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  status: AnalysisStatus;
  progress?: AnalysisProgress;
  result?: AnalysisResult;
}
