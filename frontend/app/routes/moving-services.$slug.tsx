import { useState, useEffect } from "react";
import { type MetaFunction, type LoaderFunction, json } from "@remix-run/node";
import { useParams, useNavigate, useLoaderData } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import DetailPageLayout from "~/components/common/DetailPageLayout";
import { 
  createServiceDetailSections 
} from "~/components/service/ServiceDetailSections";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import { getAnalytics } from "~/hooks/useAnalytics";
import { convertPostToService } from "~/types/service-types";
import type { Service } from "~/types/service-types";
import type { Comment, Post } from "~/types";

interface LoaderData {
  service: Service | null;
  comments: Comment[];
  error?: string;
}

// 🚀 Hybrid 방식: 기본 구조만 SSR, 데이터는 클라이언트에서 빠르게 로드
export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    return json<LoaderData>({ 
      service: null, 
      comments: [],
      error: "잘못된 요청입니다." 
    }, { status: 400 });
  }

  // ⚡ 즉시 응답: 데이터 없이 페이지 구조만 전송
  return json<LoaderData>({ 
    service: null, 
    comments: [],
    error: null 
  });
};

export const meta: MetaFunction = () => {
  return [
    { title: "서비스 상세 | XAI 아파트 커뮤니티" },
    { name: "description", content: "서비스 상세 정보" },
  ];
};

