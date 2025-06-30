import { useState } from "react";
import { useNavigate } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import type { CreatePostRequest, CategoryType } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "글쓰기 | XAI 아파트 커뮤니티" },
    { name: "description", content: "새로운 게시글을 작성해보세요" },
  ];
};

const categories = [
  { value: "info", label: "입주정보" },
  { value: "life", label: "생활정보" },
  { value: "story", label: "이야기" }
];

// 카테고리 value를 label로 변환하는 함수
const getCategoryLabel = (value: string): CategoryType => {
  const category = categories.find(cat => cat.value === value);
  return (category?.label as CategoryType) || "입주정보";
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
  const [tags, setTags] = useState<string[]>([]);
  const [currentTagInput, setCurrentTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  // 태그 입력 처리
  const handleTagInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    
    // 쉼표가 입력되면 태그 추가
    if (value.includes(',')) {
      const newTag = value.replace(',', '').trim();
      if (newTag && !tags.includes(newTag) && tags.length < 3) {
        setTags(prev => [...prev, newTag]);
      }
      setCurrentTagInput('');
    } else {
      setCurrentTagInput(value);
    }
  };

  // 엔터 키로 태그 추가
  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const newTag = currentTagInput.trim();
      if (newTag && !tags.includes(newTag) && tags.length < 3) {
        setTags(prev => [...prev, newTag]);
        setCurrentTagInput('');
      }
    } else if (e.key === 'Backspace' && currentTagInput === '' && tags.length > 0) {
      // 백스페이스로 마지막 태그 삭제
      setTags(prev => prev.slice(0, -1));
    }
  };

  // 태그 삭제
  const removeTag = (indexToRemove: number) => {
    setTags(prev => prev.filter((_, index) => index !== indexToRemove));
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
          tags: tags.length > 0 ? tags : undefined,
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
    if (formData.title.trim() || formData.content.trim() || tags.length > 0) {
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
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                태그 (선택사항)
              </label>
              
              {/* 태그 컨테이너 */}
              <div className="w-full min-h-[48px] px-4 py-2 bg-var-section border border-var-color rounded-lg focus-within:ring-2 focus-within:ring-accent-primary focus-within:border-transparent">
                <div className="flex flex-wrap gap-2 items-center">
                  {/* 기존 태그들 */}
                  {tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 bg-accent-primary text-white rounded-full text-sm"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => removeTag(index)}
                        className="ml-1 hover:bg-accent-primary/80 rounded-full p-0.5 transition-colors"
                        aria-label={`${tag} 태그 삭제`}
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </span>
                  ))}
                  
                  {/* 태그 입력 필드 */}
                  {tags.length < 3 && (
                    <input
                      type="text"
                      value={currentTagInput}
                      onChange={handleTagInput}
                      onKeyDown={handleTagKeyDown}
                      placeholder={tags.length === 0 ? "태그 입력 후 쉼표(,) 또는 엔터" : ""}
                      className="flex-1 min-w-[120px] bg-transparent border-none outline-none text-var-primary placeholder-var-muted"
                      maxLength={20}
                    />
                  )}
                </div>
              </div>
              
              <div className="mt-1 text-xs text-var-muted">
                {tags.length < 3 ? (
                  <>쉼표(,) 또는 엔터로 태그 추가 • 백스페이스로 태그 삭제 • 최대 3개</>
                ) : (
                  <span className="text-orange-600">⚠️ 최대 3개까지 추가할 수 있습니다</span>
                )}
              </div>
            </div>

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