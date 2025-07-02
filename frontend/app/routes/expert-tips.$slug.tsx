import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from '@remix-run/react';
import AppLayout from '~/components/layout/AppLayout';
import CommentSection from '~/components/comment/CommentSection';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';
import type { Post, Tip, Comment } from '~/types';
import { formatNumber } from "~/lib/utils";

export default function ExpertTipDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError } = useNotification();
  const [tip, setTip] = useState<Tip | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [bookmarkCount, setBookmarkCount] = useState(0);

  // Post를 Tip으로 변환하는 함수
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
      slug: post.slug || post.id, // slug가 없으면 id를 사용
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

  const loadTip = async () => {
    if (!slug) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        // expert_tips 타입인지 확인
        if (response.data.metadata?.type !== 'expert_tips') {
          setIsNotFound(true);
          showError('해당 전문가 꿀정보를 찾을 수 없습니다');
          return;
        }
        
        const convertedTip = convertPostToTip(response.data);
        setTip(convertedTip);
        setLikeCount(convertedTip.likes_count);
        setBookmarkCount(convertedTip.saves_count);
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

  const loadComments = async () => {
    if (!slug) return;
    
    try {
      const response = await apiClient.getComments(slug);
      if (response.success && response.data) {
        console.log('원본 댓글 데이터:', response.data.comments);
        
        // 재귀적으로 모든 중첩된 답글의 id 필드 보장
        const processCommentsRecursive = (comments: any[]): any[] => {
          return comments.map(comment => ({
            ...comment,
            id: comment.id || comment._id, // id가 없으면 _id 사용
            replies: comment.replies ? processCommentsRecursive(comment.replies) : []
          }));
        };
        
        const processedComments = processCommentsRecursive(response.data.comments || []);
        
        console.log('처리된 댓글 데이터:', processedComments);
        setComments(processedComments);
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  const formatDateSimple = (dateString: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  const handleCommentAdded = () => {
    loadComments();
  };

  useEffect(() => {
    loadTip();
    loadComments();
  }, [slug]);

  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </AppLayout>
    );
  }

  if (isNotFound || !tip) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            전문가 꿀정보를 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 mb-6">
            요청하신 전문가 꿀정보가 존재하지 않거나 삭제되었습니다.
          </p>
          <Link 
            to="/tips"
            className="inline-block px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            전문가 꿀정보 목록으로 돌아가기
          </Link>
        </div>
      </AppLayout>
    );
  }

  // 콘텐츠를 문단으로 분할
  const contentParagraphs = tip.content.split('\n').filter(p => p.trim());

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
      <CommentSection
        postSlug={slug!}
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