import { AnalyticsService } from './analytics-service';
import { apiClient } from './api';
import type { 
  AnalyticsDashboard, 
  DateRangeFilter, 
  GA4Analytics, 
  CommunityAnalytics, 
  BusinessInsights 
} from '~/types/analytics';

export class AnalyticsDashboardService {
  private analyticsService: AnalyticsService;

  constructor() {
    this.analyticsService = new AnalyticsService();
  }

  /**
   * 통합 분석 데이터 조회
   */
  async getDashboardData(dateRange: DateRangeFilter = '7days'): Promise<AnalyticsDashboard> {
    try {
      // 병렬로 데이터 조회
      const [ga4Data, communityData, businessData] = await Promise.all([
        this.getGA4Analytics(dateRange),
        this.getCommunityAnalytics(dateRange),
        this.getBusinessInsights(dateRange)
      ]);

      return {
        dateRange,
        lastUpdated: new Date().toISOString(),
        ga4Analytics: ga4Data,
        communityAnalytics: communityData,
        businessInsights: businessData
      };
    } catch (error) {
      console.error('분석 데이터 조회 오류:', error);
      throw new Error('분석 데이터를 불러오는데 실패했습니다.');
    }
  }

  /**
   * GA4 분석 데이터 조회 (시뮬레이션)
   * 실제 환경에서는 GA4 Reporting API를 사용
   */
  private async getGA4Analytics(dateRange: DateRangeFilter): Promise<GA4Analytics> {
    // GA4가 연결되어 있으면 실제 데이터 시도, 아니면 목업 데이터
    const isConnected = this.analyticsService.isConnected();
    
    if (isConnected) {
      // GA4 연결 상태 확인을 위한 테스트 이벤트 전송
      this.analyticsService.trackEvent('analytics_dashboard_view', {
        date_range: dateRange,
        timestamp: new Date().toISOString()
      });
    }

    // 현재는 목업 데이터 반환 (GA4 Reporting API 구현 전까지)
    return this.getMockGA4Data(dateRange);
  }

  /**
   * 커뮤니티 활동 분석 데이터 조회
   */
  private async getCommunityAnalytics(dateRange: DateRangeFilter): Promise<CommunityAnalytics> {
    try {
      // 백엔드 API를 통해 실제 데이터 조회 시도
      const response = await apiClient.request('GET', '/analytics/community', {
        params: { date_range: dateRange }
      });

      if (response.success && response.data) {
        return response.data;
      }
    } catch (error) {
      console.warn('커뮤니티 분석 API 오류, 목업 데이터 사용:', error);
    }

    // API가 없거나 실패하면 목업 데이터 반환
    return this.getMockCommunityData(dateRange);
  }

  /**
   * 비즈니스 인사이트 데이터 조회
   */
  private async getBusinessInsights(dateRange: DateRangeFilter): Promise<BusinessInsights> {
    try {
      // 백엔드 API를 통해 실제 데이터 조회 시도
      const response = await apiClient.request('GET', '/analytics/business', {
        params: { date_range: dateRange }
      });

      if (response.success && response.data) {
        return response.data;
      }
    } catch (error) {
      console.warn('비즈니스 인사이트 API 오류, 목업 데이터 사용:', error);
    }

    // API가 없거나 실패하면 목업 데이터 반환
    return this.getMockBusinessData(dateRange);
  }

  /**
   * 날짜 범위에 따른 일수 계산
   */
  private getDaysFromRange(dateRange: DateRangeFilter): number {
    switch (dateRange) {
      case '3days': return 3;
      case '7days': return 7;
      case 'all': return 30; // 전체는 최근 30일로 제한
      default: return 7;
    }
  }

