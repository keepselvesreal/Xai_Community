/**
 * 클라이언트 에러 리포터 유틸리티
 * 
 * 작업 시간: 2025-07-23 14:30:00 KST
 * 작업 버전: v1.0.0
 * 주요 컴포넌트들:
 * - ErrorReporter: 에러 수집 및 전송 클래스
 * - ClientErrorData: 클라이언트 에러 데이터 인터페이스
 * - reportError: 전역 에러 리포팅 함수
 * 
 * 주요 함수들:
 * - reportError: 일반 JavaScript 에러 리포팅 (line 45-70)
 * - reportNetworkError: 네트워크 에러 리포팅 (line 72-100)
 * - reportTimeoutError: 타임아웃 에러 리포팅 (line 102-125)
 * - setupGlobalErrorHandlers: 전역 에러 핸들러 등록 (line 160-200)
 * 
 * 관련 파일들:
 * - backend/nadle_backend/routers/client_errors.py: 서버 측 에러 수집 API
 * - app/root.tsx: 전역 에러 핸들러 등록 필요
 */

interface ClientErrorData {
  error_type: string;
  error_message: string;
  stack_trace?: string;
  user_agent?: string;
  url?: string;
  browser?: string;
  browser_version?: string;
  os?: string;
  network_status?: string;
  request_url?: string;
  response_status?: number;
  timeout_duration?: number;
  component_name?: string;
  page_path?: string;
  action?: string;
  additional_info?: Record<string, any>;
}

class ErrorReporter {
  private static instance: ErrorReporter;
  private apiEndpoint = '/api/client-errors/report';
  private isOnline = true;
  private errorQueue: ClientErrorData[] = [];

  private constructor() {
    // 브라우저 환경에서만 네트워크 상태 모니터링
    if (typeof window !== 'undefined' && typeof navigator !== 'undefined') {
      this.isOnline = navigator.onLine;
      
      window.addEventListener('online', () => {
        this.isOnline = true;
        this.flushErrorQueue();
      });
      
      window.addEventListener('offline', () => {
        this.isOnline = false;
      });
    }
  }

  static getInstance(): ErrorReporter {
    if (!ErrorReporter.instance) {
      ErrorReporter.instance = new ErrorReporter();
    }
    return ErrorReporter.instance;
  }

  /**
   * 일반 JavaScript 에러 리포팅
   */
  async reportError(
    error: Error,
    context: {
      componentName?: string;
      action?: string;
      additionalInfo?: Record<string, any>;
    } = {}
  ): Promise<void> {
    // 서버 환경에서는 에러 리포팅 스킵
    if (typeof window === 'undefined') {
      return;
    }

    const errorData: ClientErrorData = {
      error_type: error.name || 'Error',
      error_message: error.message,
      stack_trace: error.stack,
      url: window.location.href,
      user_agent: navigator.userAgent,
      browser: this.getBrowserInfo(),
      browser_version: this.getBrowserVersion(),
      os: this.getOSInfo(),
      network_status: this.isOnline ? 'online' : 'offline',
      component_name: context.componentName,
      page_path: window.location.pathname,
      action: context.action,
      additional_info: context.additionalInfo
    };

    await this.sendError(errorData);
  }

  /**
   * 네트워크 에러 리포팅
   */
  async reportNetworkError(
    error: Error,
    requestUrl: string,
    responseStatus?: number,
    context: {
      componentName?: string;
      action?: string;
      additionalInfo?: Record<string, any>;
    } = {}
  ): Promise<void> {
    // 서버 환경에서는 에러 리포팅 스킵
    if (typeof window === 'undefined') {
      return;
    }

    const errorData: ClientErrorData = {
      error_type: 'NetworkError',
      error_message: error.message || 'Network request failed',
      stack_trace: error.stack,
      url: window.location.href,
      user_agent: navigator.userAgent,
      browser: this.getBrowserInfo(),
      browser_version: this.getBrowserVersion(),
      os: this.getOSInfo(),
      network_status: this.isOnline ? 'online' : 'offline',
      request_url: requestUrl,
      response_status: responseStatus,
      component_name: context.componentName,
      page_path: window.location.pathname,
      action: context.action,
      additional_info: context.additionalInfo
    };

    await this.sendError(errorData);
  }

