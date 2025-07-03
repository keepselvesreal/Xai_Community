/**
 * 재사용 가능한 태그 입력 컴포넌트
 */

import React from 'react';

interface TagInputProps {
  tags: string[];
  currentTagInput: string;
  onTagInputChange: (value: string) => void;
  onTagKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onRemoveTag: (index: number) => void;
  maxTags?: number;
  placeholder?: string;
  className?: string;
}

export default function TagInput({
  tags,
  currentTagInput,
  onTagInputChange,
  onTagKeyDown,
  onRemoveTag,
  maxTags = 3,
  placeholder = "태그 입력 후 쉼표(,) 또는 엔터",
  className = "",
}: TagInputProps) {
  const canAddMore = tags.length < maxTags;
  const isAtLimit = tags.length >= maxTags;

  return (
    <div>
      <label className="block text-sm font-medium text-var-primary mb-2">
        태그 (선택사항)
      </label>
      
      {/* 태그 컨테이너 */}
      <div className={`w-full min-h-[48px] px-4 py-2 bg-var-section border border-var-color rounded-lg focus-within:ring-2 focus-within:ring-accent-primary focus-within:border-transparent ${className}`}>
        <div className="flex flex-wrap gap-2 items-center">
          {/* 기존 태그들 */}
          {tags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 bg-accent-primary text-white rounded-full text-sm"
            >
              #{tag}
              <button
                type="button"
                onClick={() => onRemoveTag(index)}
                className="ml-1 hover:bg-accent-primary/80 rounded-full p-0.5 transition-colors"
                aria-label={`${tag} 태그 삭제`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))}
          
          {/* 태그 입력 필드 */}
          {canAddMore && (
            <input
              type="text"
              value={currentTagInput}
              onChange={(e) => onTagInputChange(e.target.value)}
              onKeyDown={onTagKeyDown}
              placeholder={tags.length === 0 ? placeholder : ""}
              className="flex-1 min-w-[120px] bg-transparent border-none outline-none text-var-primary placeholder-var-muted"
              maxLength={20}
            />
          )}
        </div>
      </div>
      
      <div className="mt-1 text-xs text-var-muted">
        {!isAtLimit ? (
          <>쉼표(,) 또는 엔터로 태그 추가 • 백스페이스로 태그 삭제 • 최대 {maxTags}개</>
        ) : (
          <span className="text-orange-600">⚠️ 최대 {maxTags}개까지 추가할 수 있습니다</span>
        )}
      </div>
    </div>
  );
}