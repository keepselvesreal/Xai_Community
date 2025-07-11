import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link, useLoaderData } from '@remix-run/react';
import { json, type LoaderFunction, type MetaFunction } from '@remix-run/node';
import AppLayout from '~/components/layout/AppLayout';
import CommentSection from '~/components/comment/CommentSection';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';
import type { Post, Tip, Comment } from '~/types';
import { formatNumber } from "~/lib/utils";

interface LoaderData {
  post: Post | null;
  tip: Tip | null;
  comments: Comment[];
  error?: string;
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  if (!data?.post) {
    return [
      { title: "전문가 꿀정보 | XAI 아파트 커뮤니티" },
      { name: "description", content: "XAI 아파트 커뮤니티의 전문가 꿀정보를 확인하세요." },
    ];
  }

  const { post } = data;
  return [
    { title: `${post.title} | XAI 아파트 커뮤니티` },
    { name: "description", content: post.metadata?.summary || post.title },
    { property: "og:title", content: post.title },
    { property: "og:description", content: post.metadata?.summary || post.title },
    { property: "og:type", content: "article" },
  ];
};

// 🚀 SSR 방식: 서버에서 데이터를 미리 로드하여 깜빡임 방지
export const loader: LoaderFunction = async ({ params }) => {
  const { slug } = params;
  
  if (!slug) {
    return json<LoaderData>({ 
      post: null, 
      tip: null,
      comments: [],
      error: "잘못된 요청입니다." 
    }, { status: 400 });
  }

  try {
    // 서버에서 게시글과 댓글 데이터 미리 로드
    const [postResult, commentsResult] = await Promise.all([
      apiClient.getPost(slug),
      apiClient.getCommentsBatch(slug)
    ]);

    // 게시글 데이터 처리
    if (postResult.success && postResult.data) {
      // expert_tips 타입 확인
      if (postResult.data.metadata?.type !== 'expert_tips') {
        return json<LoaderData>({ 
          post: null, 
          tip: null,
          comments: [],
          error: "해당 전문가 꿀정보를 찾을 수 없습니다." 
        }, { status: 404 });
      }

      // 댓글 데이터 처리
      let comments = [];
      if (commentsResult.success && commentsResult.data) {
        if (commentsResult.data.data?.comments) {
          comments = commentsResult.data.data.comments;
        } else if (commentsResult.data.comments) {
          comments = commentsResult.data.comments;
        } else if (Array.isArray(commentsResult.data)) {
          comments = commentsResult.data;
        }
      }

      return json<LoaderData>({ 
        post: postResult.data, 
        tip: null, // 클라이언트에서 변환
        comments: comments,
        error: null 
      });
    } else {
      return json<LoaderData>({ 
        post: null, 
        tip: null,
        comments: [],
        error: "전문가 꿀정보를 찾을 수 없습니다." 
      }, { status: 404 });
    }
  } catch (error) {
    console.error('SSR Loader Error (expert-tips):', error);
    return json<LoaderData>({ 
      post: null, 
      tip: null,
      comments: [],
      error: "데이터를 불러오는 중 오류가 발생했습니다." 
    }, { status: 500 });
  }
};

