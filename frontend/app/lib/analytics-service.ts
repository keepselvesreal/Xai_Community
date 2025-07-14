// GA4 글로벌 타입 정의
declare global {
  interface Window {
    gtag: (...args: any[]) => void;
    dataLayer: any[];
  }
}

export class AnalyticsService {
  private measurementId: string;
  private environment: string;

  constructor() {
    this.measurementId = this.getMeasurementId();
    this.environment = this.getEnvironment();
    
    // 개발시 디버깅 정보 출력
    if (this.environment !== 'production') {
      if (this.isConnected()) {
        console.log('✅ GA4 Analytics 초기화 성공:', {
          environment: this.environment,
          measurementId: this.measurementId,
          isConnected: true
        });
      } else {
        console.warn('⚠️ GA4 Analytics 초기화 실패:', {
          environment: this.environment,
          measurementId: this.measurementId || '미설정',
          isConnected: false,
          reason: !this.measurementId ? '측정 ID 없음' : '브라우저 환경 아님'
        });
      }
    }
  }

  // GA4 측정 ID 가져오기 (환경별 자동 선택)
  getMeasurementId(): string {
    // 환경 확인 (NODE_ENV 또는 VITE_NODE_ENV 사용)
    const nodeEnv = typeof window !== 'undefined' 
      ? import.meta.env.VITE_NODE_ENV || import.meta.env.NODE_ENV
      : process.env.VITE_NODE_ENV || process.env.NODE_ENV;
    
    let measurementId = '';
    let expectedVarName = '';
    
    // 환경별 측정 ID 선택
    switch (nodeEnv) {
      case 'production':
        measurementId = typeof window !== 'undefined' 
          ? import.meta.env.VITE_GA_MEASUREMENT_ID_PROD || ''
          : process.env.VITE_GA_MEASUREMENT_ID_PROD || '';
        expectedVarName = 'VITE_GA_MEASUREMENT_ID_PROD';
        break;
      
      case 'staging':
        measurementId = typeof window !== 'undefined' 
          ? import.meta.env.VITE_GA_MEASUREMENT_ID_STAGING || ''
          : process.env.VITE_GA_MEASUREMENT_ID_STAGING || '';
        expectedVarName = 'VITE_GA_MEASUREMENT_ID_STAGING';
        break;
      
      case 'development':
      case 'test':
      default:
        measurementId = typeof window !== 'undefined' 
          ? import.meta.env.VITE_GA_MEASUREMENT_ID_DEV || ''
          : process.env.VITE_GA_MEASUREMENT_ID_DEV || '';
        expectedVarName = 'VITE_GA_MEASUREMENT_ID_DEV';
    }
    
    // GA4 측정 ID 유효성 검사
    if (!measurementId) {
      console.error(`❌ GA4: ${nodeEnv} 환경의 측정 ID가 설정되지 않았습니다.`);
      console.error(`   필수 환경변수: ${expectedVarName}`);
      console.error(`   설정 방법: .env 파일에 ${expectedVarName}=G-XXXXXXXXXX 추가`);
      console.error(`   GA4 이벤트 추적이 비활성화됩니다.`);
    } else if (!measurementId.startsWith('G-')) {
      console.error(`❌ GA4: 잘못된 측정 ID 형식입니다: ${measurementId}`);
      console.error(`   올바른 형식: G-XXXXXXXXXX (예: G-S7LF8WRRC7)`);
      console.error(`   GA4 이벤트 추적이 비활성화됩니다.`);
      return '';
    }
    
    return measurementId;
  }

  // 현재 환경 가져오기
  getEnvironment(): string {
    const env = typeof window !== 'undefined' 
      ? import.meta.env.VITE_NODE_ENV || import.meta.env.NODE_ENV
      : process.env.VITE_NODE_ENV || process.env.NODE_ENV;
    
    if (!env) {
      console.warn('⚠️ GA4: 환경변수 VITE_NODE_ENV 또는 NODE_ENV가 설정되지 않았습니다. development로 기본 설정됩니다.');
      console.warn('   설정 방법: .env 파일에 VITE_NODE_ENV=development|staging|production 추가');
      return 'development';
    }
    
    const validEnvironments = ['development', 'staging', 'production', 'test'];
    if (!validEnvironments.includes(env)) {
      console.warn(`⚠️ GA4: 알 수 없는 환경 '${env}'입니다. development로 설정됩니다.`);
      console.warn(`   유효한 환경: ${validEnvironments.join(', ')}`);
      return 'development';
    }
    
    return env;
  }

  // GA4 연결 상태 확인
  isConnected(): boolean {
    return typeof window !== 'undefined' && !!this.measurementId;
  }

  // 페이지 뷰 이벤트 전송
  trackPageView(pagePath: string, pageTitle?: string): void {
    if (!this.isConnected()) {
      console.warn('GA4: 페이지 뷰 추적 실패 - 측정 ID가 없거나 서버 환경입니다.');
      return;
    }

    try {
      if (window.gtag) {
        window.gtag('config', this.measurementId, {
          page_title: pageTitle || document.title,
          page_location: window.location.href,
          page_path: pagePath,
        });

        console.log('GA4 페이지 뷰 전송:', pagePath);
      } else {
        console.warn('GA4: gtag 함수가 로드되지 않았습니다.');
      }
    } catch (error) {
      console.error('GA4 페이지 뷰 전송 오류:', error);
    }
  }

