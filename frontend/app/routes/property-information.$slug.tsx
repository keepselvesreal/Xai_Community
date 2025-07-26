import { json, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, useNavigate, useParams } from "@remix-run/react";
import { useState, useEffect, useCallback } from "react";
import AppLayout from "~/components/layout/AppLayout";
import DetailPageLayout from "~/components/common/DetailPageLayout";
import SafeHTMLRenderer from "~/components/common/SafeHTMLRenderer";
import { useAuth } from "~/contexts/AuthContext";
import { useNotification } from "~/contexts/NotificationContext";
import { apiClient } from "~/lib/api";
import type { Post, Comment } from "~/types";

interface LoaderData {
  post: Post | null;
  comments: Comment[];
  error?: string;
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  // Hybrid 방식에서는 loader가 의도적으로 null을 반환하므로 기본 메타데이터 제공
  if (!data?.post) {
    return [
      { title: "부동산 정보 | XAI 아파트 커뮤니티" },
      { name: "description", content: "XAI 아파트 커뮤니티의 부동산 정보를 확인하세요." },
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

export default function PropertyInformationDetail() {
  const { slug } = useParams();
  const loaderData = useLoaderData<LoaderData>();
  const { user, logout } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();
  
  // ⚡ Hybrid: 페이지 구조는 즉시 표시, 데이터는 빠르게 로드
  const [post, setPost] = useState<Post | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isNotFound, setIsNotFound] = useState(false);
  const [pendingReactions, setPendingReactions] = useState<Set<string>>(new Set());
  const [userReactions, setUserReactions] = useState<{
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  }>({ liked: false, disliked: false, bookmarked: false });

  const handleCommentAdded = async () => {
    if (!slug) return;
    
    console.log('🔄 handleCommentAdded 호출됨 - 댓글 목록 새로고침 시작');
    
    try {
      // 🚀 2단계: 배치 조회로 댓글과 작성자 정보 함께 로드
      const response = await apiClient.getCommentsBatch(slug);
      console.log('🔍 getCommentsBatch 전체 응답:', {
        success: response.success,
        data: response.data,
        dataStructure: Object.keys(response.data || {}),
        hasComments: !!(response.data?.comments),
        hasPagination: !!(response.data?.pagination),
        firstComment: response.data?.comments?.[0],
        // 더 상세한 구조 분석
        dataDataComments: response.data?.data?.comments,
        firstDataComment: response.data?.data?.comments?.[0],
        firstCommentUserReaction: response.data?.data?.comments?.[0]?.user_reaction,
        allCommentFields: response.data?.data?.comments?.[0] ? Object.keys(response.data.data.comments[0]) : []
      });
      
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
        console.log('✅ 댓글 목록 업데이트 완료:', {
          commentCount: processedComments.length,
          firstCommentUserReaction: processedComments[0]?.user_reaction,
          hasUserReactions: processedComments.some(c => c.user_reaction)
        });
        setComments(processedComments);
        
        // 댓글 수 업데이트
        if (post) {
          const commentCount = processedComments.length;
          setPost(prev => prev ? {
            ...prev,
            stats: {
              view_count: prev.stats?.view_count || 0,
              like_count: prev.stats?.like_count || 0,
              dislike_count: prev.stats?.dislike_count || 0,
              bookmark_count: prev.stats?.bookmark_count || 0,
              comment_count: commentCount,
              ...prev.stats
            }
          } : prev);
        }
      }
    } catch (error) {
      console.error('댓글 로드 실패:', error);
    }
  };

  // 🚀 Optimistic UI: 즉시 UI 업데이트, API는 백그라운드 처리
  const handleReactionChange = useCallback(async (reactionType: 'like' | 'dislike' | 'bookmark') => {
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
    }
  }, [user, post, slug, pendingReactions, userReactions, showError]);

  // 작성자 권한 체크 함수
  const isAuthor = () => {
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
  };

  const handleEditPost = () => {
    navigate(`/property-information/${slug}/edit`);
  };

  const handleDeletePost = async () => {
    if (!confirm('정말로 삭제하시겠습니까?')) return;
    
    try {
      const response = await apiClient.deletePost(slug!);
      if (response.success) {
        showSuccess('정보가 삭제되었습니다');
        navigate('/info');
      } else {
        showError(response.error || '정보 삭제에 실패했습니다');
      }
    } catch (error) {
      showError('정보 삭제 중 오류가 발생했습니다');
    }
  };

