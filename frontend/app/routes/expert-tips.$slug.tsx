import { useState, useEffect } from "react";
import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import CommentSection from "~/components/comment/CommentSection";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import type { Post, Tip, Comment } from "~/types";
import { formatNumber } from "~/lib/utils";

export const meta: MetaFunction = ({ data }: { data: any }) => {
  const tip = data?.tip;
  return [
    { title: `${tip?.title || '전문가 꿀정보'} | XAI 아파트 커뮤니티` },
    { name: "description", content: tip?.content?.substring(0, 150) || "전문가 꿀정보 상세 내용" },
  ];
};

export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    throw new Response("Not Found", { status: 404 });
  }
  
  // API에서 특정 팁 데이터 가져오기
  try {
    const response = await apiClient.getPosts({
      service: 'residential_community',
      metadata_type: 'expert_tips',
      slug: slug,
      page: 1,
      size: 1
    });

    if (!response.success || !response.data?.items?.length) {
      throw new Response("Not Found", { status: 404 });
    }

    const post = response.data.items[0];
    
    // Post를 Tip으로 변환
    const convertPostToTip = (post: Post): Tip => {
      // JSON content 파싱 시도
      let parsedContent = null;
      let introduction = '전문가';
      let actualContent = post.content;
      
      try {
        parsedContent = JSON.parse(post.content);
        if (parsedContent && typeof parsedContent === 'object') {
          introduction = parsedContent.introduction || '전문가';
          actualContent = parsedContent.content || post.content;
        }
      } catch (error) {
        // JSON 파싱 실패 시 기존 방식으로 fallback
        introduction = post.metadata?.expert_title || '전문가';
        actualContent = post.content;
      }
      
      return {
        id: parseInt(post.id),
        title: post.title,
        content: actualContent,
        slug: post.slug,
        expert_name: post.author?.display_name || post.metadata?.expert_name || '익명 전문가',
        expert_title: introduction,
        created_at: post.created_at,
        category: post.metadata?.category || '생활',
        tags: post.metadata?.tags || [],
        views_count: post.stats?.view_count || 0,
        likes_count: post.stats?.like_count || 0,
        saves_count: post.stats?.bookmark_count || 0,
        is_new: new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000
      };
    };

    const tip = convertPostToTip(post);
    return json({ tip });
  } catch (error) {
    console.error('Error fetching tip:', error);
    throw new Response("Not Found", { status: 404 });
  }
};


