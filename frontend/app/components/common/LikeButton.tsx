import { useState } from "react";

interface LikeButtonProps {
  count: number;
  itemId?: number;
  itemType?: 'post' | 'info' | 'service' | 'tip';
  onLike?: (itemId: number, itemType: string) => void;
  className?: string;
}

export default function LikeButton({ 
  count, 
  itemId, 
  itemType, 
  onLike, 
  className = "" 
}: LikeButtonProps) {
  const [isLiked, setIsLiked] = useState(false);

  const handleClick = () => {
    setIsLiked(!isLiked);
    if (onLike && itemId && itemType) {
      onLike(itemId, itemType);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-1 hover:text-accent-primary transition-colors ${
        isLiked ? 'text-accent-primary' : 'text-var-muted'
      } ${className}`}
    >
      👍 {count + (isLiked ? 1 : 0)}
    </button>
  );
}