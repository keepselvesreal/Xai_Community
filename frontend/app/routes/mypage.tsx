import { useState } from "react";
import { json, redirect, type LoaderFunction, type MetaFunction } from "@remix-run/node";
import { useLoaderData, Link } from "@remix-run/react";
import AppLayout from "~/components/layout/AppLayout";
import { useAuth } from "~/contexts/AuthContext";

export const meta: MetaFunction = () => {
  return [
    { title: "마이페이지 | XAI 아파트 커뮤니티" },
    { name: "description", content: "내 정보 및 활동 내역" },
  ];
};

export const loader: LoaderFunction = async ({ request }) => {
  // 실제 환경에서는 인증 확인
  // if (!user) return redirect("/auth/login");

  // Mock 사용자 활동 데이터
  const userStats = {
    postsCount: 2,
    commentsCount: 8,
    likesReceived: 15,
    joinDate: "2023-09-15",
    consecutiveDays: 3
  };

  const recentPosts = [
    {
      id: 1,
      title: "엘리베이터 점검 관련 문의",
      category: "문의",
      created_at: "2024-03-09",
      comments_count: 3,
      likes_count: 7
    },
    {
      id: 2,
      title: "주차 공간 효율적 이용 제안",
      category: "건의",
      created_at: "2024-03-07",
      comments_count: 8,
      likes_count: 15
    }
  ];

  const recentComments = [
    {
      id: 1,
      post_title: "층간소음 관련 건의사항",
      comment: "저희 집도 같은 문제가 있어서 공감됩니다. 좋은 해결책이 있으면 좋겠어요.",
      created_at: "2024-03-10"
    },
    {
      id: 2,
      post_title: "헬스장 이용 문의",
      comment: "관리사무소에 문의하시면 자세한 안내 받으실 수 있을 거예요.",
      created_at: "2024-03-09"
    }
  ];

  return json({ userStats, recentPosts, recentComments });
};

// ActivityItem 컴포넌트
interface ActivityItemProps {
  type: string;
  icon: string;
  name: string;
  count: number;
  onToggle: (type: string) => void;
  isExpanded: boolean;
}

