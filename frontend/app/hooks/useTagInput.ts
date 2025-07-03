/**
 * 태그 입력 관리를 위한 커스텀 훅
 */

import { useState } from "react";

interface UseTagInputOptions {
  maxTags?: number;
  initialTags?: string[];
}

export const useTagInput = ({ maxTags = 3, initialTags = [] }: UseTagInputOptions = {}) => {
  const [tags, setTags] = useState<string[]>(initialTags);
  const [currentTagInput, setCurrentTagInput] = useState("");

  const addTag = (newTag: string) => {
    const trimmedTag = newTag.trim();
    if (trimmedTag && !tags.includes(trimmedTag) && tags.length < maxTags) {
      setTags(prev => [...prev, trimmedTag]);
      return true;
    }
    return false;
  };

  const removeTag = (indexToRemove: number) => {
    setTags(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  const clearCurrentInput = () => {
    setCurrentTagInput("");
  };

  const handleTagInput = (value: string) => {
    // 쉼표가 입력되면 태그 추가
    if (value.includes(',')) {
      const newTag = value.replace(',', '').trim();
      if (addTag(newTag)) {
        clearCurrentInput();
      } else {
        setCurrentTagInput(value.replace(',', ''));
      }
    } else {
      setCurrentTagInput(value);
    }
  };

  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const newTag = currentTagInput.trim();
      if (addTag(newTag)) {
        clearCurrentInput();
      }
    } else if (e.key === 'Backspace' && currentTagInput === '' && tags.length > 0) {
      // 백스페이스로 마지막 태그 삭제
      removeTag(tags.length - 1);
    }
  };

  const setInitialTags = (newTags: string[]) => {
    console.log('🏷️ useTagInput - setInitialTags 호출:', newTags);
    setTags(newTags);
    console.log('🏷️ useTagInput - tags 상태 업데이트 완료');
  };

  return {
    tags,
    currentTagInput,
    setCurrentTagInput,
    addTag,
    removeTag,
    handleTagInput,
    handleTagKeyDown,
    clearCurrentInput,
    setInitialTags,
    canAddMore: tags.length < maxTags,
    isAtLimit: tags.length >= maxTags,
  };
};