export default function ExpertTipDetail() {
  const { tip } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [likeCount, setLikeCount] = useState(tip.likes_count);
  const [bookmarkCount, setBookmarkCount] = useState(tip.saves_count);
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

  const formatDateSimple = (dateString: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  const handleLike = async () => {
    try {
      // TODO: API 호출로 좋아요 처리
      setIsLiked(!isLiked);
      setLikeCount(prev => isLiked ? prev - 1 : prev + 1);
    } catch (error) {
      console.error('좋아요 처리 오류:', error);
    }
  };

  const handleBookmark = async () => {
    try {
      // TODO: API 호출로 북마크 처리
      setIsBookmarked(!isBookmarked);
      setBookmarkCount(prev => isBookmarked ? prev - 1 : prev + 1);
    } catch (error) {
      console.error('북마크 처리 오류:', error);
    }
  };

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: tip.title,
          text: tip.content.substring(0, 100) + '...',
          url: window.location.href,
        });
      } else {
        await navigator.clipboard.writeText(window.location.href);
        alert('링크가 복사되었습니다.');
      }
    } catch (error) {
      console.error('공유 오류:', error);
    }
  };

  // 콘텐츠를 문단으로 분할
  const contentParagraphs = tip.content.split('\n').filter(p => p.trim());

  const loadComments = async () => {
    if (!tip.slug) return;
    
    try {
      console.log('댓글 로딩 시작 - slug:', tip.slug);
      const response = await apiClient.getComments(tip.slug);
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
  }, [tip.slug]);

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      {/* 뒤로가기 버튼 */}
      <div className="mb-6">
        <Link 
          to="/tips"
          className="inline-flex items-center gap-2 text-var-secondary hover:text-var-primary transition-colors"
        >
          <span>←</span>
          <span>목록으로</span>
        </Link>
      </div>

      {/* 글 헤더 */}
      <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-8 mb-8 text-white">
        <div className="mb-4">
          <span className="bg-white/20 text-white px-3 py-1 rounded-full text-sm font-medium">
            {tip.category}
          </span>
          {tip.is_new && (
            <span className="ml-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs font-medium">
              NEW
            </span>
          )}
        </div>
        <h1 className="text-3xl font-bold mb-4">{tip.title}</h1>
        <div className="flex items-center justify-between">
          <div className="text-white/90">
            <p className="font-medium">{tip.expert_title}</p>
            <p className="text-sm opacity-75">{formatDateSimple(tip.created_at)}</p>
          </div>
          <div className="flex items-center gap-6 text-white/90">
            <button
              onClick={handleLike}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className={`text-lg ${isLiked ? '❤️' : '🤍'}`}>
                {isLiked ? '❤️' : '🤍'}
              </span>
              <span className="text-sm">추천 {formatNumber(likeCount)}</span>
            </button>
            <button
              onClick={handleBookmark}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className={`text-lg ${isBookmarked ? '🔖' : '📝'}`}>
                {isBookmarked ? '🔖' : '📝'}
              </span>
              <span className="text-sm">저장 {formatNumber(bookmarkCount)}</span>
            </button>
            <button
              onClick={handleShare}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className="text-lg">📤</span>
              <span className="text-sm">공유</span>
            </button>
          </div>
        </div>
      </div>

      {/* 글 내용 */}
      <div className="bg-var-card border border-var-color rounded-2xl p-8 mb-8">
        {/* 통계 정보 */}
        <div className="flex items-center justify-center gap-12 mb-8 py-6 border-b border-var-light">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">{formatNumber(tip.views_count)}</div>
            <div className="text-sm text-var-muted">조회수</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">{formatNumber(likeCount)}</div>
            <div className="text-sm text-var-muted">추천</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-1">{formatNumber(bookmarkCount)}</div>
            <div className="text-sm text-var-muted">저장</div>
          </div>
        </div>

        {/* 글 내용 */}
        <div className="prose max-w-none">
          {contentParagraphs.map((paragraph, index) => (
            <p key={index} className="text-var-secondary leading-relaxed mb-4">
              {paragraph}
            </p>
          ))}
        </div>

        {/* 태그 */}
        {tip.tags && tip.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-8 pt-6 border-t border-var-light">
            {tip.tags.map((tag: string, index: number) => (
              <span 
                key={index}
                className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm"
              >
                {tag.startsWith('#') ? tag : `#${tag}`}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 댓글 섹션 */}
      <div>
        <h3 className="text-lg font-semibold mb-4">디버깅 정보</h3>
        <div className="bg-yellow-50 p-4 rounded-lg mb-4 text-sm">
          <p>댓글 개수: {comments?.length || 0}</p>
          <p>댓글 데이터 존재: {comments && comments.length > 0 ? 'Yes' : 'No'}</p>
          <p>Comments 타입: {typeof comments}</p>
          <p>Comments 배열 여부: {Array.isArray(comments) ? 'Yes' : 'No'}</p>
          <p>tip.slug: {tip.slug}</p>
          <p>Comments 배열: {comments ? JSON.stringify(comments.map(c => ({ id: c.id, content: c.content.substring(0, 30) }))) : 'undefined'}</p>
        </div>
      </div>
      <CommentSection
        postSlug={tip.slug!}
        comments={comments}
        onCommentAdded={handleCommentAdded}
      />

      {/* 관련 글 (향후 구현) */}
      <div className="bg-var-card border border-var-color rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-var-primary mb-4 flex items-center gap-2">
          <span>📚</span>
          관련 꿀정보 추천
        </h3>
        <div className="text-center py-8 text-var-muted">
          <p>관련 꿀정보를 준비 중입니다.</p>
          <Link 
            to="/tips"
            className="inline-block mt-4 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            다른 꿀정보 보기
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}