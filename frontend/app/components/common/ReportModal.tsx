import { useState, useCallback } from "react";
import Modal from "~/components/ui/Modal";
import Button from "~/components/ui/Button";
import Textarea from "~/components/ui/Textarea";

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetType: "post" | "comment";
  targetId: string;
  onSubmit: (content: string) => Promise<void>;
  isLoading?: boolean;
}

const ReportModal = ({ 
  isOpen, 
  onClose, 
  targetType, 
  targetId, 
  onSubmit, 
  isLoading = false 
}: ReportModalProps) => {
  const [content, setContent] = useState("");
  const [error, setError] = useState("");

  const validateContent = useCallback((value: string | any): string | null => {
    // 타입 가드: value가 문자열이 아닌 경우 문자열로 변환
    const stringValue = typeof value === 'string' ? value : String(value || '');
    
    if (!stringValue.trim()) {
      return "신고 내용은 필수 입력 항목입니다.";
    }
    if (stringValue.length < 10) {
      return "신고 내용은 최소 10자 이상 입력해야 합니다.";
    }
    if (stringValue.length > 1000) {
      return "신고 내용은 최대 1000자까지 입력 가능합니다.";
    }
    return null;
  }, []);

  const handleContentChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = event.target.value;
    setContent(value);
    
    // 실시간 검증
    const validationError = validateContent(value);
    setError(validationError || "");
  }, [validateContent]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateContent(content);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      await onSubmit(content);
      
      // 성공 후 초기화
      setContent("");
      setError("");
      onClose();
    } catch (error) {
      console.error("신고 제출 실패:", error);
      setError("신고 제출 중 오류가 발생했습니다. 다시 시도해주세요.");
    }
  }, [content, validateContent, onSubmit, onClose]);

  const handleClose = useCallback(() => {
    setContent("");
    setError("");
    onClose();
  }, [onClose]);

  // 안전한 문자열 변환 및 trim 함수
  const safeStringTrim = useCallback((value: any): string => {
    const stringValue = typeof value === 'string' ? value : String(value || '');
    return stringValue.trim();
  }, []);

  const targetText = targetType === "post" ? "게시글" : "댓글";

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="신고하기">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            이 {targetText}을 신고하는 이유를 작성해주세요.
          </p>
        </div>

        <div>
          <label htmlFor="report-content" className="block text-sm font-medium text-gray-700 mb-1">
            신고 내용 *
          </label>
          <Textarea
            id="report-content"
            value={content}
            onChange={handleContentChange}
            placeholder="신고 사유를 자세히 작성해주세요. (최소 10자 이상)"
            rows={6}
            className={error ? "border-red-500" : ""}
            disabled={isLoading}
          />
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            onClick={handleClose}
            variant="secondary"
            disabled={isLoading}
          >
            취소
          </Button>
          <Button
            type="submit"
            disabled={isLoading || !!error || !safeStringTrim(content)}
            className="bg-red-600 hover:bg-red-700"
          >
            {isLoading ? "신고 중..." : "신고하기"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default ReportModal;