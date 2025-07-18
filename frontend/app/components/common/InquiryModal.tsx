import { useState, useCallback } from "react";
import Modal from "~/components/ui/Modal";
import Button from "~/components/ui/Button";
import Input from "~/components/ui/Input";
import Textarea from "~/components/ui/Textarea";
import { InquiryConfig, InquiryFormData, InquirySubmissionData, FieldConfig } from "~/types/inquiry";

interface InquiryModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: InquiryConfig;
  onSubmit: (data: InquirySubmissionData) => Promise<void>;
  isLoading?: boolean;
}

const InquiryModal = ({ isOpen, onClose, config, onSubmit, isLoading = false }: InquiryModalProps) => {
  const [formData, setFormData] = useState<InquiryFormData>({
    name: "",
    content: "",
    contact: "",
    website_url: ""
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateField = useCallback((field: FieldConfig, value: string): string | null => {
    // Required 검증
    if (field.required && !value.trim()) {
      return `${field.label}은(는) 필수 입력 항목입니다.`;
    }

    if (!value.trim()) return null; // 비어있고 required가 아니면 검증 통과

    // 길이 검증
    if (field.minLength && value.length < field.minLength) {
      return `${field.label}은(는) 최소 ${field.minLength}자 이상 입력해야 합니다.`;
    }
    if (field.maxLength && value.length > field.maxLength) {
      return `${field.label}은(는) 최대 ${field.maxLength}자까지 입력 가능합니다.`;
    }

    // 패턴 검증
    if (field.validation?.pattern) {
      const regex = new RegExp(field.validation.pattern);
      if (!regex.test(value)) {
        return field.validation.message || `${field.label} 형식이 올바르지 않습니다.`;
      }
    }

    return null;
  }, []);

  const handleInputChange = useCallback((fieldName: string, value: string) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
    
    // 실시간 검증
    const field = config.fields.find(f => f.name === fieldName);
    if (field) {
      const error = validateField(field, value);
      setErrors(prev => ({
        ...prev,
        [fieldName]: error || ""
      }));
    }
  }, [config.fields, validateField]);

  const validateForm = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    config.fields.forEach(field => {
      const value = formData[field.name] || "";
      const error = validateField(field, value);
      if (error) {
        newErrors[field.name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  }, [config.fields, formData, validateField]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      // content 데이터 구성
      let contentData: string;
      
      const hasExtraFields = config.fields.some(f => f.name === "contact" || f.name === "website_url");
      
      if (hasExtraFields) {
        // 등록 문의: JSON 형태
        const jsonData: Record<string, string> = {};
        config.fields.forEach(field => {
          const value = formData[field.name];
          if (value) {
            jsonData[field.name] = value;
          }
        });
        contentData = JSON.stringify(jsonData);
      } else {
        // 건의/신고: 일반 텍스트 (content 필드만)
        contentData = formData.content || "";
      }

      // 제목 생성 (이름 필드가 있으면 사용, 없으면 기본 제목)
      const titleSuffix = formData.name ? ` - ${formData.name}` : "";
      
      const submissionData: InquirySubmissionData = {
        title: `${config.title}${titleSuffix}`,
        content: contentData,
        service: "residential_community",
        metadata: {
          type: config.type,
          category: config.title
        }
      };

      await onSubmit(submissionData);
      
      // 성공 시 폼 초기화 및 모달 닫기
      setFormData({ name: "", content: "", contact: "", website_url: "" });
      setErrors({});
      onClose();
    } catch (error) {
      console.error("문의 제출 실패:", error);
    }
  }, [config, formData, validateForm, onSubmit, onClose]);

  const renderField = useCallback((field: FieldConfig) => {
    const value = formData[field.name] || "";
    const error = errors[field.name];
    const fieldId = `inquiry-${field.name}`;

    const commonProps = {
      id: fieldId,
      name: field.name,
      value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => 
        handleInputChange(field.name, e.target.value),
      placeholder: field.placeholder,
      required: field.required,
      maxLength: field.maxLength,
      className: error ? "border-red-500 focus:border-red-500" : ""
    };

    return (
      <div key={field.name}>
        <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700 mb-1">
          {field.label}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        
        {field.type === "textarea" ? (
          <Textarea
            {...commonProps}
            rows={3}
          />
        ) : (
          <Input
            {...commonProps}
            type={field.type}
          />
        )}
        
        {error && (
          <p className="text-xs text-red-600 mt-1">{error}</p>
        )}
        
        {field.maxLength && (
          <p className="text-xs text-gray-400 text-right mt-1">
            {value.length}/{field.maxLength}
          </p>
        )}
      </div>
    );
  }, [formData, errors, handleInputChange]);

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title={config.title}
      size="lg"
      className="max-h-[92vh] overflow-hidden"
    >
      <div className="flex flex-col h-full">

        {/* 로그인 안내 */}
        {config.loginNotice && (
          <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
            {config.loginNotice}
          </div>
        )}

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 min-h-0">
            {config.fields.map(renderField)}
          </div>
          
          {/* 버튼 영역 */}
          <div className="flex justify-end gap-3 mt-3 pt-2 border-t border-gray-200 flex-shrink-0">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              취소
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="min-w-[120px]"
            >
              {isLoading ? "제출 중..." : "제출"}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default InquiryModal;