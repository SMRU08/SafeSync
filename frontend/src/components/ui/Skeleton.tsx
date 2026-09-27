import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'rectangular' | 'circular' | 'rounded';
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rounded',
  style,
}) => {
  const variantClass =
    variant === 'circular'
      ? 'rounded-full'
      : variant === 'rectangular'
      ? 'rounded-none'
      : 'rounded-lg';

  return (
    <div
      className={`animate-shimmer bg-slate-800/60 border border-slate-700/30 ${variantClass} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
};

export const CardSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => {
  return (
    <div className="glass-card rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" className="w-10 h-10 flex-shrink-0" />
        <div className="space-y-1.5 flex-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <div className="pt-2 border-t border-slate-800/60 space-y-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex justify-between items-center">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
    </div>
  );
};

export const TableSkeleton: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 5,
}) => {
  return (
    <div className="glass-card rounded-xl overflow-hidden border border-slate-800/80">
      <div className="p-3.5 bg-slate-900/60 border-b border-slate-800 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      <div className="divide-y divide-slate-800/60 p-2 space-y-2">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex items-center gap-4 py-2 px-2">
            {Array.from({ length: cols }).map((_, c) => (
              <Skeleton key={c} className="h-3.5 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export const CameraSkeleton: React.FC = () => {
  return (
    <div className="glass-card rounded-xl border border-slate-800/80 overflow-hidden flex flex-col">
      <div className="px-3.5 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skeleton variant="circular" className="w-2.5 h-2.5" />
          <Skeleton className="h-4 w-28" />
        </div>
        <Skeleton className="h-4 w-14 rounded-full" />
      </div>
      <div className="aspect-video bg-slate-950 flex flex-col items-center justify-center p-6">
        <Skeleton className="w-12 h-12 rounded-xl mb-3" />
        <Skeleton className="h-3 w-36 mb-1.5" />
        <Skeleton className="h-2 w-24" />
      </div>
    </div>
  );
};

export const ChartSkeleton: React.FC<{ height?: number }> = ({ height = 260 }) => {
  return (
    <div className="glass-card rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="space-y-1">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-32" />
        </div>
        <Skeleton className="h-7 w-24 rounded-lg" />
      </div>
      <div
        className="w-full flex items-end gap-3 pt-6 px-2"
        style={{ height: `${height}px` }}
      >
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t-md"
            style={{ height: `${20 + ((i * 19) % 75)}%` }}
          />
        ))}
      </div>
    </div>
  );
};

export const IncidentSkeleton: React.FC = () => {
  return (
    <div className="glass-card rounded-xl p-4 border border-slate-800/80 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <Skeleton variant="circular" className="w-8 h-8 flex-shrink-0" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-36" />
            <Skeleton className="h-3 w-28" />
          </div>
        </div>
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
      <Skeleton className="h-10 w-full rounded-lg" />
      <div className="flex justify-between items-center pt-2 border-t border-slate-800/60">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-7 w-20 rounded-md" />
      </div>
    </div>
  );
};
