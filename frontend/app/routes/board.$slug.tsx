import { useEffect, useState, useCallback, useMemo, memo } from 'react';
import { useParams, useNavigate, useLoaderData } from '@remix-run/react';
import { json, type LoaderFunction } from '@remix-run/node';
import AppLayout from '~/components/layout/AppLayout';
import Card from '~/components/ui/Card';
import Button from '~/components/ui/Button';
import CommentSection from '~/components/comment/CommentSection';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';
import type { Post, Comment, PaginatedResponse } from '~/types';
import { performanceMeasurer } from '~/utils/performance-measure';

interface LoaderData {
  post: Post | null;
  comments: Comment[];
  error?: string;
}

// 🚀 Hybrid 방식: 기본 구조만 SSR, 데이터는 클라이언트에서 빠르게 로드
export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    return json<LoaderData>({ 
      post: null, 
      comments: [],
      error: "잘못된 요청입니다." 
    }, { status: 400 });
  }

  // ⚡ 즉시 응답: 데이터 없이 페이지 구조만 전송
  return json<LoaderData>({ 
    post: null, 
    comments: [],
    error: null 
  });
};

interface ReactionButtonsProps {
  post: Post;
  onReactionChange: (reactionType: 'like' | 'dislike' | 'bookmark') => void;
  pendingReactions?: Set<string>;
}

// 🚀 React.memo로 성능 최적화: post.stats가 변경되지 않으면 리렌더링 방지
const ReactionButtons = memo(({ post, onReactionChange, pendingReactions = new Set() }: ReactionButtonsProps) => {
  // 매번 새로운 함수 생성 방지
  const handleLike = useCallback(() => onReactionChange('like'), [onReactionChange]);
  const handleDislike = useCallback(() => onReactionChange('dislike'), [onReactionChange]);
  const handleBookmark = useCallback(() => onReactionChange('bookmark'), [onReactionChange]);

  return (
    <div className="flex items-center space-x-2">
      <Button
        variant="outline"
        size="sm"
        onClick={handleLike}
        disabled={pendingReactions.has('like')}
        className="flex items-center space-x-1"
      >
        <span>👍</span>
        <span>{post.stats?.like_count || post.stats?.likes || 0}</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleDislike}
        disabled={pendingReactions.has('dislike')}
        className="flex items-center space-x-1"
      >
        <span>👎</span>
        <span>{post.stats?.dislike_count || post.stats?.dislikes || 0}</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleBookmark}
        disabled={pendingReactions.has('bookmark')}
        className="flex items-center space-x-1"
      >
        <span>🔖</span>
        <span>{post.stats?.bookmark_count || post.stats?.bookmarks || 0}</span>
      </Button>
    </div>
  );
}, (prevProps, nextProps) => {
  // 사용자 정의 비교 함수: 필요한 경우에만 리렌더링
  const statsChanged = 
    prevProps.post.stats?.like_count !== nextProps.post.stats?.like_count ||
    prevProps.post.stats?.dislike_count !== nextProps.post.stats?.dislike_count ||
    prevProps.post.stats?.bookmark_count !== nextProps.post.stats?.bookmark_count;
  
  const pendingChanged = 
    prevProps.pendingReactions?.size !== nextProps.pendingReactions?.size ||
    [...(prevProps.pendingReactions || [])].some(r => !nextProps.pendingReactions?.has(r));

  return !statsChanged && !pendingChanged;
});


