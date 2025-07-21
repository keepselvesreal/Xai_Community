import { useState, useCallback } from "react";
import * as React from "react";
import { useNavigate } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import PostWriteForm, { type PostWriteFormConfig } from "~/components/common/PostWriteForm";
import TagInput from "~/components/common/TagInput";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { useTagInput } from "~/hooks/useTagInput";
import { apiClient } from "~/lib/api";
import type { CreatePostRequest, CategoryType, ExpertTipFormData } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "꿀정보 작성 | XAI 아파트 커뮤니티" },
    { name: "description", content: "전문가 꿀정보를 작성해보세요" },
  ];
};

const categories = [
  { value: "cleaning", label: "청소/정리" },
  { value: "interior", label: "인테리어" },
  { value: "lifestyle", label: "생활" },
  { value: "saving", label: "절약" },
  { value: "pets", label: "반려동물" }
];

// 카테고리 value를 label로 변환하는 함수
const getCategoryLabel = (value: string): CategoryType => {
  const category = categories.find(cat => cat.value === value);
  return (category?.label as CategoryType) || "생활";
};

export default function TipsWrite() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showSuccess, showError } = useNotification();

  // 글쓰기 권한 체크
  const hasWritePermission = () => {
    if (!user) return false;
    if (user.is_admin) return true;
    return user.can_write_expert_tips || false;
  };

  // 컴포넌트 마운트 시 권한 체크
  React.useEffect(() => {
    if (!user) {
      showError("로그인이 필요합니다.");
      navigate("/auth/login");
      return;
    }

    if (!hasWritePermission()) {
      showError("전문가 꿀정보를 작성할 권한이 없습니다. 관리자에게 문의해주세요.");
      navigate("/tips");
      return;
    }
  }, [user, navigate, showError]);

  // 권한이 없으면 로딩 상태 표시
  if (!user || !hasWritePermission()) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-500">권한을 확인하고 있습니다...</p>
        </div>
      </div>
    );
  }
  
  const [formData, setFormData] = useState<ExpertTipFormData>({
    title: "",
    content: "",
    category: "lifestyle",
    introduction: "",
    tags: []
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 태그 입력 훅 사용 (전문가 꿀정보는 최대 5개)
  const {
    tags,
    currentTagInput,
    handleTagInput,
    handleTagKeyDown,
    removeTag,
    canAddMore,
    isAtLimit
  } = useTagInput({ maxTags: 5, initialTags: formData.tags });

  // PostWriteForm 데이터 변경 핸들러
  const handleFormDataChange = useCallback((data: Partial<ExpertTipFormData>) => {
    setFormData(prev => ({ ...prev, ...data }));
  }, []);

  const handleSubmit = async (data: ExpertTipFormData) => {
    // 자기소개 필드 검증
    if (!data.introduction.trim()) {
      showError("자기소개를 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    
    try {
      // JSON 형태로 content 구성 (자기소개 + 내용)
      const contentData = {
        introduction: data.introduction.trim(),
        content: data.content.trim()
      };

      // 백엔드 API 호출 데이터 구성
      const postData: CreatePostRequest = {
        title: data.title.trim(),
        content: JSON.stringify(contentData),
        service: "residential_community",
        metadata: {
          type: "expert_tips",
          category: getCategoryLabel(data.category),
          tags: tags.length > 0 ? tags : undefined,
          expert_name: user?.display_name || user?.user_handle || "익명 전문가",
        }
      };

      const response = await apiClient.createPost(postData);
      
      if (response.success && response.data) {
        showSuccess("전문가 꿀정보가 성공적으로 작성되었습니다!");
        navigate("/tips");
      } else {
        showError(response.error || "꿀정보 작성에 실패했습니다.");
      }
    } catch (error) {
      showError("꿀정보 작성 중 오류가 발생했습니다.");
      console.error("꿀정보 작성 오류:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = useCallback(() => {
    navigate("/tips");
  }, [navigate]);

  // PostWriteForm 설정
  const config: PostWriteFormConfig = {
    pageTitle: "전문가 꿀정보 작성",
    pageDescription: "당신만의 전문 노하우와 꿀팁을 공유해보세요",
    submitButtonText: "💡 꿀정보 작성",
    successMessage: "전문가 꿀정보가 성공적으로 작성되었습니다!",
    guidelines: [
      "검증된 전문 지식을 바탕으로 실용적인 팁을 제공해주세요",
      "단계별로 쉽게 따라할 수 있도록 구체적으로 설명해주세요",
      "안전상 주의사항이 있다면 반드시 명시해주세요",
      "전문가로서의 경험과 노하우를 공유해주세요",
      "관련 태그를 활용해 다른 주민들이 쉽게 찾을 수 있도록 해주세요"
    ],
    titleMaxLength: 200,
    contentMaxLength: 15000
  };

  // 확장 필드: 카테고리 선택 + 자기소개
  const extendedFields = (
    <>
      {/* 전문 분야 선택 */}
      <div>
        <label className="block text-sm font-medium text-var-primary mb-2">
          전문 분야 <span className="text-red-500">*</span>
        </label>
        <select
          name="category"
          value={formData.category}
          onChange={(e) => handleFormDataChange({ category: e.target.value })}
          className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
        >
          {categories.map((category) => (
            <option key={category.value} value={category.value}>
              {category.label}
            </option>
          ))}
        </select>
      </div>

      {/* 자기소개 */}
      <div>
        <label className="block text-sm font-medium text-var-primary mb-2">
          자기소개 <span className="text-red-500">*</span>
        </label>
        <textarea
          name="introduction"
          value={formData.introduction}
          onChange={(e) => handleFormDataChange({ introduction: e.target.value })}
          placeholder="간단한 자기소개를 작성해주세요"
          rows={3}
          className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent resize-vertical"
          maxLength={200}
        />
        <div className="mt-1 text-xs text-var-muted text-right">
          {formData.introduction.length}/200자
        </div>
      </div>
    </>
  );

  // 내용 뒤 필드: 태그 입력 + 가이드라인
  const afterContentFields = (
    <>
      {/* 태그 입력 */}
      <TagInput
        tags={tags}
        currentTagInput={currentTagInput}
        onTagInputChange={handleTagInput}
        onTagKeyDown={handleTagKeyDown}
        onRemoveTag={removeTag}
        maxTags={5}
        placeholder="태그를 입력하세요"
      />

      {/* 작성 가이드라인 */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h4 className="font-medium text-green-900 mb-2">💡 전문가 꿀정보 작성 가이드라인</h4>
        <ul className="text-sm text-green-800 space-y-1">
          <li>• 검증된 전문 지식을 바탕으로 실용적인 팁을 제공해주세요</li>
          <li>• 단계별로 쉽게 따라할 수 있도록 구체적으로 설명해주세요</li>
          <li>• 안전상 주의사항이 있다면 반드시 명시해주세요</li>
          <li>• 전문가로서의 경험과 노하우를 공유해주세요</li>
          <li>• 관련 태그를 활용해 다른 주민들이 쉽게 찾을 수 있도록 해주세요</li>
        </ul>
      </div>
    </>
  );

  return (
    <PostWriteForm<ExpertTipFormData>
      config={config}
      initialData={formData}
      onDataChange={handleFormDataChange}
      extendedFields={extendedFields}
      afterContentFields={afterContentFields}
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isSubmitting={isSubmitting}
    />
  );
}