  /**
   * 타임아웃 에러 리포팅
   */
  async reportTimeoutError(
    requestUrl: string,
    timeoutDuration: number,
    context: {
      componentName?: string;
      action?: string;
      additionalInfo?: Record<string, any>;
    } = {}
  ): Promise<void> {
    // 서버 환경에서는 에러 리포팅 스킵
    if (typeof window === 'undefined') {
      return;
    }

    const errorData: ClientErrorData = {
      error_type: 'TimeoutError',
      error_message: `Request timeout after ${timeoutDuration}ms`,
      url: window.location.href,
      user_agent: navigator.userAgent,
      browser: this.getBrowserInfo(),
      browser_version: this.getBrowserVersion(),
      os: this.getOSInfo(),
      network_status: this.isOnline ? 'online' : 'offline',
      request_url: requestUrl,
      timeout_duration: timeoutDuration,
      component_name: context.componentName,
      page_path: window.location.pathname,
      action: context.action,
      additional_info: context.additionalInfo
    };

    await this.sendError(errorData);
  }

  private async sendError(errorData: ClientErrorData): Promise<void> {
    if (!this.isOnline) {
      // 오프라인 상태면 큐에 저장
      this.errorQueue.push(errorData);
      return;
    }

    try {
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData),
      });

      if (!response.ok) {
        console.warn('Failed to report error to server:', response.status);
      }
    } catch (error) {
      // 에러 리포팅이 실패해도 앱은 계속 동작해야 함
      console.warn('Error reporter failed:', error);
      this.errorQueue.push(errorData);
    }
  }

  private async flushErrorQueue(): Promise<void> {
    if (this.errorQueue.length === 0) return;

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    for (const errorData of errors) {
      await this.sendError(errorData);
    }
  }

  private getBrowserInfo(): string {
    if (typeof navigator === 'undefined') return 'Unknown';
    
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    
    return 'Unknown';
  }

  private getBrowserVersion(): string {
    if (typeof navigator === 'undefined') return 'Unknown';
    
    const userAgent = navigator.userAgent;
    const match = userAgent.match(/(Chrome|Firefox|Safari|Edge)\/(\d+)/);
    return match ? match[2] : 'Unknown';
  }

  private getOSInfo(): string {
    if (typeof navigator === 'undefined') return 'Unknown';
    
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Windows')) return 'Windows';
    if (userAgent.includes('Mac')) return 'macOS';
    if (userAgent.includes('Linux')) return 'Linux';
    if (userAgent.includes('Android')) return 'Android';
    if (userAgent.includes('iOS')) return 'iOS';
    
    return 'Unknown';
  }
}

// 전역 인스턴스
const errorReporter = ErrorReporter.getInstance();

/**
 * 전역 에러 리포팅 함수들
 */
export const reportError = (
  error: Error,
  context?: {
    componentName?: string;
    action?: string;
    additionalInfo?: Record<string, any>;
  }
) => errorReporter.reportError(error, context);

export const reportNetworkError = (
  error: Error,
  requestUrl: string,
  responseStatus?: number,
  context?: {
    componentName?: string;
    action?: string;
    additionalInfo?: Record<string, any>;
  }
) => errorReporter.reportNetworkError(error, requestUrl, responseStatus, context);

export const reportTimeoutError = (
  requestUrl: string,
  timeoutDuration: number,
  context?: {
    componentName?: string;
    action?: string;
    additionalInfo?: Record<string, any>;
  }
) => errorReporter.reportTimeoutError(requestUrl, timeoutDuration, context);

/**
 * 전역 에러 핸들러 설정
 */
export const setupGlobalErrorHandlers = () => {
  // 브라우저 환경에서만 실행
  if (typeof window === 'undefined') {
    return;
  }

  // 처리되지 않은 JavaScript 에러
  window.addEventListener('error', (event) => {
    reportError(event.error || new Error(event.message), {
      additionalInfo: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        type: 'unhandled_error'
      }
    });
  });

  // 처리되지 않은 Promise rejection
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error 
      ? event.reason 
      : new Error(String(event.reason));
    
    reportError(error, {
      additionalInfo: {
        type: 'unhandled_promise_rejection'
      }
    });
  });

  // 리소스 로딩 에러
  window.addEventListener('error', (event) => {
    if (event.target !== window) {
      const target = event.target as HTMLElement;
      const error = new Error(`Resource loading failed: ${target.tagName}`);
      
      reportError(error, {
        additionalInfo: {
          type: 'resource_loading_error',
          tagName: target.tagName,
          src: (target as any).src || (target as any).href,
          currentSrc: (target as any).currentSrc
        }
      });
    }
  }, true);

  console.log('✅ Global error handlers registered');
};

export default errorReporter;