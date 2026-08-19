import { OverallScore } from '../types/analysis';
import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts';

interface ScoreCardProps {
  score: OverallScore;
}

export function ScoreCard({ score }: ScoreCardProps) {
  const getScoreColor = (value: number) => {
    if (value >= 90) return '#10B981'; // Emerald 500
    if (value >= 75) return '#3B82F6'; // Blue 500
    if (value >= 60) return '#F59E0B'; // Amber 500
    return '#EF4444'; // Red 500
  };

  const data = [
    {
      name: 'Score',
      value: score.score,
      fill: getScoreColor(score.score),
    }
  ];

  return (
    <div className="card flex flex-col md:flex-row items-center gap-8 bg-gradient-to-br from-surface to-surface/50 border-primary/20">
      <div className="w-48 h-48 relative flex-shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart 
            cx="50%" 
            cy="50%" 
            innerRadius="75%" 
            outerRadius="100%" 
            barSize={12} 
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: '#334155' }}
              dataKey="value"
              cornerRadius={10}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color: getScoreColor(score.score) }}>
            {score.score}%
          </span>
        </div>
      </div>
      
      <div className="flex-1 text-center md:text-left">
        <h2 className="text-3xl font-bold mb-2">
          {score.label} UI Consistency
        </h2>
        <p className="text-textMuted mb-6 max-w-lg">
          Based on our AI analysis across the provided pages, your UI consistency score is {score.score}%. 
          We found a total of {score.total_issues} issues that you might want to review.
        </p>
        
        <div className="flex flex-wrap justify-center md:justify-start gap-4">
          {score.high_issues > 0 && (
            <div className="flex items-center gap-2 bg-error/10 border border-error/30 px-3 py-1.5 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-error"></div>
              <span className="text-sm font-medium text-error">{score.high_issues} High Priority</span>
            </div>
          )}
          {score.medium_issues > 0 && (
            <div className="flex items-center gap-2 bg-warning/10 border border-warning/30 px-3 py-1.5 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-warning"></div>
              <span className="text-sm font-medium text-warning">{score.medium_issues} Medium</span>
            </div>
          )}
          {score.low_issues > 0 && (
            <div className="flex items-center gap-2 bg-success/10 border border-success/30 px-3 py-1.5 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-success"></div>
              <span className="text-sm font-medium text-success">{score.low_issues} Low</span>
            </div>
          )}
          {score.total_issues === 0 && (
            <div className="flex items-center gap-2 bg-success/10 border border-success/30 px-3 py-1.5 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-success"></div>
              <span className="text-sm font-medium text-success">Perfect consistency!</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
