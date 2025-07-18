import { useState, useCallback } from "react";
import { InquiryType, InquirySubmissionData } from "~/types/inquiry";
import { inquiryConfigs } from "~/config/inquiryConfigs";
import { apiClient } from "~/lib/api";

// 환경별 API URL 설정 (기존 api.ts와 동일한 방식)
function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  return 'http://localhost:8000';
}

/**
 * 문의 시스템을 위한 커스텀 훅
 */
export const useInquiry = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitInquiry = useCallback(async (data: InquirySubmissionData): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      // 문의 데이터를 PostCreate 구조로 변환
      const postData = {
        title: data.title,
        content: data.content,
        service: data.service,
        metadata: {
          type: data.metadata.type,
          category: data.metadata.category || data.metadata.type,
          tags: [],
          attachments: [],
          file_ids: [],
          inline_images: [],
          editor_type: "plain",
          visibility: "public"
        }
      };

      console.log("문의 제출 요청:", postData);

      // 로그인 여부에 관계없이 문의 제출 가능하도록 직접 fetch 사용
      const response = await fetch(`${getApiBaseUrl()}/api/posts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Authorization 헤더는 선택적으로만 추가
          ...(apiClient.isAuthenticated() ? { 
            "Authorization": `Bearer ${localStorage.getItem('authToken')?.replace(/^Bearer\s+/i, '') || ''}` 
          } : {})
        },
        body: JSON.stringify(postData),
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error("API 응답 오류:", response.status, errorData);
        throw new Error(`문의 제출 실패 (${response.status}): ${errorData}`);
      }

      const result = await response.json();
      console.log("문의 제출 성공:", result);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "문의 제출 중 오류가 발생했습니다.";
      setError(errorMessage);
      console.error("문의 제출 오류:", err);
      throw err; // 호출자에게 에러 전파
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getInquiryConfig = useCallback((type: InquiryType) => {
    return inquiryConfigs[type];
  }, []);

  return {
    submitInquiry,
    getInquiryConfig,
    isLoading,
    error,
    clearError: () => setError(null)
  };
};