export default function ExpertTipDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const loaderData = useLoaderData<LoaderData>();
  
  // ⚡ SSR: 서버에서 로드된 데이터를 초기값으로 사용
  const [tip, setTip] = useState<Tip | null>(null);
  const [post, setPost] = useState<Post | null>(loaderData?.post || null);
  const [comments, setComments] = useState<Comment[]>(loaderData?.comments || []);
  const [isLoading, setIsLoading] = useState(false); // SSR 데이터가 있으면 로딩 불필요
  const [isNotFound, setIsNotFound] = useState(!!loaderData?.error);
  const [isLiked, setIsLiked] = useState(false);
  const [isDisliked, setIsDisliked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [dislikeCount, setDislikeCount] = useState(0);
  const [bookmarkCount, setBookmarkCount] = useState(0);
  const [commentCount, setCommentCount] = useState(0);

  // Post를 Tip으로 변환하는 함수 (클라이언트에서 다시 필요)
  const convertPostToTip = (post: Post): Tip => {
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
      introduction = post.metadata?.expert_title || '전문가';
      actualContent = post.content;
    }
    
    return {
      id: parseInt(post.id),
      title: post.title,
      content: actualContent,
      slug: post.slug || post.id,
      expert_name: post.author?.display_name || post.metadata?.expert_name || '익명 전문가',
      expert_title: introduction,
      created_at: post.created_at,
      category: post.metadata?.category || '생활',
      tags: post.metadata?.tags || [],
      views_count: post.stats?.view_count || 0,
      likes_count: post.stats?.like_count || 0,
      dislikes_count: post.stats?.dislike_count || 0,
      comments_count: post.stats?.comment_count || 0,
      saves_count: post.stats?.bookmark_count || 0,
      is_new: new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000
    };
  };

  // 🗑️ 기존 loadTip 함수 제거 - 병렬 로딩으로 통합됨
  

  const handleLike = async () => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!tip || !slug) return;

    try {
      const response = await apiClient.likePost(slug);
      
      if (response.success) {
        if (response.data) {
          // 추천/비추천은 서로 배타적으로 업데이트
          setLikeCount(response.data.like_count || 0);
          setDislikeCount(response.data.dislike_count || 0);
          // 저장 기능은 독립적이므로 업데이트하지 않음
        }
      } else {
        showError(response.error || '추천 처리에 실패했습니다');
      }
    } catch (error) {
      showError('추천 처리 중 오류가 발생했습니다');
    }
  };

  const handleDislike = async () => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!tip || !slug) return;

    try {
      const response = await apiClient.dislikePost(slug);
      
      if (response.success) {
        if (response.data) {
          // 추천/비추천은 서로 배타적으로 업데이트
          setLikeCount(response.data.like_count || 0);
          setDislikeCount(response.data.dislike_count || 0);
          // 저장 기능은 독립적이므로 업데이트하지 않음
        }
      } else {
        showError(response.error || '비추천 처리에 실패했습니다');
      }
    } catch (error) {
      showError('비추천 처리 중 오류가 발생했습니다');
    }
  };

  const handleBookmark = async () => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!tip || !slug) return;

    try {
      const response = await apiClient.bookmarkPost(slug);
      
      if (response.success) {
        if (response.data) {
          // 저장 기능은 추천/비추천과 독립적이므로 북마크 수만 업데이트
          setBookmarkCount(response.data.bookmark_count || 0);
          // 추천/비추천 수는 변경하지 않음
        }
      } else {
        showError(response.error || '저장 처리에 실패했습니다');
      }
    } catch (error) {
      showError('저장 처리 중 오류가 발생했습니다');
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

  // 🗑️ 기존 loadComments 함수 제거 - 병렬 로딩으로 통합됨

  const formatDateSimple = (dateString: string): string => {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

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
        
        const processCommentsRecursive = (comments: any[]): any[] => {
          return comments.map(comment => ({
            ...comment,
            id: comment.id || comment._id,
            replies: comment.replies ? processCommentsRecursive(comment.replies) : []
          }));
        };
        
        const processedComments = processCommentsRecursive(comments);
        setComments(processedComments);
        
        // 댓글 수 업데이트 (중첩된 답글 포함 총 개수 계산)
        const countAllComments = (comments: any[]): number => {
          return comments.reduce((total, comment) => {
            return total + 1 + (comment.replies ? countAllComments(comment.replies) : 0);
          }, 0);
        };
        
        const totalCommentCount = countAllComments(processedComments);
        setCommentCount(totalCommentCount);
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  // 작성자 권한 체크 함수
  const isAuthor = () => {
    if (!user || !tip) return false;
    
    // User ID로 비교 (문자열 변환)
    const userId = String(user.id);
    
    // tip에서 변환된 데이터는 author_id가 없을 수 있으므로 원본 post 데이터 사용 필요
    // loadTip에서 받은 response.data의 author_id를 사용
    if (post && post.author_id) {
      const authorId = String(post.author_id);
      if (userId === authorId) {
        return true;
      }
    }
    
    // author 객체가 있으면 ID 비교
    if (post && post.author && String(user.id) === String(post.author.id)) {
      return true;
    }
    
    // 추가적인 비교: email 또는 user_handle
    if (post && post.author) {
      if (user.email && user.email === post.author.email) {
        return true;
      }
      if (user.user_handle && user.user_handle === post.author.user_handle) {
        return true;
      }
    }
    
    return false;
  };

  const handleEditTip = () => {
    navigate(`/expert-tip/${slug}/edit`);
  };

  const handleDeleteTip = async () => {
    if (!confirm('정말로 삭제하시겠습니까?')) return;
    
    try {
      const response = await apiClient.deletePost(slug!);
      if (response.success) {
        showSuccess('전문가 꿀정보가 삭제되었습니다');
        navigate('/tips');
      } else {
        showError(response.error || '게시글 삭제에 실패했습니다');
      }
    } catch (error) {
      showError('게시글 삭제 중 오류가 발생했습니다');
    }
  };

  // ⚡ SSR 데이터 활용: 서버에서 로드된 데이터를 초기화
  useEffect(() => {
    const initializeData = () => {
      if (!slug) return;
      
      // SSR에서 에러가 있으면 에러 상태 유지
      if (loaderData.error) {
        setIsNotFound(true);
        showError(loaderData.error);
        return;
      }
      
      // SSR에서 로드된 post 데이터가 있으면 tip으로 변환
      if (loaderData.post) {
        const convertedTip = convertPostToTip(loaderData.post);
        setTip(convertedTip);
        setLikeCount(convertedTip.likes_count);
        setDislikeCount(loaderData.post.stats?.dislike_count || 0);
        setBookmarkCount(convertedTip.saves_count);
        setCommentCount(loaderData.post.stats?.comment_count || 0);
        
        // 댓글 처리 (SSR에서 로드된 댓글 데이터)
        if (loaderData.comments) {
          const processCommentsRecursive = (comments: any[]): any[] => {
            return comments.map(comment => ({
              ...comment,
              id: comment.id || comment._id,
              replies: comment.replies ? processCommentsRecursive(comment.replies) : []
            }));
          };
          
          const processedComments = processCommentsRecursive(loaderData.comments);
          setComments(processedComments);
          
          // 댓글 수 업데이트 (중첩된 답글 포함 총 개수 계산)
          const countAllComments = (comments: any[]): number => {
            return comments.reduce((total, comment) => {
              return total + 1 + (comment.replies ? countAllComments(comment.replies) : 0);
            }, 0);
          };
          
          const totalCommentCount = countAllComments(processedComments);
          setCommentCount(totalCommentCount);
        }
      } else {
        // SSR에서 데이터가 없으면 404 처리
        setIsNotFound(true);
        showError('전문가 꿀정보를 찾을 수 없습니다');
      }
    };
    
    initializeData();
  }, [slug, loaderData]);

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
            {loaderData.error || "요청하신 전문가 꿀정보가 존재하지 않거나 삭제되었습니다."}
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
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-var-secondary hover:text-var-primary transition-colors mr-4"
        >
          <span>←</span>
          <span>뒤로가기</span>
        </button>
        <Link 
          to="/tips"
          className="inline-flex items-center gap-2 text-var-secondary hover:text-var-primary transition-colors"
        >
          <span>📋</span>
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
              <span className="text-lg">👍</span>
              <span className="text-sm">추천 {formatNumber(likeCount)}</span>
            </button>
            <button
              onClick={handleDislike}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className="text-lg">👎</span>
              <span className="text-sm">비추천 {formatNumber(dislikeCount)}</span>
            </button>
            <button
              onClick={handleBookmark}
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              <span className="text-lg">🔖</span>
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
        
        {/* 수정/삭제 버튼 (작성자만 보이도록) */}
        {isAuthor() && (
          <div className="flex items-center justify-center gap-3 mt-4 pt-4 border-t border-white/20">
            <button
              onClick={handleEditTip}
              className="flex items-center gap-2 px-4 py-2 bg-white/20 text-white rounded-lg hover:bg-white/30 transition-colors"
            >
              <span>✏️</span>
              <span>수정</span>
            </button>
            <button
              onClick={handleDeleteTip}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-white rounded-lg hover:bg-red-500/30 transition-colors"
            >
              <span>🗑️</span>
              <span>삭제</span>
            </button>
          </div>
        )}
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
            <div className="text-3xl font-bold text-red-600 mb-1">{formatNumber(dislikeCount)}</div>
            <div className="text-sm text-var-muted">비추천</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-1">{formatNumber(commentCount)}</div>
            <div className="text-sm text-var-muted">댓글</div>
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