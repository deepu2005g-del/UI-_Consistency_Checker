import { CategoryScore as ICategoryScore } from '../types/analysis';

interface CategoryScoreProps {
  category: ICategoryScore;
}

export function CategoryScore({ category }: CategoryScoreProps) {
  const getScoreColorClass = (value: number) => {
    if (value >= 90) return 'bg-success';
    if (value >= 75) return 'bg-primary';
    if (value >= 60) return 'bg-warning';
    return 'bg-error';
  };
  
  const getTextColorClass = (value: number) => {
    if (value >= 90) return 'text-success';
    if (value >= 75) return 'text-primary';
    if (value >= 60) return 'text-warning';
    return 'text-error';
  };

  return (
    <div className="card p-4 flex flex-col justify-between hover:border-border/80 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-semibold">{category.category}</h3>
        <span className={`font-bold text-lg ${getTextColorClass(category.score)}`}>
          {category.score}%
        </span>
      </div>
      
      <div className="w-full bg-background rounded-full h-2.5 mb-2 overflow-hidden border border-border/50">
        <div 
          className={`h-2.5 rounded-full ${getScoreColorClass(category.score)} transition-all duration-1000 ease-out`} 
          style={{ width: `${category.score}%` }}
        ></div>
      </div>
      
      <div className="flex justify-between items-center mt-2 text-xs">
        <span className="text-textMuted">{category.label}</span>
        {category.issue_count > 0 ? (
          <span className="text-warning bg-warning/10 px-2 py-0.5 rounded-full">
            {category.issue_count} issues
          </span>
        ) : (
          <span className="text-success bg-success/10 px-2 py-0.5 rounded-full">
            Clean
          </span>
        )}
      </div>
    </div>
  );
}
