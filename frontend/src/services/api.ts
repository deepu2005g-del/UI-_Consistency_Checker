import { AnalysisResponse, AnalysisResult } from '../types/analysis';

const API_BASE = (import.meta as any).env.VITE_API_URL || '/api';

export const analyzeScreenshots = async (files: File[]): Promise<AnalysisResponse> => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  const response = await fetch(`${API_BASE}/analyze/screenshots`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || 'Failed to start screenshot analysis');
  }

  return response.json();
};

export const analyzeUrl = async (url: string): Promise<AnalysisResponse> => {
  const response = await fetch(`${API_BASE}/analyze/url`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || 'Failed to start URL analysis');
  }

  return response.json();
};

export const getAnalysis = async (analysisId: string): Promise<AnalysisResponse> => {
  const response = await fetch(`${API_BASE}/analysis/${analysisId}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch analysis status');
  }

  return response.json();
};

export const getReport = async (analysisId: string): Promise<AnalysisResult> => {
  const response = await fetch(`${API_BASE}/analysis/${analysisId}/report`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || 'Failed to fetch analysis report');
  }

  return response.json();
};
