import { useState } from 'react';
import { Globe, ArrowRight } from 'lucide-react';

interface UrlInputProps {
  onAnalyze: (url: string) => void;
  isLoading: boolean;
}

export function UrlInput({ onAnalyze, isLoading }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    try {
      const parsedUrl = new URL(url.trim());
      if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
        setError('Please enter a valid HTTP/HTTPS URL');
        return;
      }
      
      const hostname = parsedUrl.hostname.toLowerCase();
      if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
        setError('Localhost URLs cannot be analyzed. Please use a public URL or upload screenshots.');
        return;
      }

      setError('');
      onAnalyze(url.trim());
    } catch {
      setError('Please enter a valid URL (e.g., https://example.com)');
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="card text-center py-10">
        <div className="flex justify-center mb-6 text-primary">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Globe size={32} />
          </div>
        </div>
        
        <h3 className="text-xl font-medium mb-2">Analyze Live Website</h3>
        <p className="text-textMuted mb-8 text-sm">
          Enter a public URL. We'll automatically capture multiple pages and viewports.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) setError('');
              }}
              placeholder="https://example.com"
              className="w-full bg-background border border-border rounded-lg pl-4 pr-32 py-4 text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
              disabled={isLoading}
            />
            <button 
              type="submit"
              className="absolute right-2 top-2 bottom-2 btn-primary flex items-center gap-2"
              disabled={isLoading}
            >
              {isLoading ? 'Starting...' : (
                <>
                  Analyze <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
          
          {error && (
            <p className="text-error text-sm text-left px-2">{error}</p>
          )}
        </form>
        
        <div className="mt-8 text-left bg-background p-4 rounded-lg border border-border text-sm text-textMuted">
          <p className="font-medium text-text mb-2">How it works:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>We visit the URL and extract layout & styles.</li>
            <li>We discover up to 5 internal pages automatically.</li>
            <li>We capture desktop, tablet, and mobile layouts.</li>
            <li>Requires a publicly accessible internet URL.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
