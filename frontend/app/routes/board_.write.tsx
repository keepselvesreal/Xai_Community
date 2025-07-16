import { useState } from "react";
import { useNavigate } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import { PostWriteForm } from "~/components/common";
import type { PostWriteFormConfig } from "~/components/common";
import TagInput from "~/components/common/TagInput";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { useTagInput } from "~/hooks/useTagInput";
import { apiClient } from "~/lib/api";
import { categories, getCategoryLabel } from "~/utils/categories";
import type { CreatePostRequest } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "글쓰기 | XAI 아파트 커뮤니티" },
    { name: "description", content: "새로운 게시글을 작성해보세요" },
  ];
};

interface BoardFormData {
  title: string;
  content: string;
  category: string;
  tags: string[];
}

const config: PostWriteFormConfig = {
  pageTitle: "글쓰기",
  pageDescription: "아파트 주민들과 정보를 공유하고 소통해보세요.",
  submitButtonText: "게시글 작성",
  successMessage: "게시글이 성공적으로 작성되었습니다!",
  guidelines: [
    "아파트 주민들에게 도움이 되는 정보를 공유해주세요",
    "서로를 배려하는 건전한 내용으로 작성해주세요",
    "개인정보나 민감한 정보는 포함하지 마세요",
    "명확하고 이해하기 쉬운 제목을 작성해주세요",
    "태그를 활용해 다른 주민들이 쉽게 찾을 수 있도록 해주세요",
  ],
  titleMaxLength: 200,
  contentMaxLength: 10000,
};

export default function BoardWrite() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  
  const [formData, setFormData] = useState<BoardFormData>({
    title: "",
    content: "",
    category: "info",
    tags: [],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 태그 입력 관리를 위한 커스텀 훅 사용
  const tagInput = useTagInput({ maxTags: 3 });

  const handleFormDataChange = (data: Partial<BoardFormData>) => {
    setFormData(prev => ({
      ...prev,
      ...data,
    }));
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      category: e.target.value,
    }));
  };

  const handleSubmit = async (data: BoardFormData) => {
    setIsSubmitting(true);
    
    try {
      // 백엔드 API 호출 데이터 구성
      const postData: CreatePostRequest = {
        title: data.title.trim(),
        content: data.content.trim(),
        service: "residential_community",
        metadata: {
          type: "board",
          category: getCategoryLabel(data.category),
          tags: tagInput.tags.length > 0 ? tagInput.tags : undefined,
        }
      };

      const response = await apiClient.createPost(postData);
      
      if (response.success && response.data) {
        showSuccess(config.successMessage);
        navigate("/board");
      } else {
        showError(response.error || "게시글 작성에 실패했습니다.");
      }
    } catch (error) {
      showError("게시글 작성 중 오류가 발생했습니다.");
      console.error("게시글 작성 오류:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (formData.title.trim() || formData.content.trim() || tagInput.tags.length > 0) {
      if (window.confirm("작성 중인 내용이 있습니다. 정말로 취소하시겠습니까?")) {
        navigate("/board");
      }
    } else {
      navigate("/board");
    }
  };

  // 확장 필드 컴포넌트 (카테고리 선택 + 태그 입력)
  const extendedFields = (
    <>
      {/* 카테고리 선택 */}
      <div>
        <label htmlFor="category" className="block text-sm font-medium text-var-primary mb-2">
          카테고리
        </label>
        <select
          id="category"
          name="category"
          value={formData.category}
          onChange={handleCategoryChange}
          className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
        >
          {categories.map((category) => (
            <option key={category.value} value={category.value}>
              {category.label}
            </option>
          ))}
        </select>
      </div>

      {/* 태그 입력 */}
      <TagInput
        tags={tagInput.tags}
        currentTagInput={tagInput.currentTagInput}
        onTagInputChange={tagInput.handleTagInput}
        onTagKeyDown={tagInput.handleTagKeyDown}
        onRemoveTag={tagInput.removeTag}
        maxTags={3}
        placeholder="태그 입력 후 쉼표(,) 또는 엔터"
      />
    </>
  );

  return (
    <PostWriteForm
      config={config}
      initialData={formData}
      onDataChange={handleFormDataChange}
      extendedFields={extendedFields}
      onSubmit={handleSubmit}
      onCancel={handleCancel}
      isSubmitting={isSubmitting}
    />
  );
}