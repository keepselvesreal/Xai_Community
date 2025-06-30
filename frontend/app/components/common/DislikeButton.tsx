import { useState } from "react";

interface DislikeButtonProps {
  count: number;
  itemId?: number;
  itemType?: 'post' | 'info' | 'service' | 'tip';
  onDislike?: (itemId: number, itemType: string) => void;
  className?: string;
}

export default function DislikeButton({ 
  count, 
  itemId, 
  itemType, 
  onDislike, 
  className = "" 
}: DislikeButtonProps) {
  const [isDisliked, setIsDisliked] = useState(false);

  const handleClick = () => {
    setIsDisliked(!isDisliked);
    if (onDislike && itemId && itemType) {
      onDislike(itemId, itemType);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-1 hover:text-red-500 transition-colors ${
        isDisliked ? 'text-red-500' : 'text-var-muted'
      } ${className}`}
    >
      👎 {count + (isDisliked ? 1 : 0)}
    </button>
  );
}