import { useState, useCallback } from "react";
import { InquiryType, InquirySubmissionData } from "~/types/inquiry";
import { inquiryConfigs } from "~/config/inquiryConfigs";
import { apiClient } from "~/lib/api";

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

      // apiClient를 사용하여 문의 제출 (HTTPS URL 및 인증 처리 자동화)
      const response = await apiClient.createPost(postData);

      if (!response.success) {
        console.error("API 응답 오류:", response.error);
        throw new Error(`문의 제출 실패: ${response.error}`);
      }

      console.log("문의 제출 성공:", response.data);
      
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