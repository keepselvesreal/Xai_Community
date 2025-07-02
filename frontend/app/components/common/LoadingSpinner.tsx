interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'accent';
  text?: string;
  fullscreen?: boolean;
  className?: string;
}

export default function LoadingSpinner({
  size = 'md',
  color = 'accent',
  text,
  fullscreen = false,
  className = ''
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  const colorClasses = {
    primary: 'border-var-primary',
    secondary: 'border-var-secondary',
    accent: 'border-accent-primary'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  const spinner = (
    <div 
      className={`flex flex-col items-center justify-center gap-3 ${className}`}
      role="status"
      aria-label={text || "Loading"}
    >
      <div
        className={`
          ${sizeClasses[size]}
          ${colorClasses[color]}
          border-2
          border-t-transparent
          rounded-full
          animate-spin
        `}
      />
      {text && (
        <p className={`${textSizeClasses[size]} text-var-secondary font-medium`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-var-primary bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-var-card rounded-xl p-8 shadow-lg">
          {spinner}
        </div>
      </div>
    );
  }

  return spinner;
}

// 인라인 로딩 컴포넌트 (텍스트와 함께 사용)
export function InlineLoader({ 
  size = 'sm', 
  className = '' 
}: Pick<LoadingSpinnerProps, 'size' | 'className'>) {
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  return (
    <div
      className={`
        ${sizeClasses[size]}
        border-2
        border-accent-primary
        border-t-transparent
        rounded-full
        animate-spin
        inline-block
        ${className}
      `}
    />
  );
}

// 페이지 로딩 컴포넌트
export function PageLoader({ text = "페이지를 불러오는 중..." }: { text?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-var-primary">
      <LoadingSpinner size="lg" text={text} />
    </div>
  );
}

// 섹션 로딩 컴포넌트
export function SectionLoader({ text, height = "200px" }: { text?: string; height?: string }) {
  return (
    <div 
      className="flex items-center justify-center bg-var-card rounded-xl border border-var-color"
      style={{ height }}
    >
      <LoadingSpinner size="md" text={text} />
    </div>
  );
}