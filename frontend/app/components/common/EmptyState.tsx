interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export default function EmptyState({
  icon = "📭",
  title,
  description,
  action,
  className = ""
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center text-center p-12 ${className}`}>
      <div className="text-6xl mb-4">{icon}</div>
      
      <h3 className="text-var-primary font-semibold text-lg mb-2">
        {title}
      </h3>
      
      {description && (
        <p className="text-var-secondary mb-6 max-w-md">
          {description}
        </p>
      )}
      
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-accent-primary text-white rounded-xl font-medium hover:bg-accent-hover transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}