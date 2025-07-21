import { useState, useEffect } from "react";
import { type MetaFunction, type LoaderFunction, json } from "@remix-run/node";
import { useParams, useNavigate, useLoaderData } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import DetailPageLayout from "~/components/common/DetailPageLayout";
import ReportModal from "~/components/common/ReportModal";
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
  
  // 신고 모달 상태
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  
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

  // 댓글 상태 변경 감지하여 실시간 통계 업데이트
  useEffect(() => {
    if (!service || !post || !comments) return;
    
    console.log('📊 댓글 상태 변경 감지, 실시간 통계 업데이트 시작:', {
      commentsLength: comments.length,
      hasService: !!service,
      hasPost: !!post
    });
    
    // 서비스 통계 업데이트
    const updatedService = recalculateServiceRating(service, comments);
    if (updatedService && updatedService !== service) {
      setService(updatedService);
      console.log('📊 실시간 서비스 통계 업데이트 완료:', {
        newRating: updatedService.rating,
        reviewCount: updatedService.serviceStats?.review_count
      });
    }
    
    // 포스트 통계 업데이트 (게시글 헤더용)
    const updatedPost = updatePostStats(post, comments);
    if (updatedPost && 
        (updatedPost.stats?.inquiry_count !== post.stats?.inquiry_count ||
         updatedPost.stats?.review_count !== post.stats?.review_count ||
         updatedPost.stats?.comment_count !== post.stats?.comment_count)) {
      setPost(updatedPost);
      console.log('📊 실시간 포스트 통계 업데이트 완료:', {
        totalComments: updatedPost.stats?.comment_count,
        inquiryCount: updatedPost.stats?.inquiry_count,
        reviewCount: updatedPost.stats?.review_count,
        이전_문의수: post.stats?.inquiry_count,
        이전_후기수: post.stats?.review_count
      });
    }
  }, [comments]); // comments 상태 변경 시마다 실행

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
        console.log('🔄 댓글 목록만 업데이트 완료:', {
          totalComments: comments.length,
          inquiryComments: comments.filter(c => c.metadata?.subtype === 'service_inquiry').length,
          reviewComments: comments.filter(c => c.metadata?.subtype === 'service_review').length
        });
      }
    } catch (error) {
      console.error('댓글 새로고침 오류:', error);
    }
  };

  // 서비스 별점 재계산 함수
  const recalculateServiceRating = (currentService: Service | null, comments: Comment[]): Service | null => {
    if (!currentService) return null;
    
    try {
      // 문의 댓글과 후기 댓글 분리
      const inquiryComments = comments.filter(
        comment => comment.metadata?.subtype === 'service_inquiry'
      );
      const reviewComments = comments.filter(
        comment => comment.metadata?.subtype === 'service_review'
      );
      
      let updatedService = { ...currentService };
      
      // 후기가 있으면 별점 계산
      if (reviewComments.length > 0) {
        const ratingsFromComments = reviewComments
          .filter(comment => comment.metadata?.rating)
          .map(comment => Number(comment.metadata.rating));
        
        if (ratingsFromComments.length > 0) {
          const sum = ratingsFromComments.reduce((acc, rating) => acc + rating, 0);
          const averageRating = sum / ratingsFromComments.length;
          const roundedRating = Math.round(averageRating * 10) / 10; // 소수점 1자리까지
          
          updatedService.rating = roundedRating;
        }
      } else {
        // 후기가 없으면 기본 별점 유지 (또는 0으로 설정)
        updatedService.rating = currentService.rating || 0;
      }
      
      // 서비스 통계 업데이트
      updatedService.serviceStats = {
        ...currentService.serviceStats,
        inquiries: inquiryComments.length,
        reviews: reviewComments.length,
        review_count: reviewComments.length,
        average_rating: updatedService.rating
      };
      
      console.log('📊 서비스 별점 재계산 완료:', {
        inquiryCount: inquiryComments.length,
        reviewCount: reviewComments.length,
        averageRating: updatedService.rating,
        previousRating: currentService.rating
      });
      
      return updatedService;
    } catch (error) {
      console.error('서비스 별점 재계산 오류:', error);
      return currentService;
    }
  };

  // Post 객체 통계 업데이트 함수
  const updatePostStats = (currentPost: Post | null, comments: Comment[]): Post | null => {
    if (!currentPost) return null;
    
    try {
      // 문의 댓글과 후기 댓글 분리
      const inquiryComments = comments.filter(
        comment => comment.metadata?.subtype === 'service_inquiry'
      );
      const reviewComments = comments.filter(
        comment => comment.metadata?.subtype === 'service_review'
      );
      
      // Post 객체의 stats 업데이트
      const updatedPost = {
        ...currentPost,
        stats: {
          ...currentPost.stats,
          comment_count: comments.length, // 총 댓글 수
          inquiry_count: inquiryComments.length, // 문의 수
          review_count: reviewComments.length, // 후기 수
          // 기존 필드 유지
          view_count: currentPost.stats?.view_count || 0,
          like_count: currentPost.stats?.like_count || 0,
          dislike_count: currentPost.stats?.dislike_count || 0,
          bookmark_count: currentPost.stats?.bookmark_count || 0
        }
      };
      
      console.log('📊 Post 통계 업데이트 완료:', {
        totalComments: comments.length,
        inquiryCount: inquiryComments.length,
        reviewCount: reviewComments.length,
        이전상태: {
          inquiry_count: currentPost.stats?.inquiry_count,
          review_count: currentPost.stats?.review_count,
          comment_count: currentPost.stats?.comment_count
        }
      });
      
      return updatedPost;
    } catch (error) {
      console.error('Post 통계 업데이트 오류:', error);
      return currentPost;
    }
  };

  // 댓글 추가 후 콜백 (새 댓글 작성 시)
  const handleCommentAdded = async () => {
    console.log('🔄 댓글 추가 후 콜백 시작');
    
    // 1. 댓글 목록을 먼저 새로고침
    await refreshComments();
    
    // 2. 서버에서 통계 정보 새로고침
    await refreshServiceStats();
    
    // 3. 통계 업데이트는 useEffect에서 comments 상태 변경 감지 후 처리
    console.log('📊 댓글 새로고침 완료, useEffect에서 통계 업데이트 예정');
  };

  // 댓글 반응 후 콜백 (추천/비추천 시)
  const handleCommentReaction = async () => {
    // 댓글 반응 시에는 로딩 없이 댓글만 새로고침
    await refreshComments();
    
    // 통계 업데이트는 useEffect에서 comments 상태 변경 감지 후 처리
    console.log('📊 댓글 반응 후 새로고침 완료, useEffect에서 통계 업데이트 예정');
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

  // 신고 제출 핸들러
  const handleReportSubmit = async (content: string) => {
    setReportLoading(true);
    try {
      if (!post) {
        throw new Error('게시글 정보가 없습니다.');
      }
      
      const response = await apiClient.reportPost(post.id, content);
      if (response.success) {
        showSuccess('신고가 접수되었습니다. 검토 후 조치하겠습니다.');
        setIsReportModalOpen(false);
      } else {
        throw new Error(response.error || '신고 접수에 실패했습니다.');
      }
    } catch (error) {
      console.error('신고 실패:', error);
      showError('신고 접수 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setReportLoading(false);
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
    handleCommentReaction, // 댓글 반응 전용 콜백 추가
    () => setIsReportModalOpen(true) // 신고 버튼 핸들러 추가
  );

  return (
    <AppLayout 
      user={user || undefined}
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
          user={user || undefined}
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

      {/* 신고 모달 */}
      {post && (
        <ReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          targetType="post"
          targetId={post.id}
          onSubmit={handleReportSubmit}
          isLoading={reportLoading}
        />
      )}

    </AppLayout>
  );
}