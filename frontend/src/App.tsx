import { useState } from 'react';
import { Analyze } from './pages/Analyze';
import { Results } from './pages/Results';
import { Palette, CheckCircle, Smartphone, Zap } from 'lucide-react';

function App() {
  const [currentRoute, setCurrentRoute] = useState<'home' | 'analyze' | 'results'>('home');
  const [analysisId, setAnalysisId] = useState<string | null>(null);

  const handleAnalysisComplete = (id: string) => {
    setAnalysisId(id);
    setCurrentRoute('results');
  };

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <header className="glass sticky top-0 z-50 flex items-center h-16 px-6 border-b border-white/5">
        <div 
          className="flex items-center gap-3 cursor-pointer group" 
          onClick={() => setCurrentRoute('home')}
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-primary/20 group-hover:scale-105 transition-transform">
            UI
          </div>
          <span className="font-semibold text-lg tracking-tight text-white/90">Consistency Checker</span>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        {currentRoute === 'home' && (
          <div className="flex flex-col items-center px-4 py-20 pb-32 max-w-6xl mx-auto">
            <div className="inline-block px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary font-medium text-sm mb-8 animate-in slide-in-from-bottom-4 duration-500">
              Powered by Google Gemini 2.0 Flash
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold text-center tracking-tight mb-6 animate-in slide-in-from-bottom-6 duration-700">
              Stop guessing if your UI <br className="hidden md:block" />
              is <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-purple-500 to-pink-500">visually consistent</span>.
            </h1>
            
            <p className="text-xl md:text-2xl text-textMuted max-w-3xl text-center mb-12 animate-in slide-in-from-bottom-8 duration-700 delay-100 leading-relaxed">
              Upload screenshots or provide a URL. Our AI analyzes your design system, spots inconsistencies, and generates CSS fixes instantly.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 mb-24 animate-in slide-in-from-bottom-10 duration-700 delay-200">
              <button 
                className="bg-primary hover:bg-primaryHover text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-0.5"
                onClick={() => setCurrentRoute('analyze')}
              >
                Start Free Analysis
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full animate-in fade-in duration-1000 delay-300">
              <div className="card hover:-translate-y-1 transition-transform duration-300 border-white/5 bg-surface/40 backdrop-blur-sm">
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-6">
                  <Palette size={24} />
                </div>
                <h3 className="text-xl font-bold mb-3 text-white/90">Design System Extraction</h3>
                <p className="text-textMuted leading-relaxed">Automatically extracts colors, typography, buttons, and spacing into a structured dataset directly from your UI.</p>
              </div>

              <div className="card hover:-translate-y-1 transition-transform duration-300 border-white/5 bg-surface/40 backdrop-blur-sm">
                <div className="w-12 h-12 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-6">
                  <CheckCircle size={24} />
                </div>
                <h3 className="text-xl font-bold mb-3 text-white/90">Smart Consistency Engine</h3>
                <p className="text-textMuted leading-relaxed">Detects variations in padding, border-radii, font weights, and colors across multiple pages with configurable tolerances.</p>
              </div>

              <div className="card hover:-translate-y-1 transition-transform duration-300 border-white/5 bg-surface/40 backdrop-blur-sm">
                <div className="w-12 h-12 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center mb-6">
                  <Zap size={24} />
                </div>
                <h3 className="text-xl font-bold mb-3 text-white/90">AI-Generated Fixes</h3>
                <p className="text-textMuted leading-relaxed">Generates specific, copy-paste ready CSS and Tailwind utility fixes to resolve detected inconsistencies immediately.</p>
              </div>
            </div>
          </div>
        )}
        
        {currentRoute === 'analyze' && (
          <Analyze 
            onComplete={handleAnalysisComplete} 
            onBack={() => setCurrentRoute('home')} 
          />
        )}

        {currentRoute === 'results' && analysisId && (
          <Results 
            analysisId={analysisId} 
            onBack={() => setCurrentRoute('home')}
            onNewAnalysis={() => setCurrentRoute('analyze')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