function ActivityItem({ type, icon, name, count, onToggle, isExpanded }: ActivityItemProps) {
  const mockData: Record<string, any[]> = {
    'board-posts': [
      { title: '엘리베이터 소음 문제', author: '홍길동', date: '2024-03-10' },
    ],
    'board-comments': [
      { title: '층간소음 관련 건의사항', comment: '저희 집도 같은 문제가 있어서 공감됩니다.', date: '2024-03-10' },
    ],
    'info-posts': [
      { title: '헬스장 이용 안내', author: '관리사무소', date: '2024-03-09' },
    ],
    'info-comments': [
      { title: '주차장 이용 규칙', comment: '명확한 안내 감사드립니다.', date: '2024-03-08' },
    ],
    'service-inquiries': [
      { title: '클리닝 서비스 문의', category: '청소', date: '2024-03-09' },
    ],
    'service-reviews': [
      { title: '세탁소 이용 후기', rating: 4.5, comment: '서비스가 매우 만족스럽습니다.', date: '2024-03-08' },
    ],
    'tips-posts': [
      { title: '겨울철 화분 관리법', expert: '김정원', date: '2024-03-07' },
    ],
    'tips-comments': [
      { title: '전기세 절약하는 법', comment: '유용한 팁 감사합니다!', date: '2024-03-06' },
    ],
    // 반응 데이터
    'board-likes': [
      { title: '공동현관 보안 강화 건의', author: '김철수', date: '2024-03-10' },
    ],
    'board-dislikes': [
      { title: '잘못된 정보 게시글', author: '이영희', date: '2024-03-09' },
    ],
    'board-saves': [
      { title: '아파트 관리비 절약 팁', author: '박민수', date: '2024-03-08' },
    ],
    'info-likes': [
      { title: '재활용 분리수거 안내', author: '관리사무소', date: '2024-03-07' },
    ],
    'info-dislikes': [
      { title: '부정확한 정보 공지', author: '홍길동', date: '2024-03-06' },
    ],
    'info-saves': [
      { title: '응급상황 대처법', author: '안전관리팀', date: '2024-03-05' },
    ],
    'service-likes': [
      { title: 'ABC 마트 할인 이벤트', category: '마트', date: '2024-03-04' },
    ],
    'service-dislikes': [
      { title: '불친절한 서비스', category: '세탁소', date: '2024-03-03' },
    ],
    'service-saves': [
      { title: '좋은 청소 업체 추천', category: '청소', date: '2024-03-02' },
    ],
    'tips-likes': [
      { title: '베란다 정원 가꾸기', expert: '김정원', date: '2024-03-01' },
    ],
    'tips-dislikes': [
      { title: '효과 없는 팁', expert: '이전기', date: '2024-02-28' },
    ],
    'tips-saves': [
      { title: '에너지 절약 비법', expert: '박절약', date: '2024-02-27' },
    ]
  };

  const data = mockData[type] || [];

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
          {count}개
          <span className="text-xs" style={{color: 'var(--text-muted)'}}>{isExpanded ? '숨기기' : '보기'}</span>
        </span>
      </div>

      {isExpanded && (
        <div className="ml-4 mt-2 space-y-2">
          <div className="bg-white border border-var-light rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h5 className="font-semibold text-var-primary">{icon} {name}</h5>
              <span className="text-var-muted text-sm">{data.length}개</span>
            </div>
            <div className="space-y-3">
              {data.map((item, index) => (
                <div key={index} className="border-b border-var-light pb-3 last:border-b-0 last:pb-0">
                  <div className="font-medium text-var-primary text-sm mb-1">{item.title}</div>
                  <div className="text-var-muted text-xs space-x-2">
                    {item.author && <span>작성자: {item.author}</span>}
                    {item.expert && <span>전문가: {item.expert}</span>}
                    {item.category && <span>카테고리: {item.category}</span>}
                    {item.rating && <span>⭐ {item.rating}</span>}
                    <span>{item.date}</span>
                  </div>
                  {item.comment && <div className="text-var-secondary text-sm mt-2 italic">"{item.comment}"</div>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function MyPage() {
  const { userStats, recentPosts, recentComments } = useLoaderData<typeof loader>();
  const { user, logout } = useAuth();
  const [activityTab, setActivityTab] = useState<'write' | 'reaction'>('write');
  const [expandedActivities, setExpandedActivities] = useState<Set<string>>(new Set());

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

        {/* 내 활동 카드 */}
        <div className="card p-0 overflow-hidden">
          <div className="bg-gradient-to-r from-accent-primary to-accent-secondary p-6">
            <h3 className="font-bold text-xl text-white drop-shadow-sm">
              내 활동
            </h3>
          </div>

          <div className="p-8">
            {/* 요약 정보 */}
            <div className="grid grid-cols-2 gap-4 mb-8">
              <div className="text-center p-6 bg-var-section rounded-xl border border-var-light">
                <div className="text-3xl font-bold mb-2" style={{color: 'var(--accent-primary)'}}>{user ? userStats.postsCount : '0'}</div>
                <div className="text-sm font-medium" style={{color: 'var(--text-muted)'}}>총 작성 글</div>
              </div>
              <div className="text-center p-6 bg-var-section rounded-xl border border-var-light">
                <div className="text-3xl font-bold mb-2" style={{color: 'var(--accent-primary)'}}>{user ? userStats.commentsCount : '0'}</div>
                <div className="text-sm font-medium" style={{color: 'var(--text-muted)'}}>총 반응</div>
              </div>
              <div className="text-center p-6 bg-var-section rounded-xl border border-var-light">
                <div className="text-3xl font-bold mb-2" style={{color: 'var(--accent-primary)'}}>{user ? userStats.likesReceived : '0'}</div>
                <div className="text-sm font-medium" style={{color: 'var(--text-muted)'}}>받은 추천</div>
              </div>
              <div className="text-center p-6 bg-var-section rounded-xl border border-var-light">
                <div className="text-3xl font-bold mb-2" style={{color: 'var(--accent-primary)'}}>
                  {user ? `${userStats.consecutiveDays}일` : '0일'}
                </div>
                <div className="text-sm font-medium" style={{color: 'var(--text-muted)'}}>연속 활동</div>
              </div>
            </div>

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
              {activityTab === 'write' && (
                <>
                  {/* 게시판 활동 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      📝 게시판
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="board-posts" 
                        icon="📝" 
                        name="글" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('board-posts')}
                      />
                      <ActivityItem 
                        type="board-comments" 
                        icon="💬" 
                        name="댓글" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('board-comments')}
                      />
                    </div>
                  </div>

                  {/* 정보 활동 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      📋 정보
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="info-posts" 
                        icon="📝" 
                        name="글" 
                        count={user ? 0 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('info-posts')}
                      />
                      <ActivityItem 
                        type="info-comments" 
                        icon="💬" 
                        name="댓글" 
                        count={user ? 2 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('info-comments')}
                      />
                    </div>
                  </div>

                  {/* 입주 업체 서비스 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      🏢 입주 업체 서비스
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="service-inquiries" 
                        icon="❓" 
                        name="문의" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('service-inquiries')}
                      />
                      <ActivityItem 
                        type="service-reviews" 
                        icon="⭐" 
                        name="후기" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('service-reviews')}
                      />
                    </div>
                  </div>

                  {/* 전문가 꿀정보 활동 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      💡 전문가 꿀정보
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="tips-posts" 
                        icon="📝" 
                        name="글" 
                        count={user ? 0 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('tips-posts')}
                      />
                      <ActivityItem 
                        type="tips-comments" 
                        icon="💬" 
                        name="댓글" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('tips-comments')}
                      />
                    </div>
                  </div>
                </>
              )}

              {activityTab === 'reaction' && (
                <>
                  {/* 게시판 반응 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      📝 게시판
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="board-likes" 
                        icon="👍" 
                        name="추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('board-likes')}
                      />
                      <ActivityItem 
                        type="board-dislikes" 
                        icon="👎" 
                        name="비추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('board-dislikes')}
                      />
                      <ActivityItem 
                        type="board-saves" 
                        icon="📌" 
                        name="저장" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('board-saves')}
                      />
                    </div>
                  </div>

                  {/* 정보 반응 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      📋 정보
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="info-likes" 
                        icon="👍" 
                        name="추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('info-likes')}
                      />
                      <ActivityItem 
                        type="info-dislikes" 
                        icon="👎" 
                        name="비추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('info-dislikes')}
                      />
                      <ActivityItem 
                        type="info-saves" 
                        icon="📌" 
                        name="저장" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('info-saves')}
                      />
                    </div>
                  </div>

                  {/* 입주 업체 서비스 반응 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      🏢 입주 업체 서비스
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="service-likes" 
                        icon="👍" 
                        name="추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('service-likes')}
                      />
                      <ActivityItem 
                        type="service-dislikes" 
                        icon="👎" 
                        name="비추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('service-dislikes')}
                      />
                      <ActivityItem 
                        type="service-saves" 
                        icon="📌" 
                        name="저장" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('service-saves')}
                      />
                    </div>
                  </div>

                  {/* 전문가 꿀정보 반응 */}
                  <div>
                    <h4 className="font-semibold mb-3 flex items-center gap-2" style={{color: 'var(--accent-primary)'}}>
                      💡 전문가 꿀정보
                    </h4>
                    <div className="space-y-2">
                      <ActivityItem 
                        type="tips-likes" 
                        icon="👍" 
                        name="추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('tips-likes')}
                      />
                      <ActivityItem 
                        type="tips-dislikes" 
                        icon="👎" 
                        name="비추천" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('tips-dislikes')}
                      />
                      <ActivityItem 
                        type="tips-saves" 
                        icon="📌" 
                        name="저장" 
                        count={user ? 1 : 0} 
                        onToggle={toggleActivityDetail}
                        isExpanded={expandedActivities.has('tips-saves')}
                      />
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}