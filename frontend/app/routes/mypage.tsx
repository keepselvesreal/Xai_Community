import { useState, useEffect } from "react";
import { json, redirect, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";
import { apiClient } from "~/lib/api";
import { formatNumber } from "~/lib/utils";
import type { UserActivityResponse, ActivityItem } from "~/types";
import { UserInfoSkeleton } from "~/components/mypage/UserInfoSkeleton";
import { ActivitySectionSkeleton } from "~/components/mypage/ActivitySectionSkeleton";

export const meta: MetaFunction = () => {
  return [
    { title: "마이페이지 | XAI 아파트 커뮤니티" },
    { name: "description", content: "내 정보 및 활동 내역" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  // 서버 사이드에서는 기본값만 반환, 실제 데이터는 클라이언트에서 로드
  return json({
    userActivity: null
  });
};

// ActivityItem 컴포넌트
interface ActivityItemProps {
  type: string;
  icon: string;
  name: string;
  items: ActivityItem[];
  onToggle: (type: string) => void;
  isExpanded: boolean;
}

function ActivityItem({ type, icon, name, items, onToggle, isExpanded }: ActivityItemProps) {

  return (
    <>
      <div 
        className="flex justify-between items-center p-4 bg-var-section rounded-lg border border-var-light hover:border-accent-primary hover:bg-var-hover transition-all cursor-pointer"
        onClick={() => onToggle(type)}
      >
        <span className="font-medium text-sm flex items-center gap-2" style={{color: 'var(--text-primary)'}}>
          <span>{icon}</span>
          {name}
        </span>
        <span className="font-semibold text-sm flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
          {items.length}개
          <span className="text-xs" style={{color: 'var(--text-muted)'}}>{isExpanded ? '숨기기' : '보기'}</span>
        </span>
      </div>

      {isExpanded && (
        <div className="ml-4 mt-2 space-y-2">
          <div className="bg-white border border-var-light rounded-lg p-4">
            <div className="space-y-3">
              {items.map((item, index) => (
                <div key={item.id || index} className="border-b border-var-light pb-3 last:border-b-0 last:pb-0">
                  <Link 
                    to={item.route_path}
                    className="block hover:bg-var-hover p-2 rounded transition-colors"
                  >
                    {/* 반응 표시 */}
                    {item.target_type ? (
                      <>
                        <div className="font-medium text-var-primary text-sm mb-2">
                          {item.title || item.target_title || "게시글 정보 없음"}
                        </div>
                        
                        {/* 통계 정보 표시 - PostCard와 동일한 스타일 */}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{new Date(item.created_at).toLocaleDateString()}</span>
                          <span>·</span>
                          <span className="text-gray-500">
                            👁 {formatNumber(item.view_count || 0)}
                          </span>
                          <span className="text-gray-500">
                            👍 {formatNumber(item.like_count || 0)}
                          </span>
                          <span className="text-gray-500">
                            👎 {formatNumber(item.dislike_count || 0)}
                          </span>
                          <span className="text-gray-500">
                            💬 {formatNumber(item.comment_count || 0)}
                          </span>
                          <span>·</span>
                          <span className="text-gray-500">
                            {item.target_type === 'post' ? '게시글' : '댓글'}
                          </span>
                        </div>
                      </>
                    ) : (
                      /* 일반 게시글/댓글 표시 */
                      <>
                        <div className="font-medium text-var-primary text-sm mb-2">
                          {item.title || (item.content ? "댓글 대상 게시글 정보 없음" : "게시글 제목 없음")}
                        </div>
                        
                        {/* 통계 정보 표시 - PostCard와 동일한 스타일 */}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{new Date(item.created_at).toLocaleDateString()}</span>
                          <span>·</span>
                          <span className="text-gray-500">
                            👁 {formatNumber(item.view_count || 0)}
                          </span>
                          <span className="text-gray-500">
                            👍 {formatNumber(item.like_count || 0)}
                          </span>
                          <span className="text-gray-500">
                            👎 {formatNumber(item.dislike_count || 0)}
                          </span>
                          <span className="text-gray-500">
                            💬 {formatNumber(item.comment_count || 0)}
                          </span>
                          {item.subtype && (
                            <>
                              <span>·</span>
                              <span className="inline-block px-2 py-1 bg-accent-light text-accent-primary rounded text-xs">
                                {item.subtype === 'service_inquiry' ? '문의' : item.subtype === 'service_review' ? '후기' : item.subtype}
                              </span>
                            </>
                          )}
                        </div>
                      </>
                    )}
                  </Link>
                </div>
              ))}
              {items.length === 0 && (
                <div className="text-center text-var-muted py-4">
                  활동 기록이 없습니다
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function MyPage() {
  const loaderData = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const [activityTab, setActivityTab] = useState<'write' | 'reaction'>('write');
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());
  const [userActivity, setUserActivity] = useState<UserActivityResponse | null>(null);
  const [userStats, setUserStats] = useState({
    postsCount: 0,
    commentsCount: 0,
    likesReceived: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 댓글을 페이지 타입별로 분류하는 헬퍼 함수
  const getCommentsByPageType = (comments: ActivityItem[], pageType: string): ActivityItem[] => {
    if (!comments) return [];
    
    return comments.filter(comment => {
      if (!comment.route_path) return false;
      
      switch (pageType) {
        case 'board':
          return comment.route_path.startsWith('/board-post/') && !comment.subtype;
        case 'info':
          return comment.route_path.startsWith('/property-info/') && !comment.subtype;
        case 'services':
          return (comment.route_path.startsWith('/moving-services-post/') || 
                  comment.route_path.startsWith('/services/')) && !comment.subtype;
        case 'tips':
          return (comment.route_path.startsWith('/expert-tips/') || 
                  comment.route_path.startsWith('/expert-tip/') ||
                  comment.route_path.startsWith('/tips/')) && !comment.subtype;
        default:
          return false;
      }
    });
  };

  // 반응을 페이지 타입별로 분류하는 헬퍼 함수
  const getReactionsByPageType = (reactions: ActivityItem[], pageType: string): ActivityItem[] => {
    if (!reactions || !userActivity) return [];
    
    // 모든 페이지의 게시물 ID들을 수집
    const allPosts = [
      ...(userActivity.posts.board || []),
      ...(userActivity.posts.info || []),
      ...(userActivity.posts.services || []),
      ...(userActivity.posts.tips || [])
    ];
    
    // 해당 페이지 타입의 게시물 ID들만 추출
    const pageTypePosts = userActivity.posts[pageType] || [];
    const pageTypePostIds = new Set(pageTypePosts.map(post => post.id));
    
    // 반응 분류
    return reactions.filter(reaction => {
      if (!reaction.target_id) return false;
      
      if (reaction.target_type === 'post') {
        // 게시글에 대한 반응: target_id가 해당 페이지 타입의 게시글 ID와 일치하는지 확인
        return pageTypePostIds.has(reaction.target_id);
      } else if (reaction.target_type === 'comment') {
        // 댓글에 대한 반응: 댓글이 속한 게시글을 찾아야 함
        // 일단 route_path로 대략적으로 판단 (임시)
        if (reaction.route_path) {
          switch (pageType) {
            case 'board':
              return reaction.route_path.startsWith('/board-post/');
            case 'info':
              return reaction.route_path.startsWith('/property-info/');
            case 'services':
              return reaction.route_path.startsWith('/moving-services-post/') || 
                     reaction.route_path.startsWith('/services/');
            case 'tips':
              return reaction.route_path.startsWith('/expert-tips/') || 
                     reaction.route_path.startsWith('/expert-tip/') ||
                     reaction.route_path.startsWith('/tips/');
            default:
              return false;
          }
        }
        return false;
      }
      
      return false;
    });
  };

  // 사용자 활동 데이터 로드 함수
  const loadUserActivity = async () => {
    if (!user || !apiClient.isAuthenticated()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const activity = await apiClient.getUserActivity(1, 10); // 페이지네이션 파라미터 추가
      
      
      setUserActivity(activity);
      // 새로운 API 구조에서는 pagination 정보에서 총 개수만 사용
      if (activity.pagination) {
        setUserStats({
          postsCount: activity.pagination.posts.total_count,
          commentsCount: activity.pagination.comments.total_count,
          likesReceived: activity.pagination.reactions.total_count
        });
      }
    } catch (err) {
      console.error('Failed to load user activity:', err);
      setError('활동 기록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 초기 로드
  useEffect(() => {
    loadUserActivity();
  }, [user, loaderData.userStats]);

  // 페이지 포커스 시 자동 새로고침 제거 (수동 새로고침만 사용)

  // 게스트 사용자를 위한 기본 데이터
  const displayUser = user || {
    email: 'guest@example.com',
    username: 'Guest User'
  };

  // 헬퍼 함수들
  function toggleActivityDetail(activityType: string) {
    setExpandedActivities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(activityType)) {
        newSet.delete(activityType);
      } else {
        newSet.add(activityType);
      }
      return newSet;
    });
  }

  function handleChangeUserId() {
    if (!user) {
      alert('로그인이 필요한 기능입니다.');
      return;
    }
    const newUserId = window.prompt('새로운 아이디를 입력하세요:', user?.username || user?.email);
    if (newUserId && newUserId !== (user?.username || user?.email)) {
      if (window.confirm(`아이디를 '${newUserId}'로 변경하시겠습니까?`)) {
        alert('아이디가 성공적으로 변경되었습니다.');
      }
    }
  }

  function handleChangeEmail() {
    if (!user) {
      alert('로그인이 필요한 기능입니다.');
      return;
    }
    const newEmail = window.prompt('새로운 이메일을 입력하세요:', user?.email);
    if (newEmail && newEmail !== user?.email && newEmail.includes('@')) {
      if (window.confirm(`이메일을 '${newEmail}'로 변경하시겠습니까?\n인증 이메일이 발송됩니다.`)) {
        alert('인증 이메일이 발송되었습니다. 이메일을 확인해주세요.');
      }
    } else if (newEmail && !newEmail.includes('@')) {
      alert('올바른 이메일 형식을 입력해주세요.');
    }
  }

  function handleChangePassword() {
    if (!user) {
      alert('로그인이 필요한 기능입니다.');
      return;
    }
    const currentPassword = window.prompt('현재 비밀번호를 입력하세요:');
    if (currentPassword) {
      const newPassword = window.prompt('새로운 비밀번호를 입력하세요:');
      if (newPassword && newPassword.length >= 8) {
        const confirmPassword = window.prompt('새로운 비밀번호를 다시 입력하세요:');
        if (newPassword === confirmPassword) {
          alert('비밀번호가 성공적으로 변경되었습니다.');
        } else {
          alert('비밀번호가 일치하지 않습니다.');
        }
      } else {
        alert('비밀번호는 8자 이상이어야 합니다.');
      }
    }
  }

  function handleEditProfile() {
    if (!user) {
      alert('로그인이 필요한 기능입니다.');
      return;
    }
    alert('수정 페이지로 이동합니다.');
  }

  function handleShowLoginHistory() {
    alert('로그인 기록 페이지를 표시합니다.\n\n최근 로그인:\n• 2024-12-28 14:30 (현재 세션)\n• 2024-12-27 09:15\n• 2024-12-26 18:42');
  }

  function handleShow2FA() {
    if (window.confirm('2단계 인증을 설정하시겠습니까?\n보안이 더욱 강화됩니다.')) {
      alert('2단계 인증 설정 페이지로 이동합니다.');
    }
  }

  function handleShowPrivacySettings() {
    alert('개인정보 설정 페이지로 이동합니다.\n\n설정 가능한 항목:\n• 이름 공개 여부\n• 동/호수 공개 여부\n• 활동 기록 공개 여부');
  }

  return (
    <AppLayout 
      title={user ? "마이페이지" : "회원정보 (게스트 모드)"} 
      subtitle={user ? "내 정보 및 활동 내역" : "로그인하시면 개인 정보를 확인할 수 있습니다"}
      user={user}
      onLogout={logout}
    >
      {/* 로그인 안내 메시지 (게스트일 때만) */}
      {!user && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
          <div className="flex items-center gap-3">
            <div className="text-2xl">ℹ️</div>
            <div>
              <h3 className="font-semibold text-blue-800">게스트 모드입니다</h3>
              <p className="text-blue-600 text-sm mt-1">
                개인 정보 수정 및 활동 내역을 보려면 로그인해주세요.
              </p>
              <Link
                to="/auth/login"
                className="inline-block mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                로그인하기
              </Link>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 내 정보 카드 */}
        {isLoading ? (
          <UserInfoSkeleton />
        ) : (
          <div className="card p-0 overflow-hidden">
            <div className="bg-gradient-to-r from-accent-primary to-accent-secondary p-6">
              <h3 className="font-bold text-xl text-white drop-shadow-sm">
                내 정보
              </h3>
            </div>
            
            <div className="p-8 space-y-8">
            <div className="flex justify-between items-start py-4">
              <div className="flex-1">
                <div className="font-medium text-sm mb-2" style={{color: 'var(--text-secondary)'}}>아이디</div>
                <div className="font-semibold text-xl mb-2" style={{color: 'var(--text-primary)'}}>{displayUser.username || displayUser.email}</div>
                <div className="text-sm" style={{color: 'var(--text-muted)'}}>로그인에 사용되는 아이디</div>
              </div>
              <button 
                onClick={() => handleChangeUserId()}
                className={`px-4 py-2 border rounded-lg transition-colors text-sm whitespace-nowrap ${
                  user 
                    ? 'border-accent-primary text-accent-primary hover:bg-accent-primary hover:text-white'
                    : 'border-gray-300 text-gray-400 cursor-not-allowed'
                }`}
                disabled={!user}
              >
                변경
              </button>
            </div>

            <div className="flex justify-between items-start py-4">
              <div className="flex-1">
                <div className="font-medium text-sm mb-2" style={{color: 'var(--text-secondary)'}}>이메일</div>
                <div className="font-semibold text-xl mb-2" style={{color: 'var(--text-primary)'}}>{displayUser.email}</div>
                <div className="text-sm" style={{color: 'var(--text-muted)'}}>알림 및 계정 복구용 이메일</div>
              </div>
              <button 
                onClick={() => handleChangeEmail()}
                className={`px-4 py-2 border rounded-lg transition-colors text-sm whitespace-nowrap ${
                  user 
                    ? 'border-accent-primary text-accent-primary hover:bg-accent-primary hover:text-white'
                    : 'border-gray-300 text-gray-400 cursor-not-allowed'
                }`}
                disabled={!user}
              >
                변경
              </button>
            </div>

            <div className="flex justify-between items-start py-4">
              <div className="flex-1">
                <div className="font-medium text-sm mb-2" style={{color: 'var(--text-secondary)'}}>비밀번호</div>
                <div className="font-semibold text-xl mb-2" style={{color: 'var(--text-primary)'}}>{user ? '••••••••' : '로그인 필요'}</div>
                <div className="text-sm" style={{color: 'var(--text-muted)'}}>{user ? '마지막 변경: 2024년 10월 15일' : '로그인 후 확인 가능'}</div>
              </div>
              <button 
                onClick={() => handleChangePassword()}
                className={`px-4 py-2 border rounded-lg transition-colors text-sm whitespace-nowrap ${
                  user 
                    ? 'border-accent-primary text-accent-primary hover:bg-accent-primary hover:text-white'
                    : 'border-gray-300 text-gray-400 cursor-not-allowed'
                }`}
                disabled={!user}
              >
                변경
              </button>
            </div>

            <button 
              onClick={() => handleEditProfile()}
              className={`w-full py-4 rounded-xl font-semibold transition-all text-lg ${
                user 
                  ? 'bg-accent-primary text-white hover:bg-accent-hover'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
              disabled={!user}
            >
              {user ? '수정' : '로그인 필요'}
            </button>

            {/* 보안 설정 링크 */}
            <div className="flex justify-center gap-6 pt-6 border-t border-var-light">
              <button 
                onClick={() => handleShowLoginHistory()}
                className="text-var-muted hover:text-accent-primary transition-colors text-sm"
              >
                로그인 기록
              </button>
              <button 
                onClick={() => handleShow2FA()}
                className="text-var-muted hover:text-accent-primary transition-colors text-sm"
              >
                2단계 인증
              </button>
              <button 
                onClick={() => handleShowPrivacySettings()}
                className="text-var-muted hover:text-accent-primary transition-colors text-sm"
              >
                개인정보 설정
              </button>
            </div>
          </div>
          </div>
        )}

        {/* 내 활동 카드 */}
        {isLoading ? (
          <ActivitySectionSkeleton />
        ) : (
          <div className="card p-0 overflow-hidden">
            <div className="bg-gradient-to-r from-accent-primary to-accent-secondary p-6">
              <h3 className="font-bold text-xl text-white drop-shadow-sm">
                내 활동
              </h3>
            </div>

            <div className="p-8">

            {/* 탭 네비게이션 */}
            <div className="flex gap-4 mb-8">
              <button
                onClick={() => setActivityTab('write')}
                className={`flex-1 px-6 py-3 rounded-xl font-medium transition-colors text-sm ${
                  activityTab === 'write'
                    ? 'bg-accent-primary text-white'
                    : 'bg-var-section text-var-secondary hover:bg-var-hover'
                }`}
              >
                <span className="mr-2">✏️</span>
                작성
              </button>
              <button
                onClick={() => setActivityTab('reaction')}
                className={`flex-1 px-6 py-3 rounded-xl font-medium transition-colors text-sm ${
                  activityTab === 'reaction'
                    ? 'bg-accent-primary text-white'
                    : 'bg-var-section text-var-secondary hover:bg-var-hover'
                }`}
              >
                <span className="mr-2">👍</span>
                반응
              </button>
            </div>

            {/* 활동 내용 */}
            <div className="space-y-6">
              {error && (
                <div className="text-center py-8">
                  <div className="text-red-500">{error}</div>
                </div>
              )}

              {!isLoading && !error && activityTab === 'write' && (
                <>
                  {/* 게시판 활동 */}
                  {userActivity && (
                    (userActivity.posts.board?.length > 0 || getCommentsByPageType(userActivity.comments, 'board').length > 0)
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        📝 게시판
                      </h4>
                      <div className="space-y-2">
                        {userActivity?.posts.board?.length > 0 && (
                          <ActivityItem 
                            type="board-posts" 
                            icon="📝" 
                            name="글" 
                            items={userActivity.posts.board}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('board-posts')}
                          />
                        )}
                        {getCommentsByPageType(userActivity?.comments || [], 'board').length > 0 && (
                          <ActivityItem 
                            type="board-comments" 
                            icon="💬" 
                            name="댓글" 
                            items={getCommentsByPageType(userActivity.comments, 'board')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('board-comments')}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* 정보 활동 */}
                  {userActivity && (
                    (userActivity.posts.info?.length > 0 || getCommentsByPageType(userActivity.comments, 'info').length > 0)
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        📋 정보
                      </h4>
                      <div className="space-y-2">
                        {userActivity?.posts.info?.length > 0 && (
                          <ActivityItem 
                            type="info-posts" 
                            icon="📝" 
                            name="글" 
                            items={userActivity.posts.info}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('info-posts')}
                          />
                        )}
                        {getCommentsByPageType(userActivity?.comments || [], 'info').length > 0 && (
                          <ActivityItem 
                            type="info-comments" 
                            icon="💬" 
                            name="댓글" 
                            items={getCommentsByPageType(userActivity.comments, 'info')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('info-comments')}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* 입주 업체 서비스 */}
                  {userActivity && (
                    (userActivity.posts.services?.length > 0 || 
                     getCommentsByPageType(userActivity.comments, 'services').length > 0 ||
                     userActivity.comments.filter(c => c.subtype === 'service_inquiry').length > 0 ||
                     userActivity.comments.filter(c => c.subtype === 'service_review').length > 0)
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        🏢 입주 업체 서비스
                      </h4>
                      <div className="space-y-2">
                        {userActivity?.posts.services?.length > 0 && (
                          <ActivityItem 
                            type="service-posts" 
                            icon="📝" 
                            name="글" 
                            items={userActivity.posts.services}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('service-posts')}
                          />
                        )}
                        {getCommentsByPageType(userActivity?.comments || [], 'services').length > 0 && (
                          <ActivityItem 
                            type="service-comments" 
                            icon="💬" 
                            name="댓글" 
                            items={getCommentsByPageType(userActivity.comments, 'services')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('service-comments')}
                          />
                        )}
                        {userActivity?.comments.filter(c => c.subtype === 'service_inquiry').length > 0 && (
                          <ActivityItem 
                            type="service-inquiries" 
                            icon="❓" 
                            name="문의" 
                            items={userActivity.comments.filter(c => c.subtype === 'service_inquiry')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('service-inquiries')}
                          />
                        )}
                        {userActivity?.comments.filter(c => c.subtype === 'service_review').length > 0 && (
                          <ActivityItem 
                            type="service-reviews" 
                            icon="⭐" 
                            name="후기" 
                            items={userActivity.comments.filter(c => c.subtype === 'service_review')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('service-reviews')}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* 전문가 꿀정보 활동 */}
                  {userActivity && (
                    (userActivity.posts.tips?.length > 0 || getCommentsByPageType(userActivity.comments, 'tips').length > 0)
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        💡 전문가 꿀정보
                      </h4>
                      <div className="space-y-2">
                        {userActivity?.posts.tips?.length > 0 && (
                          <ActivityItem 
                            type="tips-posts" 
                            icon="📝" 
                            name="글" 
                            items={userActivity.posts.tips}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('tips-posts')}
                          />
                        )}
                        {getCommentsByPageType(userActivity?.comments || [], 'tips').length > 0 && (
                          <ActivityItem 
                            type="tips-comments" 
                            icon="💬" 
                            name="댓글" 
                            items={getCommentsByPageType(userActivity.comments, 'tips')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('tips-comments')}
                          />
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {!isLoading && !error && activityTab === 'reaction' && (
                <>
                  {/* 게시판 반응 */}
                  {userActivity && (
                    getReactionsByPageType(userActivity.reactions.likes || [], 'board').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.dislikes || [], 'board').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.bookmarks || [], 'board').length > 0
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        📝 게시판
                      </h4>
                      <div className="space-y-2">
                        {getReactionsByPageType(userActivity?.reactions.likes || [], 'board').length > 0 && (
                          <ActivityItem 
                            type="board-likes" 
                            icon="👍" 
                            name="추천" 
                            items={getReactionsByPageType(userActivity.reactions.likes, 'board')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('board-likes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.dislikes || [], 'board').length > 0 && (
                          <ActivityItem 
                            type="board-dislikes" 
                            icon="👎" 
                            name="비추천" 
                            items={getReactionsByPageType(userActivity.reactions.dislikes, 'board')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('board-dislikes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.bookmarks || [], 'board').length > 0 && (
                          <ActivityItem 
                            type="board-bookmarks" 
                            icon="📌" 
                            name="저장" 
                            items={getReactionsByPageType(userActivity.reactions.bookmarks, 'board')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('board-bookmarks')}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* 정보 반응 */}
                  {userActivity && (
                    getReactionsByPageType(userActivity.reactions.likes || [], 'info').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.dislikes || [], 'info').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.bookmarks || [], 'info').length > 0
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        📋 정보
                      </h4>
                      <div className="space-y-2">
                        {getReactionsByPageType(userActivity?.reactions.likes || [], 'info').length > 0 && (
                          <ActivityItem 
                            type="info-likes" 
                            icon="👍" 
                            name="추천" 
                            items={getReactionsByPageType(userActivity.reactions.likes, 'info')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('info-likes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.dislikes || [], 'info').length > 0 && (
                          <ActivityItem 
                            type="info-dislikes" 
                            icon="👎" 
                            name="비추천" 
                            items={getReactionsByPageType(userActivity.reactions.dislikes, 'info')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('info-dislikes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.bookmarks || [], 'info').length > 0 && (
                          <ActivityItem 
                            type="info-bookmarks" 
                            icon="📌" 
                            name="저장" 
                            items={getReactionsByPageType(userActivity.reactions.bookmarks, 'info')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('info-bookmarks')}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* 입주 업체 서비스 반응 */}
                  {userActivity && (
                    getReactionsByPageType(userActivity.reactions.likes || [], 'services').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.dislikes || [], 'services').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.bookmarks || [], 'services').length > 0
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        🏢 입주 업체 서비스
                      </h4>
                      <div className="space-y-2">
                        {getReactionsByPageType(userActivity?.reactions.likes || [], 'services').length > 0 && (
                          <ActivityItem 
                            type="services-likes" 
                            icon="👍" 
                            name="추천" 
                            items={getReactionsByPageType(userActivity.reactions.likes, 'services')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('services-likes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.dislikes || [], 'services').length > 0 && (
                          <ActivityItem 
                            type="services-dislikes" 
                            icon="👎" 
                            name="비추천" 
                            items={getReactionsByPageType(userActivity.reactions.dislikes, 'services')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('services-dislikes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.bookmarks || [], 'services').length > 0 && (
                          <ActivityItem 
                            type="services-bookmarks" 
                            icon="📌" 
                            name="저장" 
                            items={getReactionsByPageType(userActivity.reactions.bookmarks, 'services')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('services-bookmarks')}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* 전문가 꿀정보 반응 */}
                  {userActivity && (
                    getReactionsByPageType(userActivity.reactions.likes || [], 'tips').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.dislikes || [], 'tips').length > 0 ||
                    getReactionsByPageType(userActivity.reactions.bookmarks || [], 'tips').length > 0
                  ) && (
                    <div>
                      <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                        💡 전문가 꿀정보
                      </h4>
                      <div className="space-y-2">
                        {getReactionsByPageType(userActivity?.reactions.likes || [], 'tips').length > 0 && (
                          <ActivityItem 
                            type="tips-likes" 
                            icon="👍" 
                            name="추천" 
                            items={getReactionsByPageType(userActivity.reactions.likes, 'tips')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('tips-likes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.dislikes || [], 'tips').length > 0 && (
                          <ActivityItem 
                            type="tips-dislikes" 
                            icon="👎" 
                            name="비추천" 
                            items={getReactionsByPageType(userActivity.reactions.dislikes, 'tips')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('tips-dislikes')}
                          />
                        )}
                        {getReactionsByPageType(userActivity?.reactions.bookmarks || [], 'tips').length > 0 && (
                          <ActivityItem 
                            type="tips-bookmarks" 
                            icon="📌" 
                            name="저장" 
                            items={getReactionsByPageType(userActivity.reactions.bookmarks, 'tips')}
                            onToggle={toggleActivityDetail}
                            isExpanded={expandedActivities.has('tips-bookmarks')}
                          />
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}