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
  titleLabel?: string; // 제목 필드 라벨 커스터마이징
  contentLabel?: string; // 내용 필드 라벨 커스터마이징
}

export interface PostWriteFormProps<T = Record<string, unknown>> {
  // 설정
  config: PostWriteFormConfig;
  
  // 폼 데이터
  initialData: T;
  onDataChange: (data: Partial<T>) => void;
  
  // 확장 필드
  extendedFields?: React.ReactNode;
  afterTitleFields?: React.ReactNode; // 제목 뒤에 올 필드들
  afterContentFields?: React.ReactNode;
  
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
  afterTitleFields,
  afterContentFields,
  onSubmit,
  onCancel,
  isSubmitting,
  isEditMode = false, // eslint-disable-line @typescript-eslint/no-unused-vars
}: PostWriteFormProps<T>) {
  const { user, logout } = useAuth();

  const {
    pageTitle,
    pageDescription,
    submitButtonText,
    guidelines,
    titleMaxLength = 200,
    contentMaxLength = 10000,
    titleLabel = "제목",
    contentLabel = "내용",
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
      user={user}
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
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-3">
                {titleLabel} <span className="text-red-500">*</span>
              </label>
              <input
                id="title"
                type="text"
                name="title"
                value={initialData.title}
                onChange={handleInputChange}
                placeholder={titleLabel === "업체명" ? "업체명을 입력하세요" : "제목을 입력하세요"}
                className="w-full px-4 py-3 bg-white border border-[#52C41A] rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#52C41A] focus:border-transparent"
                maxLength={titleMaxLength}
              />
              <div className="mt-2 text-xs text-gray-500 text-right">
                {initialData.title.length}/{titleMaxLength.toLocaleString()}자
              </div>
            </div>

            {/* 제목 후 필드 (연락처, 서비스 목록 등) */}
            {afterTitleFields}

            {/* 내용 입력 */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-3">
                {contentLabel}
              </label>
              <textarea
                id="content"
                name="content"
                value={initialData.content}
                onChange={handleInputChange}
                placeholder={contentLabel === "업체 소개" ? "업체 소개를 입력하세요..." : "내용을 입력하세요"}
                rows={6}
                className="w-full px-4 py-3 bg-white border border-[#52C41A] rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#52C41A] focus:border-transparent resize-vertical"
                maxLength={contentMaxLength}
              />
              <div className="mt-2 text-xs text-gray-500 text-right">
                {initialData.content.length}/{contentMaxLength.toLocaleString()}자
              </div>
            </div>

            {/* 내용 후 필드 (예: 태그 입력) */}
            {afterContentFields}

            {/* 가이드라인 */}
            {guidelines.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📝 작성 가이드라인</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  {guidelines.map((guideline, index) => (
                    <li key={index}>• {guideline}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 버튼 영역 */}
            <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onCancel}
                disabled={isSubmitting}
                className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors duration-200 disabled:opacity-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={isSubmitDisabled}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    작성 중...
                  </>
                ) : (
                  <>
                    <span>📝</span>
                    <span>{submitButtonText}</span>
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