import { useState } from "react";
import type { ReactionBarProps } from "~/types";

export default function ReactionBar({
  reactions,
  onReactionClick,
  showSave = false,
  itemId,
  itemType
}: ReactionBarProps) {
  const [userReactions, setUserReactions] = useState({
    liked: false,
    disliked: false,
    saved: false
  });

  const handleReactionClick = (type: 'like' | 'dislike' | 'save') => {
    if (onReactionClick) {
      onReactionClick(type);
    }
    
    // 로컬 상태 업데이트 (API 연동 전 임시)
    setUserReactions(prev => {
      const newState = { ...prev };
      
      if (type === 'like') {
        newState.liked = !prev.liked;
        if (newState.liked) newState.disliked = false; // 좋아요 누르면 싫어요 해제
      } else if (type === 'dislike') {
        newState.disliked = !prev.disliked;
        if (newState.disliked) newState.liked = false; // 싫어요 누르면 좋아요 해제
      } else if (type === 'save') {
        newState.saved = !prev.saved;
      }
      
      return newState;
    });
  };

  return (
    <div className="flex items-center gap-3 text-sm text-var-muted">
      {/* 조회수 */}
      <span className="flex items-center gap-1">
        👁️ {reactions.views}
      </span>

      {/* 좋아요 */}
      <button
        onClick={() => handleReactionClick('like')}
        className={`flex items-center gap-1 hover:text-accent-primary transition-colors ${
          userReactions.liked ? 'text-accent-primary' : ''
        }`}
      >
        👍 {reactions.likes + (userReactions.liked ? 1 : 0)}
      </button>

      {/* 싫어요 */}
      <button
        onClick={() => handleReactionClick('dislike')}
        className={`flex items-center gap-1 hover:text-red-500 transition-colors ${
          userReactions.disliked ? 'text-red-500' : ''
        }`}
      >
        👎 {reactions.dislikes + (userReactions.disliked ? 1 : 0)}
      </button>

      {/* 댓글 */}
      <span className="flex items-center gap-1">
        💬 {reactions.comments}
      </span>

      {/* 저장 (선택적) */}
      {showSave && reactions.saves !== undefined && (
        <button
          onClick={() => handleReactionClick('save')}
          className={`flex items-center gap-1 hover:text-yellow-500 transition-colors ${
            userReactions.saved ? 'text-yellow-500' : ''
          }`}
        >
          📌 {reactions.saves + (userReactions.saved ? 1 : 0)}
        </button>
      )}
    </div>
  );
}