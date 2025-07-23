import { apiClient } from './api';

/**
 * 간소화된 Analytics Dashboard Service
 * 모든 목업 데이터 제거하고 실제 백엔드 API만 사용
 */

// 간소화된 응답 타입
export interface UserStats {
  total_users: number;
  new_users_today: number;
  new_users_weekly: number;
  daily_active_users: number;
}

export interface ConversionRate {
  visitors_today: number;
  signups_today: number;
  conversion_rate_today: number;
  visitors_yesterday: number;
  signups_yesterday: number;
  conversion_rate_yesterday: number;
  conversion_rate_change: number;
}

export interface EventStats {
  post_creation: {
    today: number;
    yesterday_change: number;
  };
  post_likes: {
    today: number;
    yesterday_change: number;
  };
  post_bookmarks: {
    today: number;
    yesterday_change: number;
  };
  comment_creation: {
    today: number;
    yesterday_change: number;
  };
}

export interface BounceRate {
  site_bounce_rate: number;
}

export interface RealtimeActivity {
  timestamp: string;
  activity_type: string;
  user_name: string;
  description: string;
  target_title?: string;
}

export class AnalyticsDashboardService {
  
  /**
   * 사용자 통계 조회
   */
  async getUserStats(): Promise<UserStats> {
    try {
      const response = await apiClient.request('GET', '/api/analytics/users/stats');
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('사용자 통계 조회 실패');
    } catch (error) {
      console.error('사용자 통계 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 가입 전환율 조회
   */
  async getConversionRate(): Promise<ConversionRate> {
    try {
      const response = await apiClient.request('GET', '/api/analytics/funnel/signup');
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('가입 전환율 조회 실패');
    } catch (error) {
      console.error('가입 전환율 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 이벤트 통계 조회
   */
  async getEventStats(): Promise<EventStats> {
    try {
      const response = await apiClient.request('GET', '/api/analytics/events/stats');
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('이벤트 통계 조회 실패');
    } catch (error) {
      console.error('이벤트 통계 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 전체 사이트 이탈률 조회
   */
  async getBounceRate(): Promise<BounceRate> {
    try {
      const response = await apiClient.request('GET', '/api/analytics/bounce-rate');
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('이탈률 조회 실패');
    } catch (error) {
      console.error('이탈률 조회 오류:', error);
      throw error;
    }
  }

  /**
   * 실시간 활동 피드 조회
   */
  async getRealtimeActivity(limit: number = 10): Promise<RealtimeActivity[]> {
    try {
      const response = await apiClient.request('GET', '/api/analytics/realtime/activity', {
        params: { limit }
      });
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('실시간 활동 조회 실패');
    } catch (error) {
      console.error('실시간 활동 조회 오류:', error);
      throw error;
    }
  }


}

// 글로벌 인스턴스
export const analyticsDashboardService = new AnalyticsDashboardService();