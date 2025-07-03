import { useState, useEffect } from "react";
import { useNavigate, useParams } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import AppLayout from "~/components/layout/AppLayout";
import TagInput from "~/components/common/TagInput";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { useTagInput } from "~/hooks/useTagInput";
import { apiClient } from "~/lib/api";
import type { Post, CreatePostRequest } from "~/types";

export const meta: MetaFunction = () => {
  return [
    { title: "전문가 꿀정보 수정 | XAI 아파트 커뮤니티" },
    { name: "description", content: "전문가 꿀정보를 수정해보세요" },
  ];
};

// 전문가 꿀정보 카테고리 옵션
const tipCategories = [
  { value: "cleaning", label: "청소/정리" },
  { value: "interior", label: "인테리어" },
  { value: "lifestyle", label: "생활" },
  { value: "saving", label: "절약" },
  { value: "pets", label: "반려동물" },
  { value: "gardening", label: "원예" }
];

const getCategoryValue = (label: string): string => {
  const category = tipCategories.find(cat => cat.label === label);
  return category ? category.value : "lifestyle";
};

const getCategoryLabel = (value: string): string => {
  const category = tipCategories.find(cat => cat.value === value);
  return category ? category.label : "생활";
};

export default function ExpertTipEdit() {
  const navigate = useNavigate();
  const { slug } = useParams();
  const { user, logout } = useAuth();
  const { showSuccess, showError } = useNotification();
  
  const [post, setPost] = useState<Post | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    introduction: "",
    category: "lifestyle"
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isNotFound, setIsNotFound] = useState(false);

  // 태그 입력 관리를 위한 커스텀 훅 사용
  const tagInput = useTagInput({ maxTags: 3 });

  // 게시글 데이터 로드
  const loadPost = async () => {
    if (!slug) {
      setIsNotFound(true);
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        const postData = response.data;
        
        // expert_tips 타입인지 확인
        if (postData.metadata?.type !== 'expert_tips') {
          setIsNotFound(true);
          showError('해당 전문가 꿀정보를 찾을 수 없습니다');
          return;
        }
        
        setPost(postData);
        
        // JSON content 파싱 시도
        let parsedContent = null;
        let introduction = '전문가';
        let actualContent = postData.content;
        
        try {
          parsedContent = JSON.parse(postData.content);
          if (parsedContent && typeof parsedContent === 'object') {
            introduction = parsedContent.introduction || '전문가';
            actualContent = parsedContent.content || postData.content;
          }
        } catch (error) {
          // JSON 파싱 실패 시 기존 방식으로 fallback
          introduction = postData.metadata?.expert_title || '전문가';
          actualContent = postData.content;
        }
        
        // 폼 데이터 초기화
        setFormData({
          title: postData.title,
          content: actualContent,
          introduction: introduction,
          category: getCategoryValue(postData.metadata?.category || "생활")
        });
        
        // 권한 체크 - 작성자인지 확인
        if (user && postData.author_id !== user.id) {
          showError('게시글을 수정할 권한이 없습니다');
          navigate(`/expert-tips/${slug}`);
          return;
        }
      } else {
        setIsNotFound(true);
        showError('전문가 꿀정보를 찾을 수 없습니다');
      }
    } catch (error) {
      setIsNotFound(true);
      showError('전문가 꿀정보를 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  // 권한 체크 함수
  const isAuthor = () => {
    if (!user || !post) return false;
    return String(user.id) === String(post.author_id);
  };

  useEffect(() => {
    // 로그인 체크
    if (!user) {
      showError('로그인이 필요합니다');
      navigate('/auth/login');
      return;
    }
    
    loadPost();
  }, [slug, user]);

  // 태그 초기화를 위한 별도 useEffect
  useEffect(() => {
    if (post?.metadata?.tags) {
      console.log('🏷️ 전문가 꿀정보 수정 페이지 - 태그 초기화:', post.metadata.tags);
      tagInput.setInitialTags(post.metadata.tags);
    }
  }, [post]);

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

    if (!formData.introduction.trim()) {
      showError("전문가 소개를 입력해주세요.");
      return;
    }

    if (!isAuthor()) {
      showError("게시글을 수정할 권한이 없습니다.");
      return;
    }

    setIsSubmitting(true);
    
    try {
      // JSON 형태로 content 구성 (introduction과 content 분리)
      const contentData = {
        introduction: formData.introduction.trim(),
        content: formData.content.trim()
      };

      // 백엔드 API 호출 데이터 구성
      const postData: Partial<CreatePostRequest> = {
        title: formData.title.trim(),
        content: JSON.stringify(contentData),
        service: "residential_community",
        metadata: {
          type: "expert_tips",
          category: getCategoryLabel(formData.category),
          tags: tagInput.tags.length > 0 ? tagInput.tags : undefined,
          expert_title: formData.introduction.trim()
        }
      };

      const response = await apiClient.updatePost(slug!, postData);
      
      if (response.success && response.data) {
        showSuccess("전문가 꿀정보가 성공적으로 수정되었습니다!");
        // 제목이 변경되면 새로운 slug가 생성되므로 응답에서 받은 slug로 이동
        const newSlug = response.data.slug || slug;
        navigate(`/expert-tips/${newSlug}`);
      } else {
        showError(response.error || "전문가 꿀정보 수정에 실패했습니다.");
      }
    } catch (error) {
      showError("전문가 꿀정보 수정 중 오류가 발생했습니다.");
      console.error("전문가 꿀정보 수정 오류:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (formData.title.trim() !== (post?.title || '') || 
        formData.content.trim() !== (post?.content || '') || 
        formData.introduction.trim() !== '' ||
        tagInput.tags.length > 0) {
      if (window.confirm("수정 중인 내용이 있습니다. 정말로 취소하시겠습니까?")) {
        navigate(`/expert-tips/${slug}`);
      }
    } else {
      navigate(`/expert-tips/${slug}`);
    }
  };

  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
      </AppLayout>
    );
  }

  if (isNotFound || !post) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            전문가 꿀정보를 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 mb-6">
            요청하신 전문가 꿀정보가 존재하지 않거나 수정 권한이 없습니다.
          </p>
          <button
            onClick={() => navigate('/tips')}
            className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            전문가 꿀정보 목록으로 돌아가기
          </button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout user={user} onLogout={logout}>
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-var-primary mb-2">전문가 꿀정보 수정</h1>
          <p className="text-var-secondary">
            전문가 꿀정보 내용을 수정하고 업데이트하세요.
          </p>
        </div>

        {/* 수정 폼 */}
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
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                {tipCategories.map((category) => (
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
                placeholder="전문가 꿀정보 제목을 입력하세요"
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                maxLength={200}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.title.length}/200자
              </div>
            </div>

            {/* 전문가 소개 입력 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                전문가 소개 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="introduction"
                value={formData.introduction}
                onChange={handleInputChange}
                placeholder="예: 20년 경력의 청소 전문가, 인테리어 디자이너 등"
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                maxLength={100}
              />
              <div className="mt-1 text-xs text-var-muted text-right">
                {formData.introduction.length}/100자
              </div>
            </div>

            {/* 내용 입력 */}
            <div>
              <label className="block text-sm font-medium text-var-primary mb-2">
                꿀정보 내용 <span className="text-red-500">*</span>
              </label>
              <textarea
                name="content"
                value={formData.content}
                onChange={handleInputChange}
                placeholder="전문가만이 알고 있는 특별한 노하우나 팁을 공유해주세요"
                rows={12}
                className="w-full px-4 py-3 bg-var-section border border-var-color rounded-lg text-var-primary placeholder-var-muted focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent resize-vertical"
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

            {/* 수정 가이드라인 */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-medium text-green-900 mb-2">💡 전문가 꿀정보 수정 안내</h4>
              <ul className="text-sm text-green-800 space-y-1">
                <li>• 수정된 내용은 즉시 반영됩니다</li>
                <li>• 다른 사용자들이 이미 작성한 댓글은 유지됩니다</li>
                <li>• 전문성이 느껴지는 유용한 정보로 수정해주세요</li>
                <li>• 개인정보나 민감한 정보는 포함하지 마세요</li>
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
                className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    수정 중...
                  </>
                ) : (
                  <>
                    💡 꿀정보 수정
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