  // 커스텀 이벤트 전송
  trackEvent(eventName: string, eventParameters?: { [key: string]: any }): void {
    if (!this.isConnected()) {
      console.warn('GA4: 이벤트 추적 실패 - 측정 ID가 없거나 서버 환경입니다.');
      return;
    }

    try {
      if (window.gtag) {
        window.gtag('event', eventName, {
          ...eventParameters,
          // 기본 매개변수 추가
          timestamp: new Date().toISOString(),
          page_location: window.location.href,
          page_path: window.location.pathname,
          environment: this.environment,
        });

        console.log('GA4 이벤트 전송:', eventName, eventParameters);
      } else {
        console.warn('GA4: gtag 함수가 로드되지 않았습니다.');
      }
    } catch (error) {
      console.error('GA4 이벤트 전송 오류:', error);
    }
  }

  // 사용자 참여 이벤트
  trackUserEngagement(engagementTimeMs: number): void {
    this.trackEvent('user_engagement', {
      engagement_time_msec: engagementTimeMs,
      page_title: document.title,
      page_location: window.location.href,
    });
  }

  // 전환 이벤트들
  trackSignUpConversion(userId: string, method: string): void {
    this.trackEvent('sign_up', {
      user_id: userId,
      method: method,
    });
  }

  trackLoginConversion(userId: string, method: string): void {
    this.trackEvent('login', {
      user_id: userId,
      method: method,
    });
  }

  trackPostCreationConversion(postId: string, category: string): void {
    this.trackEvent('post_create', {
      post_id: postId,
      category: category,
    });
  }

  // 퍼널 분석 이벤트들
  trackFunnelStep(funnelName: string, stepName: string, stepNumber: number): void {
    this.trackEvent('funnel_step', {
      funnel_name: funnelName,
      step_name: stepName,
      step_number: stepNumber,
    });
  }

  trackFunnelComplete(funnelName: string, totalSteps: number, completionTimeMs: number): void {
    this.trackEvent('funnel_complete', {
      funnel_name: funnelName,
      total_steps: totalSteps,
      completion_time_msec: completionTimeMs,
    });
  }

  // 사용자 행동 이벤트들
  trackPostLike(postId: string, category: string): void {
    this.trackEvent('post_like', {
      post_id: postId,
      category: category,
    });
  }

  trackPostDislike(postId: string, category: string): void {
    this.trackEvent('post_dislike', {
      post_id: postId,
      category: category,
    });
  }

  trackPostBookmark(postId: string, category: string): void {
    this.trackEvent('post_bookmark', {
      post_id: postId,
      category: category,
    });
  }

  trackCommentCreate(postId: string, commentId: string, pageType?: string): void {
    this.trackEvent('comment_create', {
      post_id: postId,
      comment_id: commentId,
      page_type: pageType || 'unknown',
    });
  }

  // 페이지별 댓글 추적 메서드들
  trackBoardComment(postId: string, commentId: string): void {
    this.trackEvent('comment_create', {
      post_id: postId,
      comment_id: commentId,
      page_type: 'board',
      interaction_type: 'comment'
    });
  }

  trackPropertyInfoComment(postId: string, commentId: string): void {
    this.trackEvent('comment_create', {
      post_id: postId,
      comment_id: commentId,
      page_type: 'property_information',
      interaction_type: 'comment'
    });
  }

  trackExpertTipComment(postId: string, commentId: string): void {
    this.trackEvent('comment_create', {
      post_id: postId,
      comment_id: commentId,
      page_type: 'expert_tips',
      interaction_type: 'comment'
    });
  }

  trackServiceReview(serviceId: string, reviewId: string, rating?: number): void {
    this.trackEvent('service_review_create', {
      service_id: serviceId,
      review_id: reviewId,
      page_type: 'moving_services',
      interaction_type: 'review',
      rating: rating
    });
  }

  trackServiceInquiryComment(serviceId: string, commentId: string): void {
    this.trackEvent('service_inquiry_create', {
      service_id: serviceId,
      comment_id: commentId,
      page_type: 'moving_services',
      interaction_type: 'inquiry'
    });
  }

  trackServiceReviewComment(serviceId: string, commentId: string): void {
    this.trackEvent('service_review_create', {
      service_id: serviceId,
      comment_id: commentId,
      page_type: 'moving_services',
      interaction_type: 'review'
    });
  }

  trackSearchQuery(query: string, resultCount: number): void {
    this.trackEvent('search', {
      search_term: query,
      result_count: resultCount,
    });
  }

  trackFileUpload(fileType: string, fileSize: number): void {
    this.trackEvent('file_upload', {
      file_type: fileType,
      file_size: fileSize,
    });
  }

  // 전환율 분석을 위한 고급 이벤트들
  trackServiceInquiry(serviceType: string, inquiryType: string): void {
    this.trackEvent('service_inquiry', {
      service_type: serviceType,
      inquiry_type: inquiryType,
    });
  }

  trackEmailVerification(email: string, success: boolean): void {
    this.trackEvent('email_verification', {
      email_hash: this.hashEmail(email),
      success: success,
    });
  }

  // 유틸리티 메서드
  private hashEmail(email: string): string {
    // 간단한 해싱 (실제 운영에서는 더 강력한 해싱 사용)
    let hash = 0;
    for (let i = 0; i < email.length; i++) {
      const char = email.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 32비트 정수로 변환
    }
    return hash.toString(36);
  }
}