  // ⚡ 페이지 마운트 후 즉시 데이터 로드 (Hybrid 방식)
  useEffect(() => {
    const loadData = async () => {
      if (!slug) return;
      
      setIsLoading(true);
      try {
        // 🚀 병렬 로딩: 정보와 댓글을 동시에 호출 (배치 조회 적용)
        const [postResult, commentsResult] = await Promise.all([
          apiClient.getPost(slug),
          apiClient.getCommentsBatch(slug)  // 🚀 2단계: 배치 조회 사용
        ]);
        
        // 정보 처리
        if (postResult.success && postResult.data) {
          const postData = postResult.data;
          
          // property_information 타입인지 확인
          if (postData.metadata?.type !== 'property_information') {
            setIsNotFound(true);
            showError('해당 정보를 찾을 수 없습니다');
            return;
          }
          
          setPost(postData);
          
          // 사용자 반응 상태 초기화 (로그인 사용자만)
          if (user && postData.user_reaction) {
            setUserReactions({
              liked: postData.user_reaction.liked || false,
              disliked: postData.user_reaction.disliked || false,
              bookmarked: postData.user_reaction.bookmarked || false
            });
          }
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
        <DetailPageLayout
          post={{} as Post}
          user={user}
          comments={[]}
          onReactionChange={handleReactionChange}
          onCommentAdded={handleCommentAdded}
          onEditPost={handleEditPost}
          onDeletePost={handleDeletePost}
          isLoading={true}
          pendingReactions={pendingReactions}
          userReactions={userReactions}
          postSlug={slug}
          pageType="property_information"
        />
      </AppLayout>
    );
  }

  if (isNotFound || !post) {
    return (
      <AppLayout user={user} onLogout={logout}>
        <DetailPageLayout
          post={null as any}
          user={user}
          comments={[]}
          onReactionChange={handleReactionChange}
          onCommentAdded={handleCommentAdded}
          onEditPost={handleEditPost}
          onDeletePost={handleDeletePost}
          isLoading={false}
          pendingReactions={pendingReactions}
          userReactions={userReactions}
          postSlug={slug}
          pageType="property_information"
        />
      </AppLayout>
    );
  }

  // 부동산 정보 특성에 맞는 커스텀 섹션 정의
  const getPropertyContentSections = () => {
    if (!post) return {};

    const sections: { beforeContent?: React.ReactNode[]; afterContent?: React.ReactNode[]; afterReactions?: React.ReactNode[] } = {};

    // 요약 섹션 (본문 이전)
    if (post.metadata?.summary) {
      sections.beforeContent = [
        <div key="summary" className="bg-blue-50 p-4 rounded-lg mb-6">
          <h3 className="font-semibold text-blue-800 mb-2">📋 요약</h3>
          <p className="text-blue-700">{post.metadata.summary}</p>
        </div>
      ];
    }

    // 콘텐츠 섹션 (본문 대신)
    sections.afterContent = [
      <div key="property-content" className="mb-6">
        <SafeHTMLRenderer
          content={post.content}
          contentType={post.metadata?.content_type || 'ai_article'}
          className="prose prose-lg max-w-none"
        />
      </div>
    ];

    // 출처 정보 (반응 버튼 이후)
    if (post.metadata?.data_source) {
      sections.afterReactions = [
        <div key="data-source" className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-2">📊 데이터 출처</h3>
          <p className="text-gray-600">{post.metadata.data_source}</p>
        </div>
      ];
    }

    return sections;
  };

  return (
    <AppLayout user={user} onLogout={logout}>
      <div className="max-w-4xl mx-auto">
        {/* 상단 네비게이션 */}
        <div className="flex items-center justify-between mb-6">
          <button 
            onClick={() => navigate('/info')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 목록으로
          </button>
        </div>

        <DetailPageLayout
        post={post}
        user={user}
        comments={comments}
        onReactionChange={handleReactionChange}
        onCommentAdded={handleCommentAdded}
        onEditPost={isAuthor() ? handleEditPost : undefined}
        onDeletePost={isAuthor() ? handleDeletePost : undefined}
        isLoading={isLoading}
        pendingReactions={pendingReactions}
        userReactions={userReactions}
        postSlug={slug}
        pageType="property_information"
        sections={getPropertyContentSections()}
      />
      </div>
    </AppLayout>
  );
}