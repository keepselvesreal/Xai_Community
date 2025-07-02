import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate } from "@remix-run/react";
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

export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    return json<LoaderData>({ 
      infoItem: null, 
      error: "잘못된 요청입니다." 
    }, { status: 400 });
  }

  try {
    // API에서 정보 데이터 조회 (개별 조회 API 사용)
    const response = await apiClient.getPost(slug);

    if (response.success && response.data) {
      const post = response.data;
      
      // property_information 타입인지 확인
      if (post.metadata?.type !== 'property_information') {
        return json<LoaderData>({ 
          infoItem: null, 
          error: "정보를 찾을 수 없습니다." 
        }, { status: 404 });
      }
      
      const infoItem = convertPostToInfoItem(post);
      return json<LoaderData>({ infoItem });
    } else {
      return json<LoaderData>({ 
        infoItem: null, 
        error: "정보를 찾을 수 없습니다." 
      }, { status: 404 });
    }
  } catch (error) {
    console.error('정보 로딩 오류:', error);
    return json<LoaderData>({ 
      infoItem: null, 
      error: "정보를 불러오는 중 오류가 발생했습니다." 
    }, { status: 500 });
  }
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
  const { infoItem, error } = useLoaderData<LoaderData>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  
  // 디버깅용 - comments 상태 변화 추적
  useEffect(() => {
    console.log('Comments 상태 변경됨:', { 
      count: comments?.length || 0, 
      type: typeof comments,
      isArray: Array.isArray(comments),
      comments: comments 
    });
  }, [comments]);

  // 에러 상태 처리
  if (error || !infoItem) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <div className="text-6xl mb-4">😞</div>
          <h2 className="text-2xl font-bold text-var-primary mb-2">
            정보를 찾을 수 없습니다
          </h2>
          <p className="text-var-secondary mb-6">
            {error || "요청하신 정보가 존재하지 않거나 삭제되었을 수 있습니다."}
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

  const loadComments = async () => {
    if (!infoItem?.slug) return;
    
    try {
      console.log('댓글 로딩 시작 - slug:', infoItem.slug);
      const response = await apiClient.getComments(infoItem.slug);
      console.log('API 응답:', response);
      
      if (response.success && response.data) {
        console.log('댓글 데이터:', response.data);
        console.log('댓글 items:', response.data.items);
        console.log('response.data 전체 구조:', JSON.stringify(response.data, null, 2));
        
        // API 응답 구조 확인 후 적절한 경로로 댓글 추출
        let comments = [];
        if (response.data.items) {
          comments = response.data.items;
        } else if (response.data.comments) {
          comments = response.data.comments;
        } else if (Array.isArray(response.data)) {
          comments = response.data;
        }
        
        // 중첩된 댓글의 ID 필드 변환 (게시판 페이지와 동일한 로직)
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
        
        comments = processCommentsRecursive(comments);
        
        console.log('추출된 댓글 배열:', comments);
        console.log('첫 번째 댓글 구조:', comments[0]);
        if (comments[0]) {
          console.log('첫 번째 댓글 ID 필드들:', {
            id: comments[0].id,
            _id: comments[0]._id,
            comment_id: comments[0].comment_id,
            keys: Object.keys(comments[0])
          });
        }
        setComments(comments);
        console.log('setComments 호출 후 - comments 상태 업데이트됨');
      } else {
        console.log('API 응답 실패 또는 데이터 없음:', response);
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  const handleCommentAdded = () => {
    loadComments();
  };

  useEffect(() => {
    loadComments();
  }, [infoItem?.slug]);

  const handleLike = () => {
    // TODO: API 호출로 좋아요 처리
    setIsLiked(!isLiked);
    showSuccess(isLiked ? '좋아요를 취소했습니다.' : '좋아요를 눌렀습니다.');
  };

  const handleBookmark = () => {
    // TODO: API 호출로 북마크 처리
    setIsBookmarked(!isBookmarked);
    showSuccess(isBookmarked ? '북마크를 취소했습니다.' : '북마크에 추가했습니다.');
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
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              isLiked 
                ? 'bg-red-500 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <span>{isLiked ? '❤️' : '🤍'}</span>
            <span>좋아요</span>
          </button>
          
          <button
            onClick={handleBookmark}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              isBookmarked 
                ? 'bg-yellow-500 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <span>{isBookmarked ? '🔖' : '📑'}</span>
            <span>북마크</span>
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
        <div>
          <h3 className="text-lg font-semibold mb-4">디버깅 정보</h3>
          <div className="bg-yellow-50 p-4 rounded-lg mb-4 text-sm">
            <p>댓글 개수: {comments?.length || 0}</p>
            <p>댓글 데이터 존재: {comments && comments.length > 0 ? 'Yes' : 'No'}</p>
            <p>Comments 타입: {typeof comments}</p>
            <p>Comments 배열 여부: {Array.isArray(comments) ? 'Yes' : 'No'}</p>
            <p>infoItem.slug: {infoItem.slug}</p>
            <p>Comments 배열: {comments ? JSON.stringify(comments.map(c => ({ id: c.id, content: c.content.substring(0, 30) }))) : 'undefined'}</p>
          </div>
        </div>
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