export default function PostDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const loaderData = useLoaderData<LoaderData>();
  
  // ⚡ Hybrid: 페이지 구조는 즉시 표시, 데이터는 빠르게 로드
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true); // 클라이언트에서 데이터 로딩
  const [isNotFound, setIsNotFound] = useState(false);
  const [pendingReactions, setPendingReactions] = useState<Set<string>>(new Set());
  const [userReactions, setUserReactions] = useState<{
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  }>({ liked: false, disliked: false, bookmarked: false });

  // 🗑️ 기존 개별 로딩 함수들 제거 - 병렬 로딩으로 통합됨

  // 🚀 Optimistic UI: 즉시 UI 업데이트, API는 백그라운드 처리
  const handleReactionChange = useCallback(async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    const performanceId = `reaction_${reactionType}_${Date.now()}`;
    performanceMeasurer.start(performanceId, { reactionType, postSlug: slug });
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!post || !slug) return;

    // 중복 클릭 방지
    if (pendingReactions.has(reactionType)) {
      return;
    }

    setPendingReactions(prev => new Set([...prev, reactionType]));

    // 현재 상태 백업 (실패 시 복원용)
    const originalPost = post;

    // 🚀 1단계: 즉시 UI 업데이트 (Optimistic) - 토글 로직 적용
    let newUserReactions = { ...userReactions };
    
    setPost(prev => {
      if (!prev?.stats) return prev;
      
      const currentStats = prev.stats;
      let newStats = { ...currentStats };

      if (reactionType === 'like') {
        if (userReactions.liked) {
          // 이미 추천한 상태에서 다시 클릭 = 취소
          newStats.like_count = Math.max(0, (currentStats.like_count || 0) - 1);
          newUserReactions.liked = false;
        } else {
          // 추천 안 한 상태에서 클릭 = 추천
          newStats.like_count = (currentStats.like_count || 0) + 1;
          newUserReactions.liked = true;
          // 비추천이 있었다면 취소
          if (userReactions.disliked) {
            newStats.dislike_count = Math.max(0, (currentStats.dislike_count || 0) - 1);
            newUserReactions.disliked = false;
          }
        }
      } else if (reactionType === 'dislike') {
        if (userReactions.disliked) {
          // 이미 비추천한 상태에서 다시 클릭 = 취소
          newStats.dislike_count = Math.max(0, (currentStats.dislike_count || 0) - 1);
          newUserReactions.disliked = false;
        } else {
          // 비추천 안 한 상태에서 클릭 = 비추천
          newStats.dislike_count = (currentStats.dislike_count || 0) + 1;
          newUserReactions.disliked = true;
          // 추천이 있었다면 취소
          if (userReactions.liked) {
            newStats.like_count = Math.max(0, (currentStats.like_count || 0) - 1);
            newUserReactions.liked = false;
          }
        }
      } else if (reactionType === 'bookmark') {
        if (userReactions.bookmarked) {
          // 이미 북마크한 상태에서 다시 클릭 = 취소
          newStats.bookmark_count = Math.max(0, (currentStats.bookmark_count || 0) - 1);
          newUserReactions.bookmarked = false;
        } else {
          // 북마크 안 한 상태에서 클릭 = 북마크
          newStats.bookmark_count = (currentStats.bookmark_count || 0) + 1;
          newUserReactions.bookmarked = true;
        }
      }

      return {
        ...prev,
        stats: newStats
      };
    });
    
    // 사용자 반응 상태 업데이트
    setUserReactions(newUserReactions);

    // 🚀 2단계: 백그라운드에서 API 호출
    try {
      let response;
      
      switch (reactionType) {
        case 'like':
          response = await apiClient.likePost(slug);
          break;
        case 'dislike':
          response = await apiClient.dislikePost(slug);
          break;
        case 'bookmark':
          response = await apiClient.bookmarkPost(slug);
          break;
        default:
          throw new Error('Invalid reaction type');
      }
      
      if (response.success && response.data) {
        // 서버 응답으로 정확한 상태 동기화
        setPost(prev => prev ? {
          ...prev,
          stats: {
            ...prev.stats,
            like_count: response.data.like_count ?? prev.stats?.like_count ?? 0,
            dislike_count: response.data.dislike_count ?? prev.stats?.dislike_count ?? 0,
            bookmark_count: response.data.bookmark_count ?? prev.stats?.bookmark_count ?? 0,
            view_count: prev.stats?.view_count ?? 0,
            comment_count: prev.stats?.comment_count ?? 0,
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
        // API 실패 시 원래 상태로 복원
        setPost(originalPost);
        setUserReactions(userReactions); // 원래 사용자 반응 상태로 복원
        showError(response.error || '반응 처리에 실패했습니다');
      }
    } catch (error) {
      // 오류 발생 시 원래 상태로 복원
      setPost(originalPost);
      setUserReactions(userReactions); // 원래 사용자 반응 상태로 복원
      showError('반응 처리 중 오류가 발생했습니다');
    } finally {
      // 요청 완료 처리
      setPendingReactions(prev => {
        const next = new Set(prev);
        next.delete(reactionType);
        return next;
      });
      
      // 성능 측정 종료
      performanceMeasurer.end(performanceId, { 
        reactionType, 
        postSlug: slug,
        finalCount: post?.stats?.[`${reactionType}_count`] 
      });
    }
  }, [user, post, slug, pendingReactions, showError]);

  const handleCommentAdded = async () => {
    if (!slug) return;
    
    try {
      console.log('🔄 댓글 새로고침 시작 - slug:', slug);
      const response = await apiClient.getCommentsBatch(slug);
      console.log('🔍 댓글 새로고침 응답:', {
        success: response.success,
        data: response.data,
        hasComments: !!response.data?.comments,
        commentsLength: response.data?.comments?.length || 0
      });
      
      if (response.success && response.data) {
        const processCommentsRecursive = (comments: any[]): any[] => {
          return comments.map(comment => {
            console.log('🔍 새로고침 댓글 처리:', {
              id: comment.id || comment._id,
              content: comment.content?.substring(0, 50) + '...',
              hasReplies: !!comment.replies,
              repliesCount: comment.replies?.length || 0,
              repliesData: comment.replies
            });
            
            return {
              ...comment,
              id: comment.id || comment._id,
              replies: comment.replies ? processCommentsRecursive(comment.replies) : []
            };
          });
        };
        
        // API 응답 구조 수정: 중첩된 데이터 구조 처리
        const actualComments = response.data.data?.comments || response.data.comments || [];
        const processedComments = processCommentsRecursive(actualComments);
        console.log('🔍 새로고침 처리된 댓글:', {
          originalComments: response.data.comments,
          nestedComments: response.data.data?.comments,
          actualComments,
          processedComments,
          processedLength: processedComments.length
        });
        setComments(processedComments);
      } else {
        console.log('❌ 댓글 새로고침 실패:', response);
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Seoul', // 한국 시간대 명시적 설정
    });
  };

  // 작성자 권한 체크 함수
  const isAuthor = () => {
    if (!user || !post) return false;
    
    // User ID로 비교 (문자열 변환)
    const userId = String(user.id);
    const authorId = String(post.author_id);
    
    if (userId === authorId) {
      return true;
    }
    
    // author 객체가 있으면 ID 비교
    if (post.author && String(user.id) === String(post.author.id)) {
      return true;
    }
    
    // 추가적인 비교: email 또는 user_handle
    if (post.author) {
      if (user.email && user.email === post.author.email) {
        return true;
      }
      if (user.user_handle && user.user_handle === post.author.user_handle) {
        return true;
      }
    }
    
    return false;
  };

  const handleEditPost = () => {
    navigate(`/posts/${slug}/edit`);
  };

  const handleDeletePost = async () => {
    if (!confirm('정말로 삭제하시겠습니까?')) return;
    
    try {
      const response = await apiClient.deletePost(slug!);
      if (response.success) {
        showSuccess('게시글이 삭제되었습니다');
        navigate('/board');
      } else {
        showError(response.error || '게시글 삭제에 실패했습니다');
      }
    } catch (error) {
      showError('게시글 삭제 중 오류가 발생했습니다');
    }
  };

  // ⚡ 페이지 마운트 후 즉시 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      if (!slug) return;
      
      setIsLoading(true);
      try {
        // 🚀 병렬 로딩: 게시글과 댓글을 동시에 호출
        const [postResult, commentsResult] = await Promise.all([
          apiClient.getPost(slug),
          apiClient.getCommentsBatch(slug)
        ]);
        
        // 게시글 처리
        if (postResult.success && postResult.data) {
          setPost(postResult.data);
          
          // 사용자 반응 상태 초기화 (로그인 사용자만)
          if (user && postResult.data.user_reaction) {
            setUserReactions({
              liked: postResult.data.user_reaction.liked || false,
              disliked: postResult.data.user_reaction.disliked || false,
              bookmarked: postResult.data.user_reaction.bookmarked || false
            });
          }
        } else {
          setIsNotFound(true);
          showError('게시글을 찾을 수 없습니다');
        }
        
        // 댓글 처리
        if (commentsResult.success && commentsResult.data) {
          console.log('🔥🔥🔥 ROUTE DEBUG - board.$slug.tsx (기본) 실행됨! getCommentsBatch 사용! 시간:', new Date().toISOString());
          console.log('🔍 댓글 API 응답 구조 분석:', {
            success: commentsResult.success,
            data: commentsResult.data,
            dataType: typeof commentsResult.data,
            hasComments: !!commentsResult.data.comments,
            commentsLength: commentsResult.data.comments?.length || 0,
            fullResponse: commentsResult,
            // 중첩된 데이터 구조 확인
            nestedData: commentsResult.data.data,
            nestedDataType: typeof commentsResult.data.data,
            nestedHasComments: !!commentsResult.data.data?.comments,
            nestedCommentsLength: commentsResult.data.data?.comments?.length || 0
          });
          
          const processCommentsRecursive = (comments: any[]): any[] => {
            return comments.map(comment => {
              console.log('🔍 댓글 처리:', {
                id: comment.id || comment._id,
                content: comment.content?.substring(0, 50) + '...',
                hasReplies: !!comment.replies,
                repliesCount: comment.replies?.length || 0,
                repliesData: comment.replies
              });
              
              return {
                ...comment,
                id: comment.id || comment._id,
                replies: comment.replies ? processCommentsRecursive(comment.replies) : []
              };
            });
          };
          
          // API 응답 구조 수정: 중첩된 데이터 구조 처리
          const actualComments = commentsResult.data.data?.comments || commentsResult.data.comments || [];
          const processedComments = processCommentsRecursive(actualComments);
          console.log('🔍 처리된 댓글 데이터:', {
            originalComments: commentsResult.data.comments,
            nestedComments: commentsResult.data.data?.comments,
            actualComments,
            processedComments,
            processedLength: processedComments.length
          });
          setComments(processedComments);
        } else {
          console.log('❌ 댓글 로딩 실패:', {
            success: commentsResult.success,
            error: commentsResult.error,
            data: commentsResult.data,
            fullResponse: commentsResult
          });
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
      <AppLayout title="게시글" user={user} onLogout={logout}>
        <div className="max-w-4xl mx-auto space-y-6">
          {/* 스켈레톤 UI - 게시글 헤더 */}
          <div className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="flex space-x-4 mb-4">
              <div className="h-4 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-24"></div>
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
            <div className="flex space-x-2">
              <div className="h-8 bg-gray-200 rounded w-16"></div>
              <div className="h-8 bg-gray-200 rounded w-16"></div>
              <div className="h-8 bg-gray-200 rounded w-16"></div>
            </div>
          </div>
          
          {/* 스켈레톤 UI - 게시글 내용 */}
          <div className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              <div className="h-4 bg-gray-200 rounded w-4/6"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
          
          {/* 스켈레톤 UI - 댓글 섹션 */}
          <div className="bg-white rounded-lg shadow p-6 animate-pulse">
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

  if (isNotFound || !post) {
    return (
      <AppLayout title="게시글을 찾을 수 없음" user={user} onLogout={logout}>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            게시글을 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 mb-6">
            {loaderData.error || "요청하신 게시글이 존재하지 않거나 삭제되었습니다."}
          </p>
          <Button onClick={() => navigate('/board')}>
            게시글 목록으로 돌아가기
          </Button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title={post.title} user={user} onLogout={logout}>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 게시글 헤더 */}
        <Card>
          <Card.Header>
            <div className="space-y-4">
              <div>
                <Card.Title level={1} className="text-2xl">
                  {post.title}
                </Card.Title>
              </div>
              
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                  {post.type}
                </span>
                <span>•</span>
                <span>
                  작성자: {post.author?.display_name || post.author?.user_handle || '익명'}
                </span>
                <span>•</span>
                <span>{formatDate(post.created_at)}</span>
                {post.stats && (
                  <>
                    <span>•</span>
                    <span>조회 {post.stats.view_count || post.stats.views}</span>
                  </>
                )}
              </div>

              <ReactionButtons 
                post={post} 
                onReactionChange={handleReactionChange}
                pendingReactions={pendingReactions}
              />
              
              {/* 수정/삭제 버튼 (작성자만 보이도록) */}
              {isAuthor() && (
                <div className="flex items-center space-x-2 pt-2 border-t border-gray-200">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleEditPost}
                    className="flex items-center space-x-1"
                  >
                    <span>✏️</span>
                    <span>수정</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDeletePost}
                    className="flex items-center space-x-1 text-red-600 hover:bg-red-50"
                  >
                    <span>🗑️</span>
                    <span>삭제</span>
                  </Button>
                </div>
              )}
            </div>
          </Card.Header>
        </Card>

        {/* 게시글 내용 */}
        <Card>
          <Card.Content>
            <div className="prose max-w-none">
              <div className="whitespace-pre-wrap text-gray-700">
                {post.content}
              </div>
            </div>
          </Card.Content>
        </Card>

        {/* 태그 */}
        {post.metadata?.tags && post.metadata.tags.length > 0 && (
          <Card>
            <Card.Content>
              <div className="flex flex-wrap gap-2">
                {post.metadata.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </Card.Content>
          </Card>
        )}

        {/* 댓글 섹션 */}
        <CommentSection
          postSlug={slug!}
          comments={comments}
          onCommentAdded={handleCommentAdded}
        />
      </div>
    </AppLayout>
  );
}