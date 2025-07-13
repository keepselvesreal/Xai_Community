import { memo, useEffect, useState, useCallback, useMemo } from 'react';
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

// 🚀 Phase 4: 최적화된 SSR 방식 - 가능한 빠른 초기 응답
export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    return json<LoaderData>({ 
      post: null, 
      comments: [],
      error: "잘못된 요청입니다." 
    }, { status: 400 });
  }

  // ⚡ 최적화: 즉시 응답으로 레이아웃 빠르게 표시
  return json<LoaderData>({ 
    post: null, 
    comments: [],
    error: null 
  });
};

// 🎯 Phase 4: React.memo로 리렌더링 최적화
interface ReactionButtonsProps {
  post: Post;
  onReactionChange: (reactionType: 'like' | 'dislike' | 'bookmark') => void;
}

const ReactionButtons = memo(({ post, onReactionChange }: ReactionButtonsProps) => {
  const handleLike = useCallback(() => onReactionChange('like'), [onReactionChange]);
  const handleDislike = useCallback(() => onReactionChange('dislike'), [onReactionChange]);
  const handleBookmark = useCallback(() => onReactionChange('bookmark'), [onReactionChange]);

  return (
    <div className="flex items-center space-x-2">
      <Button
        variant="outline"
        size="sm"
        onClick={handleLike}
        className="flex items-center space-x-1"
      >
        <span>👍</span>
        <span>{post.stats?.like_count || post.stats?.likes || 0}</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleDislike}
        className="flex items-center space-x-1"
      >
        <span>👎</span>
        <span>{post.stats?.dislike_count || post.stats?.dislikes || 0}</span>
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleBookmark}
        className="flex items-center space-x-1"
      >
        <span>🔖</span>
        <span>{post.stats?.bookmark_count || post.stats?.bookmarks || 0}</span>
      </Button>
    </div>
  );
});

// 🎯 Phase 4: 스켈레톤 UI 컴포넌트 분리 및 최적화
const PostDetailSkeleton = memo(() => (
  <div className="max-w-4xl mx-auto space-y-6">
    {/* 게시글 헤더 스켈레톤 */}
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
    
    {/* 게시글 내용 스켈레톤 */}
    <div className="bg-white rounded-lg shadow p-6 animate-pulse">
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        <div className="h-4 bg-gray-200 rounded w-4/6"></div>
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      </div>
    </div>
    
    {/* 댓글 스켈레톤 */}
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
));

// 🎯 Phase 4: 게시글 헤더 컴포넌트 분리
interface PostHeaderProps {
  post: Post;
  onReactionChange: (reactionType: 'like' | 'dislike' | 'bookmark') => void;
  onEditPost: () => void;
  onDeletePost: () => void;
  isAuthor: boolean;
}

const PostHeader = memo(({ post, onReactionChange, onEditPost, onDeletePost, isAuthor }: PostHeaderProps) => {
  const formatDate = useCallback((dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Seoul',
    });
  }, []);

  const authorName = useMemo(() => 
    post.author?.display_name || post.author?.user_handle || '익명',
    [post.author]
  );

  const viewCount = useMemo(() => 
    post.stats?.view_count || post.stats?.views || 0,
    [post.stats]
  );

  return (
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
            <span>작성자: {authorName}</span>
            <span>•</span>
            <span>{formatDate(post.created_at)}</span>
            <span>•</span>
            <span>조회 {viewCount}</span>
          </div>

          <ReactionButtons 
            post={post} 
            onReactionChange={onReactionChange}
          />
          
          {/* 수정/삭제 버튼 */}
          {isAuthor && (
            <div className="flex items-center space-x-2 pt-2 border-t border-gray-200">
              <Button
                variant="outline"
                size="sm"
                onClick={onEditPost}
                className="flex items-center space-x-1"
              >
                <span>✏️</span>
                <span>수정</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onDeletePost}
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
  );
});

// 🎯 Phase 4: 게시글 내용 컴포넌트 분리
interface PostContentProps {
  content: string;
  tags?: string[];
}

