import { useState } from "react";

interface SaveButtonProps {
  count?: number;
  itemId?: number;
  itemType?: 'post' | 'info' | 'service' | 'tip';
  onSave?: (itemId: number, itemType: string) => void;
  className?: string;
}

export default function SaveButton({ 
  count, 
  itemId, 
  itemType, 
  onSave, 
  className = "" 
}: SaveButtonProps) {
  const [isSaved, setIsSaved] = useState(false);

  const handleClick = () => {
    setIsSaved(!isSaved);
    if (onSave && itemId && itemType) {
      onSave(itemId, itemType);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-1 hover:text-yellow-500 transition-colors ${
        isSaved ? 'text-yellow-500' : 'text-var-muted'
      } ${className}`}
    >
      📌 {count !== undefined ? count + (isSaved ? 1 : 0) : (isSaved ? '저장됨' : '저장')}
    </button>
  );
}