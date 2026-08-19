import { useState, useRef } from 'react';
import { UploadCloud, X, Image as ImageIcon } from 'lucide-react';

interface UploadZoneProps {
  onAnalyze: (files: File[]) => void;
  isLoading: boolean;
}

export function UploadZone({ onAnalyze, isLoading }: UploadZoneProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    setError('');
    
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    const validFiles = newFiles.filter(file => validTypes.includes(file.type));
    
    if (validFiles.length !== newFiles.length) {
      setError('Some files were ignored. Only PNG, JPG, JPEG, and WEBP are allowed.');
    }

    setFiles(prev => {
      const existingNames = new Set(prev.map(f => f.name));
      const uniqueNewFiles = validFiles.filter(f => !existingNames.has(f.name));
      return [...prev, ...uniqueNewFiles];
    });
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleAnalyzeClick = () => {
    if (files.length < 2) {
      setError('Please upload at least 2 screenshots for consistency analysis.');
      return;
    }
    setError('');
    onAnalyze(files);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div 
        className="border-2 border-dashed border-border rounded-xl p-10 text-center hover:bg-surface/50 transition-colors cursor-pointer"
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          multiple 
          accept="image/png, image/jpeg, image/jpg, image/webp"
          className="hidden" 
          ref={fileInputRef}
          onChange={handleFileInput}
        />
        <div className="flex justify-center mb-4 text-primary">
          <UploadCloud size={48} />
        </div>
        <h3 className="text-xl font-medium mb-2">Drag & Drop Screenshots</h3>
        <p className="text-textMuted mb-4">or click to browse files</p>
        <p className="text-sm text-textMuted/70">Support PNG, JPG, WEBP (Max 10MB per file)</p>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-error/10 border border-error/50 rounded-lg text-error text-sm">
          {error}
        </div>
      )}

      {files.length > 0 && (
        <div className="mt-8">
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-medium text-lg">Selected Screenshots ({files.length})</h4>
            <button 
              className="text-textMuted hover:text-text text-sm transition-colors"
              onClick={() => setFiles([])}
            >
              Clear All
            </button>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
            {files.map((file, index) => (
              <div key={`${file.name}-${index}`} className="relative group bg-surface border border-border rounded-lg overflow-hidden">
                <div className="aspect-video bg-black/20 flex items-center justify-center p-2">
                  {/* Using object URL for preview */}
                  <img 
                    src={URL.createObjectURL(file)} 
                    alt={file.name} 
                    className="max-w-full max-h-full object-contain"
                    onLoad={(e) => URL.revokeObjectURL((e.target as HTMLImageElement).src)}
                  />
                </div>
                <div className="p-2 border-t border-border flex items-center gap-2 bg-surface">
                  <ImageIcon size={14} className="text-primary flex-shrink-0" />
                  <span className="text-xs truncate text-textMuted" title={file.name}>{file.name}</span>
                </div>
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="absolute top-2 right-2 bg-black/60 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-error"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <button 
              className="btn-primary w-full md:w-auto px-8"
              onClick={handleAnalyzeClick}
              disabled={isLoading || files.length < 2}
            >
              {isLoading ? 'Uploading...' : 'Analyze Screenshots'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
