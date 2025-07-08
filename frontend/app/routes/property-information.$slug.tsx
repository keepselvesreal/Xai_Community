import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate, useParams } from "@remix-run/react";
import { useState, useEffect } from "react";
import AppLayout from "~/components/layout/AppLayout";
import SafeHTMLRenderer from "~/components/common/SafeHTMLRenderer";
import CommentSection from "~/components/comment/CommentSection";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import type { InfoItem, ContentType, Comment } from "~/types";
import { convertPostToInfoItem } from "~/types";

interface LoaderData {
  infoItem: InfoItem | null;
  comments: Comment[];
  error?: string;
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  if (!data?.infoItem) {
    return [
      { title: "정보를 찾을 수 없습니다 | XAI 아파트 커뮤니티" },
      { name: "description", content: "요청하신 정보를 찾을 수 없습니다." },
    ];
  }

  const { infoItem } = data;
  return [
    { title: `${infoItem.title} | XAI 아파트 커뮤니티` },
    { name: "description", content: infoItem.metadata.summary || infoItem.title },
    { property: "og:title", content: infoItem.title },
    { property: "og:description", content: infoItem.metadata.summary || infoItem.title },
    { property: "og:type", content: "article" },
  ];
};

// 🚀 Hybrid 방식: 기본 구조만 SSR, 데이터는 클라이언트에서 빠르게 로드
export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    return json<LoaderData>({ 
      infoItem: null, 
      comments: [],
      error: "잘못된 요청입니다." 
    }, { status: 400 });
  }

  // ⚡ 즉시 응답: 데이터 없이 페이지 구조만 전송
  return json<LoaderData>({ 
    infoItem: null, 
    comments: [],
    error: null 
  });
};

function getContentTypeLabel(contentType: ContentType): string {
  const labels = {
    'interactive_chart': '인터렉티브 차트',
    'ai_article': 'AI 생성 글',
    'data_visualization': '데이터 시각화',
    'mixed_content': '혼합 콘텐츠'
  };
  return labels[contentType] || 'AI 생성 글';
}

function getContentTypeBadgeColor(contentType: ContentType): string {
  const colors = {
    'interactive_chart': 'bg-blue-100 text-blue-700 border-blue-200',
    'ai_article': 'bg-green-100 text-green-700 border-green-200',
    'data_visualization': 'bg-purple-100 text-purple-700 border-purple-200',
    'mixed_content': 'bg-orange-100 text-orange-700 border-orange-200'
  };
  return colors[contentType] || 'bg-green-100 text-green-700 border-green-200';
}

function getCategoryLabel(category: string): string {
  const labels = {
    'market_analysis': '시세분석',
    'legal_info': '법률정보',
    'move_in_guide': '입주가이드',
    'investment_trend': '투자동향'
  };
  return labels[category] || category;
}


