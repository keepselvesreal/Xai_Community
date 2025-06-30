import { useState, useCallback } from "react";
import type { ItemReactions } from "~/types";

export interface UseReactionsOptions {
  itemId: number;
  itemType: 'post' | 'info' | 'service' | 'tip';
  initialReactions: ItemReactions;
}

export function useReactions({
  itemId,
  itemType,
  initialReactions
}: UseReactionsOptions) {
  const [reactions, setReactions] = useState(initialReactions);
  const [userReactions, setUserReactions] = useState({
    liked: false,
    disliked: false,
    saved: false
  });

  // 좋아요 핸들러
  const handleLike = useCallback(async () => {
    const wasLiked = userReactions.liked;
    const wasDisliked = userReactions.disliked;
    
    setUserReactions(prev => ({
      ...prev,
      liked: !wasLiked,
      disliked: false // 좋아요 누르면 싫어요 해제
    }));
    
    setReactions(prev => ({
      ...prev,
      likes: prev.likes + (wasLiked ? -1 : 1),
      dislikes: wasDisliked ? prev.dislikes - 1 : prev.dislikes
    }));

    // TODO: API 연동 시 실제 서버 요청
    try {
      // await api.reactions.like(itemId, itemType, !wasLiked);
      console.log(`${wasLiked ? 'Unlike' : 'Like'} ${itemType} ${itemId}`);
    } catch (error) {
      // 실패 시 상태 롤백
      setUserReactions(prev => ({
        ...prev,
        liked: wasLiked,
        disliked: wasDisliked
      }));
      
      setReactions(prev => ({
        ...prev,
        likes: prev.likes + (wasLiked ? 1 : -1),
        dislikes: wasDisliked ? prev.dislikes + 1 : prev.dislikes
      }));
      
      console.error('Failed to update like status:', error);
    }
  }, [itemId, itemType, userReactions.liked, userReactions.disliked]);

  // 싫어요 핸들러
  const handleDislike = useCallback(async () => {
    const wasLiked = userReactions.liked;
    const wasDisliked = userReactions.disliked;
    
    setUserReactions(prev => ({
      ...prev,
      liked: false, // 싫어요 누르면 좋아요 해제
      disliked: !wasDisliked
    }));
    
    setReactions(prev => ({
      ...prev,
      likes: wasLiked ? prev.likes - 1 : prev.likes,
      dislikes: prev.dislikes + (wasDisliked ? -1 : 1)
    }));

    // TODO: API 연동 시 실제 서버 요청
    try {
      // await api.reactions.dislike(itemId, itemType, !wasDisliked);
      console.log(`${wasDisliked ? 'Un-dislike' : 'Dislike'} ${itemType} ${itemId}`);
    } catch (error) {
      // 실패 시 상태 롤백
      setUserReactions(prev => ({
        ...prev,
        liked: wasLiked,
        disliked: wasDisliked
      }));
      
      setReactions(prev => ({
        ...prev,
        likes: wasLiked ? prev.likes + 1 : prev.likes,
        dislikes: prev.dislikes + (wasDisliked ? 1 : -1)
      }));
      
      console.error('Failed to update dislike status:', error);
    }
  }, [itemId, itemType, userReactions.liked, userReactions.disliked]);

  // 저장 핸들러
  const handleSave = useCallback(async () => {
    const wasSaved = userReactions.saved;
    
    setUserReactions(prev => ({
      ...prev,
      saved: !wasSaved
    }));
    
    if (reactions.saves !== undefined) {
      setReactions(prev => ({
        ...prev,
        saves: prev.saves !== undefined ? prev.saves + (wasSaved ? -1 : 1) : 0
      }));
    }

    // TODO: API 연동 시 실제 서버 요청
    try {
      // await api.reactions.save(itemId, itemType, !wasSaved);
      console.log(`${wasSaved ? 'Unsave' : 'Save'} ${itemType} ${itemId}`);
    } catch (error) {
      // 실패 시 상태 롤백
      setUserReactions(prev => ({
        ...prev,
        saved: wasSaved
      }));
      
      if (reactions.saves !== undefined) {
        setReactions(prev => ({
          ...prev,
          saves: prev.saves !== undefined ? prev.saves + (wasSaved ? 1 : -1) : 0
        }));
      }
      
      console.error('Failed to update save status:', error);
    }
  }, [itemId, itemType, userReactions.saved, reactions.saves]);

  // 조회수 증가
  const incrementViews = useCallback(() => {
    setReactions(prev => ({
      ...prev,
      views: prev.views + 1
    }));

    // TODO: API 연동 시 실제 서버 요청
    try {
      // await api.reactions.incrementViews(itemId, itemType);
      console.log(`View ${itemType} ${itemId}`);
    } catch (error) {
      console.error('Failed to increment views:', error);
    }
  }, [itemId, itemType]);

  return {
    reactions,
    userReactions,
    handleLike,
    handleDislike,
    handleSave,
    incrementViews
  };
}