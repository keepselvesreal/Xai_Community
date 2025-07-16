/**
 * 재사용 가능한 글 작성 폼 컴포넌트
 * 모든 글 작성 페이지의 공통 로직과 UI를 추상화
 */

import React from 'react';
import { useAuth } from '~/contexts/AuthContext';
import AppLayout from '~/components/layout/AppLayout';

export interface PostWriteFormConfig {
  pageTitle: string;
  pageDescription: string;
  submitButtonText: string;
  successMessage: string;
  guidelines: string[];
  titleMaxLength?: number;
  contentMaxLength?: number;
}

export interface PostWriteFormProps<T = any> {
  // 설정
  config: PostWriteFormConfig;
  
  // 폼 데이터
  initialData: T;
  onDataChange: (data: Partial<T>) => void;
  
  // 확장 필드
  extendedFields?: React.ReactNode;
  
  // 이벤트 핸들러
  onSubmit: (data: T) => Promise<void>;
  onCancel: () => void;
  
  // 상태
  isSubmitting: boolean;
  isEditMode?: boolean;
}

export default function PostWriteForm<T extends { title: string; content: string }>({
  config,
  initialData,
  onDataChange,
  extendedFields,
  onSubmit,
  onCancel,
  isSubmitting,
  isEditMode = false,
}: PostWriteFormProps<T>) {
  const { user, logout } = useAuth();

  const {
    pageTitle,
    pageDescription,
    submitButtonText,
    guidelines,
    titleMaxLength = 200,
    contentMaxLength = 10000,
  } = config;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    onDataChange({
      [name]: value,
    } as Partial<T>);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 기본 검증
    if (!initialData.title.trim() || !initialData.content.trim()) {
      return;
    }

    await onSubmit(initialData);
  };

  // 제출 버튼 비활성화 조건
  const isSubmitDisabled = isSubmitting || !initialData.title.trim() || !initialData.content.trim();

  return (
    <AppLayout 
      user={user || { id: 'test', email: 'test@test.com', name: '테스트사용자' }}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-var-primary mb-2">{pageTitle}</h1>
          <p className="text-var-secondary">
            {pageDescription}
          </p>
        </div>

        {/* 글쓰기 폼 */}
        <div className="bg-var-card border border-var-color rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 확장 필드 (카테고리 선택 등) */}
            {extendedFields}

            {/* 제목 입력 */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-var-primary mb-2">
                제목 <span className="text-red-500">*</span>
              </label>
              <input
                id="title"
                type="text"
                name="title"
                value={initialData.title}
                onChange={handleInputChange}
                placeholder="제목을 입력하세요"
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                maxLength={titleMaxLength}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {initialData.title.length}/{titleMaxLength.toLocaleString()}자
              </div>
            </div>

            {/* 내용 입력 */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-var-primary mb-2">
                내용 <span className="text-red-500">*</span>
              </label>
              <textarea
                id="content"
                name="content"
                value={initialData.content}
                onChange={handleInputChange}
                placeholder="내용을 입력하세요"
                rows={12}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent resize-vertical"
                maxLength={contentMaxLength}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {initialData.content.length}/{contentMaxLength.toLocaleString()}자
              </div>
            </div>

            {/* 작성 가이드라인 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">📝 작성 가이드라인</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                {guidelines.map((guideline, index) => (
                  <li key={index}>• {guideline}</li>
                ))}
              </ul>
            </div>

            {/* 버튼 영역 */}
            <div className="flex justify-end gap-3 pt-4 border-t border-var-color">
              <button
                type="button"
                onClick={onCancel}
                disabled={isSubmitting}
                className="px-6 py-3 border border-var-color rounded-lg text-var-secondary hover:bg-var-hover transition-colors duration-200 disabled:opacity-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={isSubmitDisabled}
                className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    작성 중...
                  </>
                ) : (
                  <>
                    ✏️ {submitButtonText}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </AppLayout>
  );
}