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
  
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    category: "lifestyle",
    introduction: ""
  });
  const [tags, setTags] = useState<string[]>([]);
  const [currentTagInput, setCurrentTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

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
      if (newTag && !tags.includes(newTag) && tags.length < 5) {
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
      if (newTag && !tags.includes(newTag) && tags.length < 5) {
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

    if (!formData.introduction.trim()) {
      showError("자기소개를 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    
    try {
      // JSON 형태로 content 구성 (자기소개 + 내용)
      const contentData = {
        introduction: formData.introduction.trim(),
        content: formData.content.trim()
      };

      // 백엔드 API 호출 데이터 구성
      const postData: CreatePostRequest = {
        title: formData.title.trim(),
        content: JSON.stringify(contentData),
        service: "residential_community",
        metadata: {
          type: "expert_tips",
          category: getCategoryLabel(formData.category),
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

  const handleCancel = () => {
    if (formData.title.trim() || formData.content.trim() || tags.length > 0) {
      if (window.confirm("작성 중인 내용이 있습니다. 정말로 취소하시겠습니까?")) {
        navigate("/tips");
      }
    } else {
      navigate("/tips");
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
          <h1 className="text-2xl font-bold text-var-primary mb-2">전문가 꿀정보 작성</h1>
          <p className="text-var-secondary">
            아파트 주민들에게 도움이 되는 전문적인 생활 팁을 공유해주세요.
          </p>
        </div>

        {/* 글쓰기 폼 */}
        <div className="bg-var-card border border-var-color rounded-xl p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 전문 분야 선택 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                전문 분야 <span className="text-red-500">*</span>
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

            {/* 자기소개 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                자기소개 <span className="text-red-500">*</span>
              </label>
              <textarea
                name="introduction"
                value={formData.introduction}
                onChange={handleInputChange}
                placeholder="예: 10년 경력의 인테리어 전문가입니다. 작은 공간도 넓고 쾌적하게 만드는 것이 제 전문 분야입니다."
                rows={3}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent resize-vertical"
                maxLength={200}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.introduction.length}/200자
              </div>
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
                placeholder="예: 겨울철 실내 화분 관리법"
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
                placeholder="전문적인 팁과 실용적인 정보를 상세히 입력해주세요"
                rows={15}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent resize-vertical"
                maxLength={15000}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.content.length}/15,000자
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
                      className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                    >
                      #{tag}
                      <button
                        type="button"
                        onClick={() => removeTag(index)}
                        className="ml-1 hover:bg-green-200 rounded-full p-0.5 transition-colors"
                        aria-label={`${tag} 태그 삭제`}
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </span>
                  ))}
                  
                  {/* 태그 입력 필드 */}
                  {tags.length < 5 && (
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
                {tags.length < 5 ? (
                  <>쉼표(,) 또는 엔터로 태그 추가 • 백스페이스로 태그 삭제 • 최대 5개</>
                ) : (
                  <span className="text-orange-600">⚠️ 최대 5개까지 추가할 수 있습니다</span>
                )}
              </div>
            </div>

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
                disabled={isSubmitting || !formData.title.trim() || !formData.content.trim() || !formData.introduction.trim()}
                className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    작성 중...
                  </>
                ) : (
                  <>
                    💡 꿀정보 작성
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