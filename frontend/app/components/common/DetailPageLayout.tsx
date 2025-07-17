import React from 'react';
import CommentSection from '~/components/comment/CommentSection';
import type { Post, User, Comment } from '~/types';

interface DetailPageLayoutProps {
  post: Post;
  user?: User;
  comments: Comment[];
  onReactionChange: (type: 'like' | 'dislike' | 'bookmark') => void;
  onCommentAdded: () => void;
  onEditPost?: () => void;
  onDeletePost?: () => void;
  isLoading?: boolean;
  pendingReactions?: Set<string>;
  userReactions?: {
    liked: boolean;
    disliked: boolean;
    bookmarked: boolean;
  };
  sections?: {
    beforeContent?: React.ReactNode[];
    afterContent?: React.ReactNode[];
    afterTags?: React.ReactNode[];
    afterReactions?: React.ReactNode[];
  };
  // 댓글 시스템 관련 props
  postSlug?: string;
  pageType?: 'board' | 'property_information' | 'expert_tips' | 'moving_services';
  subtype?: 'inquiry' | 'review' | 'service_inquiry' | 'service_review';
}

const DetailPageLayout: React.FC<DetailPageLayoutProps> = ({
  post,
  user,
  comments,
  onReactionChange,
  onCommentAdded,
  onEditPost,
  onDeletePost,
  isLoading = false,
  pendingReactions = new Set(),
  userReactions = { liked: false, disliked: false, bookmarked: false },
  sections = {},
  postSlug,
  pageType = 'board',
  subtype,
}) => {
  // 로딩 상태 처리
  if (isLoading) {
    return (
      <div data-testid="loading-skeleton" className="max-w-4xl mx-auto space-y-6">
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
      </div>
    );
  }

  // 포스트 데이터 없을 때 처리
  if (!post) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          게시글을 찾을 수 없습니다
        </h2>
        <p className="text-gray-600">
          요청하신 게시글이 존재하지 않거나 삭제되었습니다.
        </p>
      </div>
    );
  }

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Seoul',
    });
  };

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

  // 카테고리별 색상 가져오기
  const getCategoryColor = (category: string) => {
    switch (category) {
      case '입주 정보':
      case '입주정보':
      case 'info': 
        return 'bg-green-100 text-green-800';
      case '생활 정보':
      case '생활정보':
      case 'life': 
        return 'bg-orange-100 text-orange-800';
      case '이야기':
      case 'story': 
        return 'bg-purple-100 text-purple-800';
      default: 
        return 'bg-blue-100 text-blue-800';
    }
  };

  // 반응 버튼 클릭 핸들러
  const handleReactionClick = (type: 'like' | 'dislike' | 'bookmark') => {
    if (!pendingReactions.has(type)) {
      onReactionChange(type);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 메인 컨테이너 - 프로토타입 스타일 적용 */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {/* 헤더 섹션 */}
        <div className="p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4 leading-tight">
            {post.title}
          </h1>
          
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(post.metadata?.category || post.metadata?.type || '일반')}`}>
                {post.metadata?.category || post.metadata?.type || '일반'}
              </span>
              {pageType === 'expert_tips' && (
                <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs font-medium">
                  전문가
                </span>
              )}
              <span>✍️</span>
              <span>
                {post.author?.display_name || post.author?.user_handle || '익명'}
              </span>
              <span>⏰</span>
              <span>{formatDate(post.created_at)}</span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1 text-sm text-gray-600">
                <span>👁️</span>
                <span>{post.stats?.view_count || 0}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-600">
                <span>관심</span>
                <span>{post.stats?.bookmark_count || 0}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-600">
                <span>문의</span>
                <span>{post.stats?.comment_count || 0}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-gray-600">
                <span>후기</span>
                <span>{post.stats?.review_count || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* 구분선 - 프로토타입과 동일 */}
        <div className="h-px bg-gray-200"></div>

        {/* 본문 섹션 */}
        <div className="p-6">
          {/* 작성자 컨트롤 */}
          {isAuthor() && (
            <div className="flex items-center justify-center gap-2 mb-4 pb-4 border-b border-gray-100">
              <button
                onClick={onEditPost}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 transform hover:-translate-y-0.5 hover:shadow-md"
              >
                <span>수정</span>
              </button>
              <button
                onClick={onDeletePost}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 transform hover:-translate-y-0.5 hover:shadow-md"
              >
                <span>삭제</span>
              </button>
            </div>
          )}

          {/* 본문 이전 커스텀 섹션 */}
          {sections.beforeContent?.map((section, index) => (
            <div key={`before-content-${index}`} className="mb-6">
              {section}
            </div>
          ))}

          {/* 본문 텍스트 - 서비스 페이지와 전문가 꿀정보 페이지에서는 숨김 */}
          {pageType !== 'moving_services' && pageType !== 'expert_tips' && (
            <div className="text-base leading-relaxed text-gray-700 mb-6 whitespace-pre-wrap">
              {post.content}
            </div>
          )}

          {/* 본문 이후 커스텀 섹션 */}
          {sections.afterContent?.map((section, index) => (
            <div key={`after-content-${index}`} className="mb-6">
              {section}
            </div>
          ))}

          {/* 태그 이후 커스텀 섹션 */}
          {sections.afterTags?.map((section, index) => (
            <div key={`after-tags-${index}`} className="mb-6">
              {section}
            </div>
          ))}

          {/* 반응 이후 커스텀 섹션 */}
          {sections.afterReactions?.map((section, index) => (
            <div key={`after-reactions-${index}`} className="mt-6">
              {section}
            </div>
          ))}
        </div>
      </div>

      {/* 댓글 섹션 - CommentSection 컴포넌트 사용 */}
      {postSlug && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <CommentSection
            postSlug={postSlug}
            comments={comments}
            onCommentAdded={onCommentAdded}
            pageType={pageType}
            subtype={subtype}
          />
        </div>
      )}
    </div>
  );
};

export default DetailPageLayout;