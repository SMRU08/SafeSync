import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = Inbox,
  title,
  description,
  actionText,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`glass-card rounded-2xl p-8 flex flex-col items-center justify-center text-center border border-slate-800/80 shadow-xl ${className}`}
    >
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-4 shadow-inner">
        <Icon className="w-8 h-8 text-sky-400/80 animate-pulse" />
      </div>
      <h3 className="text-base font-bold text-slate-200 tracking-tight mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-5">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 active:scale-95 text-white text-xs font-semibold rounded-lg shadow-lg shadow-sky-600/30 transition-all duration-200 flex items-center gap-2"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
