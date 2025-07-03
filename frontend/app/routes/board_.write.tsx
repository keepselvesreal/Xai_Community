import { useState } from "react";
import { useNavigate } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import AppLayout from "~/components/layout/AppLayout";
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

export default function BoardWrite() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showSuccess, showError } = useNotification();
  
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    category: "info"
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 태그 입력 관리를 위한 커스텀 훅 사용
  const tagInput = useTagInput({ maxTags: 3 });

  // 인증되지 않은 사용자 처리 (일시적으로 비활성화)
  // if (!user) {
  //   navigate('/auth/login');
  //   return null;
  // }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 입력 검증
    if (!formData.title.trim()) {
      showError("제목을 입력해주세요.");
      return;
    }
    
    if (!formData.content.trim()) {
      showError("내용을 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    
    try {
      // 백엔드 API 호출 데이터 구성
      const postData: CreatePostRequest = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        service: "residential_community",
        metadata: {
          type: "board",
          category: getCategoryLabel(formData.category),
          tags: tagInput.tags.length > 0 ? tagInput.tags : undefined,
        }
      };

      const response = await apiClient.createPost(postData);
      
      if (response.success && response.data) {
        showSuccess("게시글이 성공적으로 작성되었습니다!");
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

  return (
    <AppLayout 
      user={user || { id: 'test', email: 'test@test.com', name: '테스트사용자' }}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-var-primary mb-2">글쓰기</h1>
          <p className="text-var-secondary">
            아파트 주민들과 정보를 공유하고 소통해보세요.
          </p>
        </div>

        {/* 글쓰기 폼 */}
        <div className="bg-var-card border border-var-color rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 카테고리 선택 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                카테고리
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleInputChange}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
              >
                {categories.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 제목 입력 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                제목 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="제목을 입력하세요"
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent"
                maxLength={200}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.title.length}/200자
              </div>
            </div>

            {/* 내용 입력 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                내용 <span className="text-red-500">*</span>
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                placeholder="내용을 입력하세요"
                rows={12}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent resize-vertical"
                maxLength={10000}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.content.length}/10,000자
              </div>
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

            {/* 작성 가이드라인 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">📝 게시글 작성 가이드라인</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 아파트 주민들에게 도움이 되는 정보를 공유해주세요</li>
                <li>• 서로를 배려하는 건전한 내용으로 작성해주세요</li>
                <li>• 개인정보나 민감한 정보는 포함하지 마세요</li>
                <li>• 명확하고 이해하기 쉬운 제목을 작성해주세요</li>
                <li>• 태그를 활용해 다른 주민들이 쉽게 찾을 수 있도록 해주세요</li>
              </ul>
            </div>

            {/* 버튼 영역 */}
            <div className="flex justify-end gap-3 pt-4 border-t border-var-color">
              <button
                type="button"
                onClick={handleCancel}
                disabled={isSubmitting}
                className="px-6 py-3 border border-var-color rounded-lg text-var-secondary hover:bg-var-hover transition-colors duration-200 disabled:opacity-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !formData.title.trim() || !formData.content.trim()}
                className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    작성 중...
                  </>
                ) : (
                  <>
                    ✏️ 게시글 작성
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