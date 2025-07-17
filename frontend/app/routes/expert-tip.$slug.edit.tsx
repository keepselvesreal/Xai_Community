import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "@remix-run/react";
import { type MetaFunction } from "@remix-run/node";
import AppLayout from "~/components/layout/AppLayout";
import PostWriteForm from "~/components/common/PostWriteForm";
import TagInput from "~/components/common/TagInput";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { useTagInput } from "~/hooks/useTagInput";
import { apiClient } from "~/lib/api";
import type { Post, CreatePostRequest, ExpertTipFormData, PostWriteFormConfig } from "~/types";

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
  { value: "pets", label: "반려동물" }
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
  const [formData, setFormData] = useState<ExpertTipFormData>({
    title: "",
    content: "",
    introduction: "",
    category: "lifestyle",
    tags: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isNotFound, setIsNotFound] = useState(false);

  // 태그 입력 관리를 위한 커스텀 훅 사용 (전문가 꿀정보는 최대 5개)
  const {
    tags,
    currentTagInput,
    handleTagInput,
    handleTagKeyDown,
    removeTag,
    setInitialTags,
    canAddMore,
    isAtLimit
  } = useTagInput({ maxTags: 5 });

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
        const initialFormData = {
          title: postData.title,
          content: actualContent,
          introduction: introduction,
          category: getCategoryValue(postData.metadata?.category || "생활"),
          tags: postData.metadata?.tags || []
        };
        
        setFormData(initialFormData);
        
        // 태그 초기화
        if (postData.metadata?.tags) {
          setInitialTags(postData.metadata.tags);
        }
        
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

    if (!isAuthor()) {
      showError("게시글을 수정할 권한이 없습니다.");
      return;
    }

    setIsSubmitting(true);
    
    try {
      // JSON 형태로 content 구성 (introduction과 content 분리)
      const contentData = {
        introduction: data.introduction.trim(),
        content: data.content.trim()
      };

      // 백엔드 API 호출 데이터 구성
      const postData: Partial<CreatePostRequest> = {
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

  const handleCancel = useCallback(() => {
    navigate(`/expert-tips/${slug}`);
  }, [navigate, slug]);

  // PostWriteForm 설정
  const config: PostWriteFormConfig = {
    pageTitle: "전문가 꿀정보 수정",
    pageDescription: "전문가 꿀정보 내용을 수정하고 업데이트하세요",
    submitButtonText: "💡 꿀정보 수정",
    successMessage: "전문가 꿀정보가 성공적으로 수정되었습니다!",
    guidelines: [
      "수정된 내용은 즉시 반영됩니다",
      "다른 사용자들이 이미 작성한 댓글은 유지됩니다",
      "전문성이 느껴지는 유용한 정보로 수정해주세요",
      "개인정보나 민감한 정보는 포함하지 마세요"
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
          {tipCategories.map((category) => (
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
    </>
  );

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
      <PostWriteForm<ExpertTipFormData>
        config={config}
        initialData={formData}
        onDataChange={handleFormDataChange}
        extendedFields={extendedFields}
        afterContentFields={afterContentFields}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        isSubmitting={isSubmitting}
        isEditMode={true}
      />
    </AppLayout>
  );
}