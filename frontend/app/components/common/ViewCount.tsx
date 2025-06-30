interface ViewCountProps {
  count: number;
  className?: string;
}

export default function ViewCount({ count, className = "" }: ViewCountProps) {
  return (
    <span className={`flex items-center gap-1 text-var-muted ${className}`}>
      👁️ {count}
    </span>
  );
}