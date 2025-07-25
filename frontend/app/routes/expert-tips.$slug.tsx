import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useLoaderData } from '@remix-run/react';
import { json, type LoaderFunction, type MetaFunction } from '@remix-run/node';
import AppLayout from '~/components/layout/AppLayout';
import DetailPageLayout from '~/components/common/DetailPageLayout';
import { useAuth } from '~/contexts/AuthContext';
import { useNotification } from '~/contexts/NotificationContext';
import { apiClient } from '~/lib/api';
import type { Post, Tip, Comment } from '~/types';

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
        comments: comments
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
  const [isLoading] = useState(false); // SSR 데이터가 있으면 로딩 불필요
  const [isNotFound, setIsNotFound] = useState(!!loaderData?.error);
  const [pendingReactions, setPendingReactions] = useState<Set<string>>(new Set());
  const [userReactions, setUserReactions] = useState({
    liked: false,
    disliked: false,
    bookmarked: false
  });
  const [introduction, setIntroduction] = useState<string>('전문가');
  const [actualContent, setActualContent] = useState<string>('');

  // Post에서 introduction과 content 분리하는 함수
  const parsePostContent = (post: Post) => {
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
      introduction = '전문가';
      actualContent = post.content;
    }
    
    return { introduction, actualContent };
  };

  // Post를 Tip으로 변환하는 함수 (클라이언트에서 다시 필요)
  const convertPostToTip = (post: Post): Tip => {
    const { introduction, actualContent } = parsePostContent(post);
    
    return {
      id: parseInt(post.id),
      title: post.title,
      content: actualContent,
      slug: post.slug || post.id,
      expert_name: post.author?.display_name || '익명 전문가',
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
  

  const handleReactionChange = useCallback(async (reactionType: 'like' | 'dislike' | 'bookmark') => {
    if (!user) {
      showError('로그인이 필요합니다');
      return;
    }

    if (!post || !slug) return;

    if (pendingReactions.has(reactionType)) return;

    setPendingReactions(prev => new Set(prev).add(reactionType));

    // 🚀 1단계: 즉시 UI 업데이트 (낙관적 업데이트) - 게시판과 동일한 방식
    const originalPost = post;
    const originalUserReactions = userReactions;
    
    setPost(prev => {
      if (!prev) return null;
      
      const currentStats = prev.stats || {};
      const newStats = { ...currentStats };
      const newUserReactions = { ...userReactions };
      
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
          // 북마크 안 한 상태에서 클릭 = 북마크 (추천/비추천과 독립적)
          newStats.bookmark_count = (currentStats.bookmark_count || 0) + 1;
          newUserReactions.bookmarked = true;
        }
      }

      return {
        ...prev,
        stats: newStats
      };
    });
    
    // 사용자 반응 상태 즉시 업데이트
    setUserReactions(prev => {
      const newUserReactions = { ...prev };
      
      if (reactionType === 'like') {
        if (prev.liked) {
          newUserReactions.liked = false;
        } else {
          newUserReactions.liked = true;
          if (prev.disliked) {
            newUserReactions.disliked = false;
          }
        }
      } else if (reactionType === 'dislike') {
        if (prev.disliked) {
          newUserReactions.disliked = false;
        } else {
          newUserReactions.disliked = true;
          if (prev.liked) {
            newUserReactions.liked = false;
          }
        }
      } else if (reactionType === 'bookmark') {
        newUserReactions.bookmarked = !prev.bookmarked;
        // 북마크는 추천/비추천과 독립적이므로 다른 상태는 그대로 유지
      }
      
      return newUserReactions;
    });

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
        setUserReactions(originalUserReactions);
        showError(response.error || `${reactionType === 'like' ? '추천' : reactionType === 'dislike' ? '비추천' : '저장'} 처리에 실패했습니다`);
      }
    } catch (error) {
      // 오류 발생 시 원래 상태로 복원
      setPost(originalPost);
      setUserReactions(originalUserReactions);
      showError(`${reactionType === 'like' ? '추천' : reactionType === 'dislike' ? '비추천' : '저장'} 처리 중 오류가 발생했습니다`);
    } finally {
      // 요청 완료 처리
      setPendingReactions(prev => {
        const next = new Set(prev);
        next.delete(reactionType);
        return next;
      });
    }
  }, [user, post, slug, pendingReactions, userReactions, showError]);

  // 🗑️ 기존 loadComments 함수 제거 - 병렬 로딩으로 통합됨


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
        
        // 🔄 Post 객체의 댓글 수 실시간 업데이트
        setPost(prev => prev ? {
          ...prev,
          stats: {
            ...prev.stats,
            comment_count: totalCommentCount,
            // 기존 필드 유지
            view_count: prev.stats?.view_count || 0,
            like_count: prev.stats?.like_count || 0,
            dislike_count: prev.stats?.dislike_count || 0,
            bookmark_count: prev.stats?.bookmark_count || 0
          }
        } : null);
        
        console.log('📊 전문가 꿀정보 댓글 수 업데이트:', {
          totalComments: totalCommentCount,
          이전댓글수: post?.stats?.comment_count,
          새댓글수: totalCommentCount
        });
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };


  const handleEditPost = () => {
    navigate(`/expert-tip/${slug}/edit`);
  };

  const handleDeletePost = async () => {
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
        
        // content 파싱하여 introduction과 actualContent 분리
        const { introduction: parsedIntroduction, actualContent: parsedContent } = parsePostContent(loaderData.post);
        setIntroduction(parsedIntroduction);
        setActualContent(parsedContent);
        
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
        }
      } else {
        // SSR에서 데이터가 없으면 404 처리
        setIsNotFound(true);
        showError('전문가 꿀정보를 찾을 수 없습니다');
      }
    };
    
    initializeData();
  }, [slug, loaderData]);

  // 🚀 사용자 로그인 후 댓글 user_reaction 정보 새로고침
  useEffect(() => {
    const refreshCommentsWithUserReactions = async () => {
      if (!slug || !user) return; // 사용자가 로그인하지 않으면 생략
      
      try {
        console.log('🔄 사용자 로그인 후 댓글 user_reaction 새로고침 시작');
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
          
          const processCommentsRecursive = (comments: any[]): any[] => {
            return comments.map(comment => ({
              ...comment,
              id: comment.id || comment._id,
              replies: comment.replies ? processCommentsRecursive(comment.replies) : []
            }));
          };
          
          const processedComments = processCommentsRecursive(comments);
          setComments(processedComments);
          console.log('✅ 사용자 반응 정보가 포함된 댓글 목록 새로고침 완료');
        }
      } catch (error) {
        console.error('❌ 댓글 user_reaction 새로고침 실패:', error);
      }
    };
    
    refreshCommentsWithUserReactions();
  }, [slug, user]); // user가 변경될 때마다 실행

  if (isLoading) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </AppLayout>
    );
  }

  if (isNotFound || !tip || !post) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            전문가 꿀정보를 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 mb-6">
            {loaderData.error || "요청하신 전문가 꿀정보가 존재하지 않거나 삭제되었습니다."}
          </p>
          <button
            onClick={() => navigate('/tips')}
            className="inline-block px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            전문가 꿀정보 목록으로 돌아가기
          </button>
        </div>
      </AppLayout>
    );
  }

  // 전문가 소개 섹션 컴포넌트
  const ExpertIntroSection = () => (
    <div className="border-b border-gray-200 pb-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <span>👨‍💼</span>
        <span>전문가 소개</span>
      </h2>
      
      <div className="text-gray-700 text-base leading-relaxed whitespace-pre-wrap">
        {introduction}
      </div>
    </div>
  );

  // 전문가의 한 수 섹션 컴포넌트
  const ExpertContentSection = () => (
    <div className="mb-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <span>💡</span>
        <span>전문가의 한 수</span>
      </h2>
      
      <div className="text-base leading-relaxed text-gray-700 whitespace-pre-wrap">
        {actualContent}
      </div>
    </div>
  );

  // 태그는 DetailPageLayout에서 자동으로 표시되므로 중복 제거

  // 반응 버튼은 DetailPageLayout에서 자동으로 제공되므로 중복 제거

  return (
    <AppLayout 
      user={user}
      onLogout={logout}
    >
      <div className="max-w-4xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="flex items-center justify-between mb-6">
          <button 
            onClick={() => navigate('/tips')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 목록으로
          </button>
        </div>

      <DetailPageLayout
        post={post}
        user={user || undefined}
        comments={comments}
        onReactionChange={handleReactionChange}
        onCommentAdded={handleCommentAdded}
        onEditPost={handleEditPost}
        onDeletePost={handleDeletePost}
        isLoading={isLoading}
        pendingReactions={pendingReactions}
        userReactions={userReactions}
        postSlug={slug!}
        pageType="expert_tips"
        sections={{
          beforeContent: [<ExpertIntroSection key="expert-intro" />],
          afterContent: [<ExpertContentSection key="expert-content" />]
        }}
      />
      </div>
    </AppLayout>
  );
}