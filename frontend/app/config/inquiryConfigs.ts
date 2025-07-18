import { InquiryConfig, InquiryType } from "~/types/inquiry";

/**
 * 문의 타입별 설정
 */
export const inquiryConfigs: Record<InquiryType, InquiryConfig> = {
  "moving-services-register-inquiry": {
    type: "moving-services-register-inquiry",
    title: "입주 서비스 업체 등록 문의",
    description: "입주 서비스 업체로 등록을 원하시면 아래 정보를 입력해 주세요.",
    fields: [
      {
        name: "name",
        label: "담당자명",
        type: "text",
        required: true,
        placeholder: "담당자명을 입력해 주세요",
        maxLength: 50,
        minLength: 2
      },
      {
        name: "content",
        label: "서비스 설명",
        type: "textarea",
        required: true,
        placeholder: "제공하시는 입주 서비스에 대해 자세히 설명해 주세요",
        maxLength: 1000,
        minLength: 10
      },
      {
        name: "contact",
        label: "연락처",
        type: "tel",
        required: true,
        placeholder: "010-1234-5678",
        validation: {
          pattern: "^01[0-9]-[0-9]{3,4}-[0-9]{4}$",
          message: "올바른 휴대폰 번호 형식으로 입력해 주세요 (010-1234-5678)"
        }
      },
      {
        name: "website_url",
        label: "참고 URL",
        type: "url",
        required: false,
        placeholder: "https://example.com",
        validation: {
          pattern: "^https?://.+",
          message: "올바른 웹사이트 URL을 입력해 주세요"
        }
      }
    ],
    submitButtonText: "제출",
    loginNotice: "로그인 후 작성 시 작성 기록을 내 공간 페이지에서 확인할 수 있습니다."
  },

  "expert-tips-register-inquiry": {
    type: "expert-tips-register-inquiry",
    title: "전문가의 꿀정보 등록 문의",
    description: "전문가로 등록하여 꿀정보를 공유하고 싶으시면 아래 정보를 입력해 주세요.",
    fields: [
      {
        name: "name",
        label: "전문가명",
        type: "text",
        required: true,
        placeholder: "전문가명을 입력해 주세요",
        maxLength: 50,
        minLength: 2
      },
      {
        name: "content",
        label: "전문 분야 및 경력",
        type: "textarea",
        required: true,
        placeholder: "전문 분야와 관련 경력을 자세히 설명해 주세요",
        maxLength: 1000,
        minLength: 10
      },
      {
        name: "contact",
        label: "연락처",
        type: "tel",
        required: true,
        placeholder: "010-1234-5678",
        validation: {
          pattern: "^01[0-9]-[0-9]{3,4}-[0-9]{4}$",
          message: "올바른 휴대폰 번호 형식으로 입력해 주세요 (010-1234-5678)"
        }
      },
      {
        name: "website_url",
        label: "참고 URL",
        type: "url",
        required: false,
        placeholder: "https://example.com",
        validation: {
          pattern: "^https?://.+",
          message: "올바른 웹사이트 URL을 입력해 주세요"
        }
      }
    ],
    submitButtonText: "제출",
    loginNotice: "로그인 후 작성 시 작성 기록을 내 공간 페이지에서 확인할 수 있습니다."
  },

  "suggestions": {
    type: "suggestions",
    title: "건의함",
    fields: [
      {
        name: "content",
        label: "건의 내용",
        type: "textarea",
        required: true,
        placeholder: "서비스 개선을 위한 소중한 의견을 들려주세요.\n건의하고 싶은 내용을 자세히 작성해 주세요.",
        maxLength: 1000
      }
    ],
    submitButtonText: "제출",
    loginNotice: "로그인 후 작성 시 작성 기록을 내 공간 페이지에서 확인할 수 있습니다."
  },

  "report": {
    type: "report",
    title: "신고",
    fields: [
      {
        name: "content",
        label: "신고 내용",
        type: "textarea",
        required: true,
        placeholder: "부적절한 내용이나 사용자를 신고해 주세요.\n신고 사유와 상세 내용을 작성해 주세요.",
        maxLength: 1000,
        minLength: 10
      }
    ],
    submitButtonText: "제출",
    loginNotice: "로그인 후 작성 시 작성 기록을 내 공간 페이지에서 확인할 수 있습니다."
  }
};