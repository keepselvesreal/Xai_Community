import { useEffect, useState } from 'react';
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
}

const ReactionButtons = ({ post, onReactionChange }: ReactionButtonsProps) => {
  return (
    <div className="flex items-center space-x-2">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onReactionChange('like')}
        className="flex items-center space-x-1"
      >
        <span>👍</span>
        <span>{post.stats?.like_count || post.stats?.likes || 0}</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onReactionChange('dislike')}
        className="flex items-center space-x-1"
      >
        <span>👎</span>
        <span>{post.stats?.dislike_count || post.stats?.dislikes || 0}</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => onReactionChange('bookmark')}
        className="flex items-center space-x-1"
      >
        <span>🔖</span>
        <span>{post.stats?.bookmark_count || post.stats?.bookmarks || 0}</span>
      </Button>
    </div>
  );
};


export default function PostDetailComplete() {
  console.log('🌟🌟🌟 ROUTE DEBUG - board.$slug.COMPLETE.tsx 실행됨! API 확인 필요! 시간:', new Date().toISOString());
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
  const [loadTime, setLoadTime] = useState<number | null>(null); // 성능 측정용

  const handleReactionChange = async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!post || !slug) return;

    try {
      let response;
      
      // API v3 명세서에 따른 개별 엔드포인트 사용
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
      
      if (response.success) {
        // 페이지 전체 새로고침 대신 직접 상태 업데이트
        if (response.data) {
          setPost(prev => prev ? {
            ...prev,
            stats: {
              ...prev.stats,
              // 추천/비추천은 서로 배타적으로 업데이트
              like_count: (reactionType === 'like' || reactionType === 'dislike') ? 
                (response.data.like_count ?? prev.stats?.like_count ?? 0) : 
                (prev.stats?.like_count ?? 0),
              dislike_count: (reactionType === 'like' || reactionType === 'dislike') ? 
                (response.data.dislike_count ?? prev.stats?.dislike_count ?? 0) : 
                (prev.stats?.dislike_count ?? 0),
              // 저장 기능은 독립적으로 업데이트
              bookmark_count: reactionType === 'bookmark' ? 
                (response.data.bookmark_count ?? prev.stats?.bookmark_count ?? 0) : 
                (prev.stats?.bookmark_count ?? 0),
              view_count: prev.stats?.view_count ?? 0,
              comment_count: prev.stats?.comment_count ?? 0,
            }
          } : prev);
        }
      } else {
        showError(response.error || '반응 처리에 실패했습니다');
      }
    } catch (error) {
      showError('반응 처리 중 오류가 발생했습니다');
    }
  };

  const handleCommentAdded = async () => {
    if (!slug) return;
    
    // 완전 통합 방식으로 다시 로드
    await loadCompleteData();
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

  // 🚀 완전 통합 데이터 로드 함수
  const loadCompleteData = async () => {
    if (!slug) return;
    
    const startTime = performance.now();
    
    try {
      // 🚀 완전 통합 Aggregation: 단일 API 호출로 모든 데이터 조회
      const result = await apiClient.getPostComplete(slug);
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      setLoadTime(duration);
      
      console.log(`🚀 완전 통합 로딩 완료: ${duration.toFixed(2)}ms`);
      
      if (result.success && result.data) {
        const data = result.data;
        
        // 게시글 데이터 설정
        setPost(data);
        
        // 댓글 데이터 처리
        if (data.comments) {
          const processCommentsRecursive = (comments: any[]): any[] => {
            return comments.map(comment => ({
              ...comment,
              id: comment.id || comment._id,
              replies: comment.replies ? processCommentsRecursive(comment.replies) : []
            }));
          };
          
          const processedComments = processCommentsRecursive(data.comments || []);
          setComments(processedComments);
        }
      } else {
        setIsNotFound(true);
        showError('게시글을 찾을 수 없습니다');
      }
    } catch (error) {
      setIsNotFound(true);
      showError('데이터를 불러오는 중 오류가 발생했습니다');
    }
  };

  // ⚡ 페이지 마운트 후 즉시 완전 통합 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await loadCompleteData();
      setIsLoading(false);
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
        {/* 성능 측정 표시 (개발용) */}
        {loadTime && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <p className="text-sm text-green-800">
              🚀 완전 통합 로딩 시간: <strong>{loadTime.toFixed(2)}ms</strong>
            </p>
          </div>
        )}

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