export default function ServiceDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const loaderData = useLoaderData<LoaderData>();
  
  // 상태 관리
  const [service, setService] = useState<Service | null>(null);
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [pendingReactions, setPendingReactions] = useState<Set<string>>(new Set());
  const [userReactions, setUserReactions] = useState<{
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  }>({ liked: false, disliked: false, bookmarked: false });
  
  // 🔄 서버에서 최신 통계 데이터 재로드 함수
  const refreshServiceStats = async (): Promise<void> => {
    if (!slug) return;
    
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        const updatedService = convertPostToService(response.data);
        if (updatedService) {
          setService(updatedService);
          console.log('🔄 Service stats refreshed from server:', updatedService.serviceStats);
        }
      }
    } catch (error) {
      console.warn('⚠️ Failed to refresh service stats:', error);
    }
  };

  // 데이터 로딩 함수
  const loadData = async () => {
    if (!slug) return;
    
    setIsLoading(true);
    try {
      // 🚀 병렬 로딩: 서비스와 댓글을 동시에 호출
      const [serviceResult, commentsResult] = await Promise.all([
        apiClient.getPost(slug),
        apiClient.getCommentsBatch(slug)
      ]);
      
      // 서비스 처리
      if (serviceResult.success && serviceResult.data) {
        const serviceData = convertPostToService(serviceResult.data);
        if (serviceData) {
          setService(serviceData);
          setPost(serviceResult.data);
          
          // 사용자 반응 상태 초기화 (로그인 사용자만)
          if (user && serviceResult.data.user_reaction) {
            setUserReactions({
              liked: serviceResult.data.user_reaction.liked || false,
              disliked: serviceResult.data.user_reaction.disliked || false,
              bookmarked: serviceResult.data.user_reaction.bookmarked || false
            });
          }
          
        } else {
          setIsNotFound(true);
          showError('서비스 데이터 변환에 실패했습니다');
        }
      } else {
        setIsNotFound(true);
        showError('서비스를 찾을 수 없습니다');
      }
      
      // 댓글 처리
      if (commentsResult.success && commentsResult.data) {
        let comments = [];
        if (commentsResult.data.data?.comments) {
          comments = commentsResult.data.data.comments;
        } else if (commentsResult.data.comments) {
          comments = commentsResult.data.comments;
        } else if (Array.isArray(commentsResult.data)) {
          comments = commentsResult.data;
        }
        
        setComments(comments);
      }
    } catch (error) {
      setIsNotFound(true);
      showError('데이터를 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  // 페이지 마운트 시 데이터 로드
  useEffect(() => {
    loadData();
  }, [slug]);

  // 반응 처리 함수 (북마크만 활성화)
  const handleReactionChange = async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    console.log('🔖 입주 서비스 반응 처리 시작:', {
      reactionType,
      user: !!user,
      postSlug: slug,
      currentBookmarked: userReactions.bookmarked
    });
    
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!post || !slug) return;

    // 북마크만 처리
    if (reactionType !== 'bookmark') {
      console.log('⚠️ 입주 서비스에서는 북마크만 지원됩니다');
      return;
    }

    // 중복 클릭 방지
    if (pendingReactions.has(reactionType)) {
      return;
    }

    setPendingReactions(prev => new Set([...prev, reactionType]));

    // 현재 상태 백업 (실패 시 복원용)
    const originalPost = post;
    const originalUserReactions = userReactions;

    // 🚀 1단계: 즉시 UI 업데이트 (Optimistic)
    let newUserReactions = { ...userReactions };
    
    setPost(prev => {
      if (!prev?.stats) return prev;
      
      const currentStats = prev.stats;
      let newStats = { ...currentStats };

      if (userReactions.bookmarked) {
        // 이미 북마크한 상태에서 다시 클릭 = 취소
        newStats.bookmark_count = Math.max(0, (currentStats.bookmark_count || 0) - 1);
        newUserReactions.bookmarked = false;
      } else {
        // 북마크 안 한 상태에서 클릭 = 북마크
        newStats.bookmark_count = (currentStats.bookmark_count || 0) + 1;
        newUserReactions.bookmarked = true;
      }

      console.log('🔄 Optimistic UI 업데이트:', {
        이전북마크수: currentStats.bookmark_count,
        새북마크수: newStats.bookmark_count,
        북마크상태: newUserReactions.bookmarked
      });

      return {
        ...prev,
        stats: newStats
      };
    });
    
    // 사용자 반응 상태 업데이트
    setUserReactions(newUserReactions);

    // 🚀 2단계: 백그라운드에서 API 호출
    try {
      const response = await apiClient.bookmarkPost(slug);
      
      if (response.success && response.data) {
        console.log('✅ 북마크 API 성공:', response.data);
        
        // 서버 응답으로 정확한 상태 동기화
        setPost(prev => prev ? {
          ...prev,
          stats: {
            ...prev.stats,
            bookmark_count: response.data.bookmark_count ?? prev.stats?.bookmark_count ?? 0,
            view_count: prev.stats?.view_count ?? 0,
            comment_count: prev.stats?.comment_count ?? 0,
            like_count: prev.stats?.like_count ?? 0,
            dislike_count: prev.stats?.dislike_count ?? 0,
          }
        } : prev);
        
        // 서버에서 사용자 반응 상태 동기화
        if (response.data.user_reaction) {
          setUserReactions({
            liked: response.data.user_reaction.liked || false,
            disliked: response.data.user_reaction.disliked || false,
            bookmarked: response.data.user_reaction.bookmarked || false
          });
        }
      } else {
        console.log('❌ 북마크 API 실패:', response);
        // API 실패 시 원래 상태로 복원
        setPost(originalPost);
        setUserReactions(originalUserReactions);
        showError(response.error || '북마크 처리에 실패했습니다');
      }
    } catch (error) {
      console.error('❌ 북마크 처리 중 오류:', error);
      // 오류 발생 시 원래 상태로 복원
      setPost(originalPost);
      setUserReactions(originalUserReactions);
      showError('북마크 처리 중 오류가 발생했습니다');
    } finally {
      // 요청 완료 처리
      setPendingReactions(prev => {
        const next = new Set(prev);
        next.delete(reactionType);
        return next;
      });
    }
  };

  // 댓글 목록 새로고침 유틸리티 함수
  const refreshComments = async () => {
    if (!slug) return;
    
    try {
      // 댓글 목록만 새로고침 (로딩 상태 변경 없음)
      const response = await apiClient.getCommentsBatch(slug);
      
      if (response.success && response.data) {
        let comments = [];
        if (response.data.data?.comments) {
          comments = response.data.data.comments;
        } else if (response.data.comments) {
          comments = response.data.comments;
        } else if (Array.isArray(response.data)) {
          comments = response.data;
        }
        
        setComments(comments);
        console.log('🔄 댓글 목록만 업데이트 완료:', comments.length);
      }
    } catch (error) {
      console.error('댓글 새로고침 오류:', error);
    }
  };

  // 댓글 추가 후 콜백 (새 댓글 작성 시)
  const handleCommentAdded = async () => {
    await refreshComments();
    await refreshServiceStats(); // 통계 업데이트
  };

  // 댓글 반응 후 콜백 (추천/비추천 시)
  const handleCommentReaction = async () => {
    // 댓글 반응 시에는 로딩 없이 댓글만 새로고침
    await refreshComments();
  };

  // 수정 버튼 핸들러
  const handleEditPost = () => {
    if (!service) return;
    navigate(`/services/write?edit=${service.slug || service.postId}`);
  };

  // 삭제 버튼 핸들러
  const handleDeletePost = async () => {
    if (!service) return;
    
    const confirmDelete = window.confirm(
      `정말로 "${service.name}" 업체 정보를 삭제하시겠습니까?\n\n삭제된 정보는 복구할 수 없습니다.`
    );
    
    if (!confirmDelete) return;
    
    try {
      const response = await apiClient.deletePost(service.slug || service.postId || '');
      
      if (response.success) {
        showSuccess('업체 정보가 삭제되었습니다.');
        navigate('/services');
      } else {
        showError('업체 정보 삭제에 실패했습니다.');
      }
    } catch (error) {
      showError('업체 정보 삭제 중 오류가 발생했습니다.');
    }
  };

  // 전화 문의 핸들러
  const handleInquiry = () => {
    if (service?.contact.phone) {
      window.open(`tel:${service.contact.phone}`);
    }
  };

  // 로딩 상태 처리
  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <DetailPageLayout
          post={null as any}
          user={user}
          comments={[]}
          onReactionChange={() => {}}
          onCommentAdded={() => {}}
          isLoading={true}
        />
      </AppLayout>
    );
  }

  // 404 상태 처리
  if (isNotFound || !service || !post) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center h-64">
          <div className="text-center">
            <div className="text-6xl mb-4">❌</div>
            <h3 className="text-xl font-semibold text-red-600 mb-2">서비스를 찾을 수 없습니다</h3>
            <p className="text-gray-600 mb-4">요청하신 서비스가 존재하지 않거나 삭제되었을 수 있습니다.</p>
            <button
              onClick={() => navigate('/services')}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              서비스 목록으로 돌아가기
            </button>
          </div>
        </div>
      </AppLayout>
    );
  }

  // 서비스 전용 섹션 생성 (문의/후기 섹션 포함)
  const serviceDetailSections = createServiceDetailSections(
    service,
    false, // 북마크 기능 비활성화
    () => {}, // 북마크 핸들러 비활성화
    handleInquiry,
    slug,
    comments,
    handleCommentAdded,
    handleCommentReaction // 댓글 반응 전용 콜백 추가
  );

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="flex items-center justify-between mb-6">
          <button 
            onClick={() => navigate('/services')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 목록으로
          </button>
        </div>

        {/* DetailPageLayout 사용 - 일반 댓글 섹션 제외 */}
        <DetailPageLayout
          post={post}
          user={user}
          comments={[]} // 빈 배열로 전달하여 일반 댓글 섹션 숨김
          onReactionChange={handleReactionChange}
          onCommentAdded={handleCommentAdded}
          onEditPost={handleEditPost}
          onDeletePost={handleDeletePost}
          pendingReactions={pendingReactions}
          userReactions={userReactions}
          sections={serviceDetailSections}
          // postSlug 제거하여 일반 댓글 섹션 비활성화
          pageType="moving_services"
        />
      </div>

      {/* 커스텀 문의/후기 섹션 - 별도로 렌더링 */}
      {serviceDetailSections.customSections?.map((section, index) => (
        <div key={`custom-section-${index}`} className="mt-6">
          {section}
        </div>
      ))}

    </AppLayout>
  );
}