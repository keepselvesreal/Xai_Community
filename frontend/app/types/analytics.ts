// 분석 관련 타입 정의

// 기간 필터 타입
export type DateRangeFilter = 'all' | '3days' | '7days';

// GA4 분석 데이터 타입
export interface GA4Analytics {
  // 기본 지표
  totalUsers: number;
  newUsers: number;
  sessions: number;
  pageViews: number;
  bounceRate: number;
  avgSessionDuration: number;
  
  // 시간대별 데이터
  timelineData: {
    date: string;
    users: number;
    sessions: number;
    pageViews: number;
  }[];
  
  // 페이지별 성과
  topPages: {
    path: string;
    title: string;
    pageViews: number;
    uniqueViews: number;
    avgTimeOnPage: number;
    bounceRate: number;
  }[];
  
  // 사용자 세그먼트
  userSegments: {
    newVsReturning: {
      newUsers: number;
      returningUsers: number;
    };
    deviceTypes: {
      desktop: number;
      mobile: number;
      tablet: number;
    };
    trafficSources: {
      direct: number;
      organic: number;
      referral: number;
      social: number;
    };
  };
  
  // 커스텀 이벤트
  customEvents: {
    eventName: string;
    eventCount: number;
    uniqueUsers: number;
  }[];
}

// 커뮤니티 활동 분석 데이터 타입
export interface CommunityAnalytics {
  // 전체 통계
  totalStats: {
    totalPosts: number;
    totalComments: number;
    totalUsers: number;
    activeUsers: number; // 최근 활동한 사용자
  };
  
  // 게시글 분석
  postAnalytics: {
    // 카테고리별 게시글 수
    postsByCategory: {
      category: string;
      count: number;
      percentage: number;
    }[];
    
    // 시간대별 게시글 작성 패턴
    postsByTime: {
      hour: number;
      count: number;
    }[];
    
    // 요일별 게시글 작성 패턴
    postsByDayOfWeek: {
      dayOfWeek: string;
      count: number;
    }[];
    
    // 인기 게시글
    topPosts: {
      id: string;
      title: string;
      category: string;
      viewCount: number;
      likeCount: number;
      commentCount: number;
      createdAt: string;
    }[];
  };
  
  // 사용자 참여도 분석
  engagementAnalytics: {
    // 반응별 통계
    reactionStats: {
      totalLikes: number;
      totalDislikes: number;
      totalBookmarks: number;
    };
    
    // 댓글 활동
    commentStats: {
      totalComments: number;
      avgCommentsPerPost: number;
      topCommenters: {
        userId: string;
        userName: string;
        commentCount: number;
      }[];
    };
    
    // 사용자 활동 지속성
    userRetention: {
      dailyActiveUsers: number;
      weeklyActiveUsers: number;
      monthlyActiveUsers: number;
    };
  };
}

// 비즈니스 인사이트 데이터 타입
export interface BusinessInsights {
  // 서비스 성과
  servicePerformance: {
    totalServices: number;
    totalInquiries: number;
    totalReviews: number;
    avgRating: number;
    conversionRate: number; // 방문자 대비 문의율
  };
  
  // 페이지별 성과 비교
  pageTypePerformance: {
    pageType: string;
    displayName: string;
    totalPosts: number;
    totalViews: number;
    avgEngagement: number; // 평균 참여도 (댓글+좋아요)
    growthRate: number; // 성장률
  }[];
  
  // 사용자 여정 분석
  userJourney: {
    signupToFirstPost: number; // 가입 후 첫 게시글까지 평균 일수
    visitorToSignup: number; // 방문자 대비 가입률
    postEngagementRate: number; // 게시글 참여율
  };
  
  // 시간대별 트렌드
  trends: {
    period: string; // 'daily' | 'weekly' | 'monthly'
    data: {
      date: string;
      posts: number;
      comments: number;
      newUsers: number;
      activeUsers: number;
    }[];
  };
}

// 통합 분석 대시보드 데이터 타입
export interface AnalyticsDashboard {
  dateRange: DateRangeFilter;
  lastUpdated: string;
  ga4Analytics: GA4Analytics;
  communityAnalytics: CommunityAnalytics;
  businessInsights: BusinessInsights;
}

// API 응답 타입
export interface AnalyticsApiResponse {
  success: boolean;
  data: AnalyticsDashboard;
  message?: string;
}

// 차트 데이터 타입
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

// 지표 카드 타입
export interface MetricCard {
  title: string;
  value: number | string;
  change?: number; // 변화율 (퍼센트)
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: string;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  format?: 'number' | 'percentage' | 'currency' | 'duration';
}

// 로딩 상태 타입
export interface AnalyticsLoadingState {
  isLoading: boolean;
  error: string | null;
  lastFetch: string | null;
}