  /**
   * 목업 GA4 데이터 생성
   */
  private getMockGA4Data(dateRange: DateRangeFilter): GA4Analytics {
    const days = this.getDaysFromRange(dateRange);
    const baseMultiplier = dateRange === 'all' ? 1 : dateRange === '7days' ? 0.7 : 0.3;

    // 시간대별 데이터 생성
    const timelineData = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - 1 - i));
      
      return {
        date: date.toISOString().split('T')[0],
        users: Math.floor((50 + Math.random() * 200) * baseMultiplier),
        sessions: Math.floor((60 + Math.random() * 300) * baseMultiplier),
        pageViews: Math.floor((150 + Math.random() * 500) * baseMultiplier)
      };
    });

    const totalUsers = timelineData.reduce((sum, data) => sum + data.users, 0);
    const totalSessions = timelineData.reduce((sum, data) => sum + data.sessions, 0);
    const totalPageViews = timelineData.reduce((sum, data) => sum + data.pageViews, 0);

    return {
      totalUsers,
      newUsers: Math.floor(totalUsers * 0.6),
      sessions: totalSessions,
      pageViews: totalPageViews,
      bounceRate: 35 + Math.random() * 20, // 35-55%
      avgSessionDuration: 120 + Math.random() * 180, // 2-5분

      timelineData,

      topPages: [
        {
          path: '/board',
          title: '게시판',
          pageViews: Math.floor(totalPageViews * 0.25),
          uniqueViews: Math.floor(totalPageViews * 0.2),
          avgTimeOnPage: 180,
          bounceRate: 25
        },
        {
          path: '/services',
          title: '입주 업체 서비스',
          pageViews: Math.floor(totalPageViews * 0.2),
          uniqueViews: Math.floor(totalPageViews * 0.18),
          avgTimeOnPage: 240,
          bounceRate: 30
        },
        {
          path: '/info',
          title: '부동산 정보',
          pageViews: Math.floor(totalPageViews * 0.18),
          uniqueViews: Math.floor(totalPageViews * 0.15),
          avgTimeOnPage: 200,
          bounceRate: 35
        },
        {
          path: '/tips',
          title: '전문가 꿀정보',
          pageViews: Math.floor(totalPageViews * 0.15),
          uniqueViews: Math.floor(totalPageViews * 0.12),
          avgTimeOnPage: 300,
          bounceRate: 20
        }
      ],

      userSegments: {
        newVsReturning: {
          newUsers: Math.floor(totalUsers * 0.6),
          returningUsers: Math.floor(totalUsers * 0.4)
        },
        deviceTypes: {
          desktop: Math.floor(totalUsers * 0.4),
          mobile: Math.floor(totalUsers * 0.55),
          tablet: Math.floor(totalUsers * 0.05)
        },
        trafficSources: {
          direct: Math.floor(totalUsers * 0.45),
          organic: Math.floor(totalUsers * 0.3),
          referral: Math.floor(totalUsers * 0.15),
          social: Math.floor(totalUsers * 0.1)
        }
      },

      customEvents: [
        {
          eventName: 'post_create',
          eventCount: Math.floor(20 * baseMultiplier),
          uniqueUsers: Math.floor(15 * baseMultiplier)
        },
        {
          eventName: 'post_like',
          eventCount: Math.floor(150 * baseMultiplier),
          uniqueUsers: Math.floor(80 * baseMultiplier)
        },
        {
          eventName: 'comment_create',
          eventCount: Math.floor(100 * baseMultiplier),
          uniqueUsers: Math.floor(50 * baseMultiplier)
        },
        {
          eventName: 'service_inquiry',
          eventCount: Math.floor(25 * baseMultiplier),
          uniqueUsers: Math.floor(20 * baseMultiplier)
        }
      ]
    };
  }

  /**
   * 목업 커뮤니티 데이터 생성
   */
  private getMockCommunityData(dateRange: DateRangeFilter): CommunityAnalytics {
    const baseMultiplier = dateRange === 'all' ? 1 : dateRange === '7days' ? 0.7 : 0.3;

    return {
      totalStats: {
        totalPosts: Math.floor(450 * baseMultiplier),
        totalComments: Math.floor(1200 * baseMultiplier),
        totalUsers: Math.floor(350 * baseMultiplier),
        activeUsers: Math.floor(120 * baseMultiplier)
      },

      postAnalytics: {
        postsByCategory: [
          { category: 'board', count: Math.floor(150 * baseMultiplier), percentage: 33 },
          { category: 'property_information', count: Math.floor(120 * baseMultiplier), percentage: 27 },
          { category: 'moving_services', count: Math.floor(100 * baseMultiplier), percentage: 22 },
          { category: 'expert_tips', count: Math.floor(80 * baseMultiplier), percentage: 18 }
        ],

        postsByTime: Array.from({ length: 24 }, (_, hour) => ({
          hour,
          count: Math.floor((5 + Math.random() * 15) * baseMultiplier)
        })),

        postsByDayOfWeek: [
          { dayOfWeek: '월', count: Math.floor(45 * baseMultiplier) },
          { dayOfWeek: '화', count: Math.floor(55 * baseMultiplier) },
          { dayOfWeek: '수', count: Math.floor(70 * baseMultiplier) },
          { dayOfWeek: '목', count: Math.floor(65 * baseMultiplier) },
          { dayOfWeek: '금', count: Math.floor(60 * baseMultiplier) },
          { dayOfWeek: '토', count: Math.floor(80 * baseMultiplier) },
          { dayOfWeek: '일', count: Math.floor(75 * baseMultiplier) }
        ],

        topPosts: [
          {
            id: '1',
            title: '새로 이사온 주민입니다. 인사드려요!',
            category: 'board',
            viewCount: 245,
            likeCount: 18,
            commentCount: 12,
            createdAt: new Date(Date.now() - 86400000).toISOString()
          },
          {
            id: '2',
            title: '아파트 관리비 절약 꿀팁 공유',
            category: 'expert_tips',
            viewCount: 189,
            likeCount: 25,
            commentCount: 8,
            createdAt: new Date(Date.now() - 172800000).toISOString()
          }
        ]
      },

      engagementAnalytics: {
        reactionStats: {
          totalLikes: Math.floor(850 * baseMultiplier),
          totalDislikes: Math.floor(45 * baseMultiplier),
          totalBookmarks: Math.floor(120 * baseMultiplier)
        },

        commentStats: {
          totalComments: Math.floor(1200 * baseMultiplier),
          avgCommentsPerPost: 2.7,
          topCommenters: [
            { userId: 'user1', userName: '아파트주민A', commentCount: Math.floor(45 * baseMultiplier) },
            { userId: 'user2', userName: '이웃사촌B', commentCount: Math.floor(38 * baseMultiplier) },
            { userId: 'user3', userName: '관리사무소', commentCount: Math.floor(32 * baseMultiplier) }
          ]
        },

        userRetention: {
          dailyActiveUsers: Math.floor(45 * baseMultiplier),
          weeklyActiveUsers: Math.floor(120 * baseMultiplier),
          monthlyActiveUsers: Math.floor(350 * baseMultiplier)
        }
      }
    };
  }

  /**
   * 목업 비즈니스 인사이트 데이터 생성
   */
  private getMockBusinessData(dateRange: DateRangeFilter): BusinessInsights {
    const days = this.getDaysFromRange(dateRange);
    const baseMultiplier = dateRange === 'all' ? 1 : dateRange === '7days' ? 0.7 : 0.3;

    // 시간대별 트렌드 데이터
    const trendData = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - 1 - i));
      
      return {
        date: date.toISOString().split('T')[0],
        posts: Math.floor((3 + Math.random() * 12) * baseMultiplier),
        comments: Math.floor((8 + Math.random() * 25) * baseMultiplier),
        newUsers: Math.floor((2 + Math.random() * 8) * baseMultiplier),
        activeUsers: Math.floor((15 + Math.random() * 35) * baseMultiplier)
      };
    });

    return {
      servicePerformance: {
        totalServices: Math.floor(45 * baseMultiplier),
        totalInquiries: Math.floor(180 * baseMultiplier),
        totalReviews: Math.floor(95 * baseMultiplier),
        avgRating: 4.2,
        conversionRate: 12.5
      },

      pageTypePerformance: [
        {
          pageType: 'board',
          displayName: '게시판',
          totalPosts: Math.floor(150 * baseMultiplier),
          totalViews: Math.floor(8500 * baseMultiplier),
          avgEngagement: 3.2,
          growthRate: 15.5
        },
        {
          pageType: 'moving_services',
          displayName: '입주 업체 서비스',
          totalPosts: Math.floor(100 * baseMultiplier),
          totalViews: Math.floor(6200 * baseMultiplier),
          avgEngagement: 4.8,
          growthRate: 28.3
        },
        {
          pageType: 'property_information',
          displayName: '부동산 정보',
          totalPosts: Math.floor(120 * baseMultiplier),
          totalViews: Math.floor(7100 * baseMultiplier),
          avgEngagement: 2.9,
          growthRate: 8.7
        },
        {
          pageType: 'expert_tips',
          displayName: '전문가 꿀정보',
          totalPosts: Math.floor(80 * baseMultiplier),
          totalViews: Math.floor(5800 * baseMultiplier),
          avgEngagement: 5.4,
          growthRate: 22.1
        }
      ],

      userJourney: {
        signupToFirstPost: 3.2,
        visitorToSignup: 8.5,
        postEngagementRate: 42.3
      },

      trends: {
        period: 'daily',
        data: trendData
      }
    };
  }

  /**
   * 특정 기간의 인기 게시글 조회
   */
  async getTopPosts(dateRange: DateRangeFilter, limit: number = 10) {
    try {
      const response = await apiClient.request('GET', '/analytics/top-posts', {
        params: { date_range: dateRange, limit }
      });

      if (response.success && response.data) {
        return response.data;
      }
    } catch (error) {
      console.warn('인기 게시글 API 오류:', error);
    }

    // 기본 목업 데이터
    return [];
  }

  /**
   * 실시간 활동 피드 조회
   */
  async getRecentActivity(limit: number = 20) {
    try {
      const response = await apiClient.request('GET', '/analytics/recent-activity', {
        params: { limit }
      });

      if (response.success && response.data) {
        return response.data;
      }
    } catch (error) {
      console.warn('최근 활동 API 오류:', error);
    }

    return [];
  }
}

// 글로벌 인스턴스
export const analyticsDashboardService = new AnalyticsDashboardService();