export default function InfoDetail() {
  const { slug } = useParams();
  const loaderData = useLoaderData<LoaderData>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();
  
  // ⚡ Hybrid: 페이지 구조는 즉시 표시, 데이터는 빠르게 로드
  const [infoItem, setInfoItem] = useState<InfoItem | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);

  // ⚡ 페이지 마운트 후 즉시 데이터 로드 (Hybrid 방식)
  useEffect(() => {
    const loadData = async () => {
      if (!slug) return;
      
      setIsLoading(true);
      try {
        // 🚀 병렬 로딩: 정보와 댓글을 동시에 호출 (배치 조회 적용)
        const [infoResult, commentsResult] = await Promise.all([
          apiClient.getPost(slug),
          apiClient.getCommentsBatch(slug)  // 🚀 2단계: 배치 조회 사용
        ]);
        
        // 정보 처리
        if (infoResult.success && infoResult.data) {
          const post = infoResult.data;
          
          // property_information 타입인지 확인
          if (post.metadata?.type !== 'property_information') {
            setIsNotFound(true);
            showError('해당 정보를 찾을 수 없습니다');
            return;
          }
          
          const convertedInfoItem = convertPostToInfoItem(post);
          setInfoItem(convertedInfoItem);
        } else {
          setIsNotFound(true);
          showError('정보를 찾을 수 없습니다');
        }
        
        // 댓글 처리 (배치 조회된 댓글 + 작성자 정보)
        if (commentsResult.success && commentsResult.data) {
          // 🚀 배치 조회로 이미 작성자 정보가 포함된 댓글 데이터 사용
          let comments = [];
          if (commentsResult.data.data?.comments) {
            comments = commentsResult.data.data.comments;  // 배치 조회 응답 구조
          } else if (commentsResult.data.comments) {
            comments = commentsResult.data.comments;
          } else if (Array.isArray(commentsResult.data)) {
            comments = commentsResult.data;
          }
          
          // 중첩된 댓글의 ID 필드 변환 (배치 조회된 데이터는 이미 작성자 정보 포함)
          const processCommentsRecursive = (comments: any[]): Comment[] => {
            return comments.map(comment => {
              const processedComment = {
                ...comment,
                id: comment.id || comment._id
              };
              
              // 중첩된 답글도 재귀적으로 처리
              if (processedComment.replies && Array.isArray(processedComment.replies)) {
                processedComment.replies = processCommentsRecursive(processedComment.replies);
              }
              
              return processedComment;
            });
          };
          
          const processedComments = processCommentsRecursive(comments);
          setComments(processedComments);
        }
      } catch (error) {
        setIsNotFound(true);
        showError('데이터를 불러오는 중 오류가 발생했습니다');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [slug]);

  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="max-w-4xl mx-auto space-y-8">
          {/* 스켈레톤 UI - 정보 헤더 */}
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-32 mb-6"></div>
            <div className="flex items-center gap-3 mb-4">
              <div className="h-6 bg-gray-200 rounded w-20"></div>
              <div className="h-6 bg-gray-200 rounded w-16"></div>
              <div className="h-6 bg-gray-200 rounded w-10"></div>
            </div>
            <div className="h-10 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-4 bg-gray-200 rounded w-20"></div>
              </div>
              <div className="flex items-center gap-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-4 bg-gray-200 rounded w-8"></div>
                ))}
              </div>
            </div>
            <div className="bg-gray-100 p-4 rounded-lg mb-6">
              <div className="h-4 bg-gray-200 rounded w-16 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-full"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4 mt-1"></div>
            </div>
          </div>
          
          {/* 스켈레톤 UI - 콘텐츠 */}
          <div className="animate-pulse">
            <div className="space-y-3 mb-8">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              <div className="h-4 bg-gray-200 rounded w-4/6"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
          
          {/* 스켈레톤 UI - 액션 버튼들 */}
          <div className="animate-pulse">
            <div className="flex items-center justify-center gap-4 p-6 bg-gray-100 rounded-lg mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-10 bg-gray-200 rounded w-20"></div>
              ))}
            </div>
          </div>
          
          {/* 스켈레톤 UI - 댓글 섹션 */}
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex space-x-3">
                  <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-full"></div>
                    <div className="h-4 bg-gray-200 rounded w-3/4 mt-1"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </AppLayout>
    );
  }

  // 에러 상태 처리
  if (isNotFound || !infoItem) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <div className="text-6xl mb-4">😞</div>
          <h2 className="text-2xl font-bold text-var-primary mb-2">
            정보를 찾을 수 없습니다
          </h2>
          <p className="text-var-secondary mb-6">
            {loaderData.error || "요청하신 정보가 존재하지 않거나 삭제되었을 수 있습니다."}
          </p>
          <button
            onClick={() => navigate('/info')}
            className="px-6 py-3 bg-accent-primary text-white rounded-xl font-medium hover:bg-accent-hover transition-colors"
          >
            정보 목록으로 돌아가기
          </button>
        </div>
      </AppLayout>
    );
  }

  const handleCommentAdded = async () => {
    if (!slug) return;
    
    try {
      // 🚀 2단계: 배치 조회로 댓글과 작성자 정보 함께 로드
      const response = await apiClient.getCommentsBatch(slug);
      if (response.success && response.data) {
        // 배치 조회된 댓글 데이터 처리
        let comments = [];
        if (response.data.data?.comments) {
          comments = response.data.data.comments;  // 배치 조회 응답 구조
        } else if (response.data.comments) {
          comments = response.data.comments;
        } else if (Array.isArray(response.data)) {
          comments = response.data;
        }
        
        // 중첩된 댓글의 ID 필드 변환 (배치 조회된 데이터는 이미 작성자 정보 포함)
        const processCommentsRecursive = (comments: any[]): Comment[] => {
          return comments.map(comment => {
            const processedComment = {
              ...comment,
              id: comment.id || comment._id
            };
            
            if (processedComment.replies && Array.isArray(processedComment.replies)) {
              processedComment.replies = processCommentsRecursive(processedComment.replies);
            }
            
            return processedComment;
          });
        };
        
        const processedComments = processCommentsRecursive(comments);
        setComments(processedComments);
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  const handleReactionChange = async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!infoItem || !infoItem.slug) return;

    try {
      let response;
      
      // API v3 명세서에 따른 개별 엔드포인트 사용
      switch (reactionType) {
        case 'like':
          response = await apiClient.likePost(infoItem.slug);
          break;
        case 'dislike':
          response = await apiClient.dislikePost(infoItem.slug);
          break;
        case 'bookmark':
          response = await apiClient.bookmarkPost(infoItem.slug);
          break;
        default:
          throw new Error('Invalid reaction type');
      }
      
      if (response.success) {
        showSuccess(reactionType === 'like' ? '추천했습니다' : 
                   reactionType === 'dislike' ? '비추천했습니다' : 
                   '북마크에 추가했습니다');
        
        // 페이지 새로고침 대신 상태 업데이트
        if (response.data && infoItem.stats) {
          infoItem.stats.like_count = response.data.like_count ?? infoItem.stats.like_count;
          infoItem.stats.dislike_count = response.data.dislike_count ?? infoItem.stats.dislike_count;
          infoItem.stats.bookmark_count = response.data.bookmark_count ?? infoItem.stats.bookmark_count;
        }
      } else {
        showError(response.error || '반응 처리에 실패했습니다');
      }
    } catch (error) {
      showError('반응 처리 중 오류가 발생했습니다');
    }
  };

  const handleLike = () => {
    handleReactionChange('like');
  };

  const handleDislike = () => {
    handleReactionChange('dislike');
  };

  const handleBookmark = () => {
    handleReactionChange('bookmark');
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: infoItem.title,
        text: infoItem.metadata.summary || infoItem.title,
        url: window.location.href
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      showSuccess('링크가 클립보드에 복사되었습니다.');
    }
  };

  return (
    <AppLayout user={user} onLogout={logout}>
      <div className="max-w-4xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/info')}
            className="flex items-center gap-2 text-var-secondary hover:text-var-primary transition-colors"
          >
            <span>←</span>
            <span>정보 목록으로 돌아가기</span>
          </button>
        </div>

        {/* 헤더 */}
        <header className="mb-8">
          {/* 배지들 */}
          <div className="flex items-center gap-3 mb-4">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getContentTypeBadgeColor(infoItem.content_type)}`}>
              {getContentTypeLabel(infoItem.content_type)}
            </span>
            <span className="bg-blue-100 text-blue-600 px-3 py-1 rounded-full text-sm font-medium">
              {getCategoryLabel(infoItem.metadata.category)}
            </span>
            {new Date().getTime() - new Date(infoItem.created_at).getTime() < 7 * 24 * 60 * 60 * 1000 && (
              <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                NEW
              </span>
            )}
          </div>

          {/* 제목 */}
          <h1 className="text-3xl font-bold text-var-primary mb-4">
            {infoItem.title}
          </h1>

          {/* 메타 정보 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4 text-sm text-var-muted">
              <span>작성일: {new Date(infoItem.created_at).toLocaleDateString('ko-KR')}</span>
              {infoItem.metadata.data_source && (
                <span>출처: {infoItem.metadata.data_source}</span>
              )}
            </div>

            {/* 통계 */}
            <div className="flex items-center gap-4 text-sm text-var-muted">
              <span className="flex items-center gap-1">
                👁️ {infoItem.stats?.view_count || 0}
              </span>
              <span className="flex items-center gap-1">
                👍 {infoItem.stats?.like_count || 0}
              </span>
              <span className="flex items-center gap-1">
                👎 {infoItem.stats?.dislike_count || 0}
              </span>
              <span className="flex items-center gap-1">
                💬 {infoItem.stats?.comment_count || 0}
              </span>
              <span className="flex items-center gap-1">
                🔖 {infoItem.stats?.bookmark_count || 0}
              </span>
            </div>
          </div>

          {/* 요약 */}
          {infoItem.metadata.summary && (
            <div className="bg-var-section p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-var-primary mb-2">📋 요약</h3>
              <p className="text-var-secondary">{infoItem.metadata.summary}</p>
            </div>
          )}
        </header>

        {/* 콘텐츠 */}
        <main className="mb-8">
          <SafeHTMLRenderer
            content={infoItem.content}
            contentType={infoItem.content_type}
            className="prose prose-lg max-w-none"
          />
        </main>

        {/* 태그 */}
        {infoItem.metadata.tags && infoItem.metadata.tags.length > 0 && (
          <section className="mb-8">
            <h3 className="font-semibold text-var-primary mb-3">🏷️ 태그</h3>
            <div className="flex flex-wrap gap-2">
              {infoItem.metadata.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-gray-50 text-gray-700 text-sm rounded-full font-medium hover:bg-gray-100 cursor-pointer"
                  onClick={() => navigate(`/info?search=${encodeURIComponent(tag)}`)}
                >
                  #{tag}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* 액션 버튼들 */}
        <section className="flex items-center justify-center gap-4 p-6 bg-var-section rounded-lg mb-8">
          <button
            onClick={handleLike}
            className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 rounded-lg font-medium transition-colors"
          >
            <span>👍</span>
            <span>추천</span>
            <span className="text-sm">({infoItem.stats?.like_count || 0})</span>
          </button>
          
          <button
            onClick={handleDislike}
            className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 rounded-lg font-medium transition-colors"
          >
            <span>👎</span>
            <span>비추천</span>
            <span className="text-sm">({infoItem.stats?.dislike_count || 0})</span>
          </button>
          
          <button
            onClick={handleBookmark}
            className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 rounded-lg font-medium transition-colors"
          >
            <span>🔖</span>
            <span>북마크</span>
            <span className="text-sm">({infoItem.stats?.bookmark_count || 0})</span>
          </button>
          
          <button
            onClick={handleShare}
            className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 hover:bg-gray-50 border border-gray-200 rounded-lg font-medium transition-colors"
          >
            <span>🔗</span>
            <span>공유</span>
          </button>
        </section>

        {/* 댓글 섹션 */}
        <CommentSection
          postSlug={infoItem.slug!}
          comments={comments}
          onCommentAdded={handleCommentAdded}
        />

        {/* 관련 정보 추천 */}
        <section>
          <h3 className="font-semibold text-var-primary mb-4">🔍 관련 정보</h3>
          <div className="text-center py-8 bg-var-section rounded-lg">
            <p className="text-var-secondary">관련 정보 기능을 준비 중입니다.</p>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}