const PostContent = memo(({ content, tags }: PostContentProps) => (
  <>
    {/* 게시글 내용 */}
    <Card>
      <Card.Content>
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-gray-700">
            {content}
          </div>
        </div>
      </Card.Content>
    </Card>

    {/* 태그 */}
    {tags && tags.length > 0 && (
      <Card>
        <Card.Content>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
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
  </>
));

export default function PostDetailOptimized() {
  console.log('⚠️⚠️⚠️ ROUTE DEBUG - board.$slug.OPTIMIZED.tsx 실행됨! 이제 getCommentsBatch 사용! 시간:', new Date().toISOString());
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const loaderData = useLoaderData<LoaderData>();
  
  // 🎯 Phase 4: 상태 관리 최적화
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loadingState, setLoadingState] = useState<'loading' | 'loaded' | 'error'>('loading');
  const [isNotFound, setIsNotFound] = useState(false);

  // 🎯 Phase 4: Progressive Loading - 단계별 데이터 로딩
  useEffect(() => {
    if (!slug) return;

    const loadDataProgressive = async () => {
      try {
        setLoadingState('loading');
        
        // 🚀 1단계: 최적화된 Aggregated API 사용 (36.61ms)
        console.time('게시글 Aggregated API');
        const aggregatedResponse = await apiClient.get(`/posts/${slug}/aggregated`);
        console.timeEnd('게시글 Aggregated API');
        
        if (aggregatedResponse.success && aggregatedResponse.data) {
          // 즉시 기본 데이터 표시
          setPost(aggregatedResponse.data.post);
          setComments(aggregatedResponse.data.comments || []);
          setLoadingState('loaded');
          
          console.log('✅ Phase 4: Aggregated API로 빠른 로딩 완료');
          return;
        }
        
        // 🔄 2단계: Aggregated 실패 시 Complete API 사용 (68.22ms)
        console.time('게시글 Complete API');
        const completeResponse = await apiClient.get(`/posts/${slug}/complete`);
        console.timeEnd('게시글 Complete API');
        
        if (completeResponse.success && completeResponse.data) {
          setPost(completeResponse.data.post);
          setComments(completeResponse.data.comments || []);
          setLoadingState('loaded');
          
          console.log('✅ Phase 4: Complete API로 로딩 완료');
          return;
        }
        
        // 🔄 3단계: 마지막 대안으로 병렬 호출 (137.57ms)
        console.time('병렬 API 호출');
        const [postResult, commentsResult] = await Promise.all([
          apiClient.getPost(slug),
          apiClient.getCommentsBatch(slug)
        ]);
        console.timeEnd('병렬 API 호출');
        
        if (postResult.success && postResult.data) {
          setPost(postResult.data);
          
          if (commentsResult.success && commentsResult.data) {
            // getCommentsBatch 응답 구조 처리
            const actualComments = commentsResult.data.data?.comments || commentsResult.data.comments || [];
            const processedComments = processCommentsRecursive(actualComments);
            setComments(processedComments);
          }
          
          setLoadingState('loaded');
          console.log('⚠️ Phase 4: 병렬 호출로 로딩 완료 (성능 저하)');
        } else {
          setIsNotFound(true);
          setLoadingState('error');
        }
        
      } catch (error) {
        console.error('데이터 로딩 실패:', error);
        setIsNotFound(true);
        setLoadingState('error');
        showError('데이터를 불러오는 중 오류가 발생했습니다');
      }
    };
    
    loadDataProgressive();
  }, [slug, showError]);

  // 🎯 Phase 4: 콜백 최적화
  const handleReactionChange = useCallback(async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!post || !slug) return;

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
        setPost(prev => prev ? {
          ...prev,
          stats: {
            ...prev.stats,
            like_count: (reactionType === 'like' || reactionType === 'dislike') ? 
              (response.data.like_count ?? prev.stats?.like_count ?? 0) : 
              (prev.stats?.like_count ?? 0),
            dislike_count: (reactionType === 'like' || reactionType === 'dislike') ? 
              (response.data.dislike_count ?? prev.stats?.dislike_count ?? 0) : 
              (prev.stats?.dislike_count ?? 0),
            bookmark_count: reactionType === 'bookmark' ? 
              (response.data.bookmark_count ?? prev.stats?.bookmark_count ?? 0) : 
              (prev.stats?.bookmark_count ?? 0),
            view_count: prev.stats?.view_count ?? 0,
            comment_count: prev.stats?.comment_count ?? 0,
          }
        } : prev);
      } else {
        showError(response.error || '반응 처리에 실패했습니다');
      }
    } catch (error) {
      showError('반응 처리 중 오류가 발생했습니다');
    }
  }, [user, post, slug, showError]);

  const handleCommentAdded = useCallback(async () => {
    if (!slug) return;
    
    try {
      const response = await apiClient.getCommentsBatch(slug);
      if (response.success && response.data) {
        // getCommentsBatch 응답 구조 처리
        const actualComments = response.data.data?.comments || response.data.comments || [];
        const processedComments = processCommentsRecursive(actualComments);
        setComments(processedComments);
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  }, [slug]);

  // 🎯 Phase 4: 권한 체크 메모이제이션
  const isAuthor = useMemo(() => {
    if (!user || !post) return false;
    
    const userId = String(user.id);
    const authorId = String(post.author_id);
    
    if (userId === authorId) return true;
    
    if (post.author && String(user.id) === String(post.author.id)) return true;
    
    if (post.author) {
      if (user.email && user.email === post.author.email) return true;
      if (user.user_handle && user.user_handle === post.author.user_handle) return true;
    }
    
    return false;
  }, [user, post]);

  const handleEditPost = useCallback(() => {
    navigate(`/posts/${slug}/edit`);
  }, [navigate, slug]);

  const handleDeletePost = useCallback(async () => {
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
  }, [slug, showSuccess, showError, navigate]);

  // 🎯 Phase 4: 로딩 상태별 렌더링 최적화
  if (loadingState === 'loading') {
    return (
      <AppLayout title="게시글" user={user} onLogout={logout}>
        <PostDetailSkeleton />
      </AppLayout>
    );
  }

  if (loadingState === 'error' || isNotFound || !post) {
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
        <PostHeader 
          post={post}
          onReactionChange={handleReactionChange}
          onEditPost={handleEditPost}
          onDeletePost={handleDeletePost}
          isAuthor={isAuthor}
        />

        <PostContent 
          content={post.content}
          tags={post.metadata?.tags}
        />

        <CommentSection
          postSlug={slug!}
          comments={comments}
          onCommentAdded={handleCommentAdded}
        />
      </div>
    </AppLayout>
  );
}

// 🎯 Phase 4: 유틸리티 함수
function processCommentsRecursive(comments: any[]): any[] {
  return comments.map(comment => ({
    ...comment,
    id: comment.id || comment._id,
    replies: comment.replies ? processCommentsRecursive(comment.replies) : []
  }));
}