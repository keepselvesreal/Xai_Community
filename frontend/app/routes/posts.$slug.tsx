import { useEffect, useState } from 'react';
import { useParams, useNavigate } from '@remix-run/react';
import AppLayout from '~/components/layout/AppLayout';
import Card from '~/components/ui/Card';
import Button from '~/components/ui/Button';
import Textarea from '~/components/ui/Textarea';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';
import type { Post, Comment, PaginatedResponse } from '~/types';

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

interface CommentSectionProps {
  postSlug: string;
  comments: Comment[];
  onCommentAdded: () => void;
}

const CommentSection = ({ postSlug, comments, onCommentAdded }: CommentSectionProps) => {
  const { user } = useAuth();
  const { showSuccess, showError } = useNotification();
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmitComment = async () => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!newComment.trim()) {
      showError('댓글 내용을 입력해주세요');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await apiClient.createComment(postSlug, {
        content: newComment.trim(),
      });

      if (response.success) {
        setNewComment('');
        onCommentAdded();
        showSuccess('댓글이 작성되었습니다');
      } else {
        showError(response.error || '댓글 작성에 실패했습니다');
      }
    } catch (error) {
      showError('댓글 작성 중 오류가 발생했습니다');
    } finally {
      setIsSubmitting(false);
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
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          댓글 <span className="text-blue-600">{comments?.length || 0}</span>개
        </h3>
      </div>

      {/* 댓글 작성 폼 */}
      {user && (
        <Card>
          <Card.Content>
            <div className="space-y-4">
              <Textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="댓글을 작성해주세요..."
                rows={3}
              />
              <div className="flex justify-end">
                <Button
                  onClick={handleSubmitComment}
                  disabled={!newComment.trim() || isSubmitting}
                  loading={isSubmitting}
                >
                  댓글 작성
                </Button>
              </div>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* 댓글 목록 */}
      <div className="space-y-4">
        {comments?.map((comment) => (
          <Card key={comment.id}>
            <Card.Content>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      {comment.author?.display_name || comment.author?.user_handle || '익명'}
                    </span>
                    <span className="text-sm text-gray-500">
                      {formatDate(comment.created_at)}
                    </span>
                  </div>
                </div>
                <div className="text-gray-700 whitespace-pre-wrap">
                  {comment.content}
                </div>
              </div>
            </Card.Content>
          </Card>
        ))}

        {(!comments || comments.length === 0) && (
          <div className="text-center py-8 text-gray-500">
            아직 댓글이 없습니다. 첫 번째 댓글을 작성해보세요!
          </div>
        )}
      </div>
    </div>
  );
};

export default function PostDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showError } = useNotification();
  
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);

  const loadPost = async () => {
    if (!slug) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.getPost(slug);
      if (response.success && response.data) {
        setPost(response.data);
      } else {
        setIsNotFound(true);
        showError('게시글을 찾을 수 없습니다');
      }
    } catch (error) {
      setIsNotFound(true);
      showError('게시글을 불러오는 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  const loadComments = async () => {
    if (!slug) return;
    
    try {
      const response = await apiClient.getComments(slug);
      if (response.success && response.data) {
        setComments(response.data.items);
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
        // 게시글 데이터 새로고침
        await loadPost();
      } else {
        showError(response.error || '반응 처리에 실패했습니다');
      }
    } catch (error) {
      showError('반응 처리 중 오류가 발생했습니다');
    }
  };

  const handleCommentAdded = () => {
    loadComments();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  useEffect(() => {
    loadPost();
    loadComments();
  }, [slug]);

  if (isLoading) {
    return (
      <AppLayout title="게시글" user={user}>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </AppLayout>
    );
  }

  if (isNotFound || !post) {
    return (
      <AppLayout title="게시글을 찾을 수 없음" user={user}>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            게시글을 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 mb-6">
            요청하신 게시글이 존재하지 않거나 삭제되었습니다.
          </p>
          <Button onClick={() => navigate('/posts')}>
            게시글 목록으로 돌아가기
          </Button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title={post.title} user={user}>
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
              />
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
        {post.tags && post.tags.length > 0 && (
          <Card>
            <Card.Content>
              <div className="flex flex-wrap gap-2">
                {post.tags.map((tag, index) => (
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