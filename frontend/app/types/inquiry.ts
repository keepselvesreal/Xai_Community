/**
 * 문의 및 신고 시스템을 위한 타입 정의
 */

export type InquiryType = 
  | "moving-services-register-inquiry"    // 입주 서비스 업체 등록 문의
  | "expert-tips-register-inquiry"        // 전문가의 꿀정보 등록 문의
  | "suggestions"                         // 건의함
  | "report";                            // 신고

export type FieldType = "text" | "textarea" | "email" | "tel" | "url";

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  required: boolean;
  placeholder?: string;
  maxLength?: number;
  minLength?: number;
  validation?: {
    pattern?: string;
    message?: string;
  };
}

export interface InquiryConfig {
  type: InquiryType;
  title: string;
  description?: string;
  fields: FieldConfig[];
  submitButtonText: string;
  loginNotice?: string;
}

export interface InquiryFormData {
  name: string;
  content: string;
  contact?: string;
  website_url?: string;
  [key: string]: string | undefined;
}

export interface InquirySubmissionData {
  title: string;
  content: string; // JSON string for register inquiries, plain text for others
  service: "residential_community";
  metadata: {
    type: InquiryType;
    category?: string;
  };
}