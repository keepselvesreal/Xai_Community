interface CommentCountProps {
  count: number;
  itemId?: number;
  itemType?: 'post' | 'info' | 'service' | 'tip';
  onCommentClick?: (itemId: number, itemType: string) => void;
  className?: string;
}

export default function CommentCount({ 
  count, 
  itemId, 
  itemType, 
  onCommentClick, 
  className = "" 
}: CommentCountProps) {
  const handleClick = () => {
    if (onCommentClick && itemId && itemType) {
      onCommentClick(itemId, itemType);
    }
  };

  const isClickable = onCommentClick && itemId && itemType;

  return (
    <span
      onClick={isClickable ? handleClick : undefined}
      className={`flex items-center gap-1 text-var-muted ${
        isClickable ? 'hover:text-accent-primary cursor-pointer' : ''
      } ${className}`}
    >
      💬 {count}
    </span>
  );
}