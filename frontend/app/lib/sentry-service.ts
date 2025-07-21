/**
 * 프론트엔드 Sentry 통합 서비스
 * 
 * 기존 error-logger.ts와 함께 동작하는 Sentry 에러 추적 및 성능 모니터링
 */

import * as Sentry from '@sentry/react';

export interface SentryConfig {
  dsn?: string;
  environment?: string;
  tracesSampleRate?: number;
  sendDefaultPii?: boolean;
  debug?: boolean;
}

export interface UserContext {
  id: string;
  email?: string;
  username?: string;
  [key: string]: any;
}

export interface ErrorContext {
  component?: string;
  action?: string;
  url?: string;
  userId?: string;
  sessionId?: string;
  additionalData?: Record<string, any>;
}

class FrontendSentryService {
  private isInitialized: boolean = false;
  private config: SentryConfig = {};

  /**
   * Sentry 초기화
   */
  public initialize(config: SentryConfig): void {
    // 환경변수에서 설정 로드
    const finalConfig: SentryConfig = {
      dsn: config.dsn || this.getDsnFromEnvironment(),
      environment: config.environment || this.getEnvironmentFromEnvironment(),
      tracesSampleRate: config.tracesSampleRate ?? this.getTracesSampleRateFromEnvironment(),
      sendDefaultPii: config.sendDefaultPii ?? this.getSendDefaultPiiFromEnvironment(),
      debug: config.debug ?? this.getDebugFromEnvironment()
    };

    this.config = finalConfig;

    // DSN이 없으면 Sentry 초기화 건너뛰기
    if (!finalConfig.dsn) {
      console.warn('⚠️ Sentry DSN이 설정되지 않았습니다. Sentry 초기화를 건너뜁니다.');
      return;
    }

    try {
      Sentry.init({
        dsn: finalConfig.dsn,
        environment: finalConfig.environment,
        release: `frontend@${finalConfig.environment || 'development'}`,
        tracesSampleRate: finalConfig.tracesSampleRate,
        sendDefaultPii: finalConfig.sendDefaultPii,
        debug: finalConfig.debug,
        // 기본 통합만 사용 (수동으로 통합 설정하지 않음)
        // integrations는 자동으로 설정됨
        beforeSend: this.beforeSend.bind(this),
        beforeSendTransaction: this.beforeSendTransaction.bind(this),
        // Session 추적 활성화
        autoSessionTracking: true,
        // 프로덕션에서는 성능 최적화
        initialScope: {
          tags: {
            component: 'frontend',
            platform: 'react'
          }
        }
      });

      this.isInitialized = true;
      
      // 전역에 Sentry 노출 (디버깅용)
      if (typeof window !== 'undefined') {
        // Sentry SDK를 전역에 노출
        Object.defineProperty(window, 'Sentry', {
          value: Sentry,
          writable: false,
          configurable: true
        });
        
        // Client와 Scope 노출 (최신 API 사용)
        (window as any).SentryClient = Sentry.getClient();
        (window as any).SentryCurrentScope = Sentry.getCurrentScope();
        
        console.log('🔗 Sentry 전역 노출 완료:', {
          Sentry: !!window.Sentry,
          Client: !!(window as any).SentryClient,
          CurrentScope: !!(window as any).SentryCurrentScope
        });
      }
      
      console.log('✅ Sentry 초기화 완료:', {
        environment: finalConfig.environment,
        dsn: finalConfig.dsn?.substring(0, 20) + '...',
        tracesSampleRate: finalConfig.tracesSampleRate,
        release: `frontend@${finalConfig.environment || 'development'}`,
        client: !!Sentry.getClient(),
        currentScope: !!Sentry.getCurrentScope()
      });

    } catch (error) {
      console.error('❌ Sentry 초기화 실패:', error);
    }
  }

  /**
   * 에러 필터링 함수
   */
  private beforeSend(event: Sentry.Event): Sentry.Event | null {
    // 404, 403 등의 HTTP 에러는 필터링
    if (event.exception) {
      for (const exception of event.exception.values || []) {
        if (exception.type === 'ChunkLoadError' || 
            exception.type === 'ResizeObserver' ||
            exception.value?.includes('404') ||
            exception.value?.includes('403')) {
          return null;
        }
      }
    }

    // 개발 환경에서 상세 로그
    if (this.config.environment === 'development') {
      console.log('🚨 Sentry Event:', event);
    }

    return event;
  }

  /**
   * 트랜잭션 필터링 함수
   */
  private beforeSendTransaction(event: Sentry.Transaction): Sentry.Transaction | null {
    // 너무 짧은 트랜잭션은 필터링
    if (event.start_timestamp && event.timestamp) {
      const duration = event.timestamp - event.start_timestamp;
      if (duration < 0.001) { // 1ms 미만
        return null;
      }
    }

    return event;
  }

  /**
   * 사용자 컨텍스트 설정
   */
  public setUser(user: UserContext): void {
    if (!this.isInitialized) return;

    Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.username,
      ...user
    });

    console.log('👤 Sentry 사용자 컨텍스트 설정:', user.id);
  }

  /**
   * 사용자 컨텍스트 제거
   */
  public clearUser(): void {
    if (!this.isInitialized) return;

    Sentry.setUser(null);
    console.log('👤 Sentry 사용자 컨텍스트 제거');
  }

  /**
   * 에러 수동 캡처
   */
  public captureError(error: Error, context?: ErrorContext): void {
    if (!this.isInitialized) {
      console.error('Sentry 미초기화 상태에서 에러 캡처 시도:', error);
      return;
    }

    Sentry.withScope((scope) => {
      if (context) {
        // 컨텍스트 설정
        if (context.component) scope.setTag('component', context.component);
        if (context.action) scope.setTag('action', context.action);
        if (context.url) scope.setTag('url', context.url);
        if (context.userId) scope.setTag('userId', context.userId);
        if (context.sessionId) scope.setTag('sessionId', context.sessionId);
        
        // 추가 데이터 설정
        if (context.additionalData) {
          Object.entries(context.additionalData).forEach(([key, value]) => {
            scope.setExtra(key, value);
          });
        }
      }

      // 에러 캡처
      Sentry.captureException(error);
    });

    console.error('🚨 Sentry 에러 캡처:', error.message);
  }

  /**
   * 커스텀 메시지 캡처
   */
  public captureMessage(message: string, level: Sentry.SeverityLevel = 'info', context?: ErrorContext): void {
    if (!this.isInitialized) return;

    Sentry.withScope((scope) => {
      scope.setLevel(level);

      if (context) {
        if (context.component) scope.setTag('component', context.component);
        if (context.action) scope.setTag('action', context.action);
        if (context.additionalData) {
          Object.entries(context.additionalData).forEach(([key, value]) => {
            scope.setExtra(key, value);
          });
        }
      }

      Sentry.captureMessage(message);
    });

    console.log(`📝 Sentry 메시지 캡처 [${level}]:`, message);
  }

  /**
   * 성능 트랜잭션 시작
   */
  public startTransaction(name: string, op: string = 'navigation'): any | null {
    if (!this.isInitialized) return null;

    // Sentry v8의 새로운 API 사용 - startSpan으로 대체
    const span = Sentry.startSpan({ name, op }, (span) => span);
    console.log('⏱️ Sentry 스팬 시작:', name);
    return span;
  }

  /**
   * 브레드크럼 추가
   */
  public addBreadcrumb(message: string, category: string = 'custom', level: Sentry.SeverityLevel = 'info', data?: any): void {
    if (!this.isInitialized) return;

    Sentry.addBreadcrumb({
      message,
      category,
      level,
      data,
      timestamp: Date.now() / 1000,
    });

    console.log('🍞 Sentry 브레드크럼 추가:', message);
  }

  /**
   * 환경변수에서 DSN 로드
   */
  private getDsnFromEnvironment(): string | undefined {
    // Vite 환경변수 접근 (클라이언트 사이드)
    if (typeof window !== 'undefined') {
      return window.ENV?.SENTRY_DSN || import.meta.env.VITE_SENTRY_DSN;
    }
    return import.meta.env.VITE_SENTRY_DSN;
  }

  /**
   * 환경변수에서 환경 설정 로드
   */
  private getEnvironmentFromEnvironment(): string {
    if (typeof window !== 'undefined') {
      return window.ENV?.NODE_ENV || window.ENV?.ENVIRONMENT || import.meta.env.VITE_ENVIRONMENT || 'development';
    }
    return import.meta.env.VITE_ENVIRONMENT || 'development';
  }

  /**
   * 환경변수에서 트레이스 샘플링 비율 로드
   */
  private getTracesSampleRateFromEnvironment(): number {
    if (typeof window !== 'undefined' && window.ENV?.SENTRY_TRACES_SAMPLE_RATE) {
      return parseFloat(window.ENV.SENTRY_TRACES_SAMPLE_RATE);
    }
    return 1.0;
  }

  /**
   * 환경변수에서 PII 전송 설정 로드
   */
  private getSendDefaultPiiFromEnvironment(): boolean {
    if (typeof window !== 'undefined' && window.ENV?.SENTRY_SEND_DEFAULT_PII) {
      return window.ENV.SENTRY_SEND_DEFAULT_PII.toLowerCase() === 'true';
    }
    return false;
  }

  /**
   * 환경변수에서 디버그 설정 로드
   */
  private getDebugFromEnvironment(): boolean {
    if (typeof window !== 'undefined' && window.ENV?.SENTRY_DEBUG) {
      return window.ENV.SENTRY_DEBUG.toLowerCase() === 'true';
    }
    return false;
  }

  /**
   * 초기화 상태 확인
   */
  public isReady(): boolean {
    return this.isInitialized;
  }

  /**
   * 현재 설정 반환
   */
  public getConfig(): SentryConfig {
    return { ...this.config };
  }

  /**
   * Sentry SDK 직접 접근 (디버깅용)
   */
  public getSentrySDK() {
    return Sentry;
  }

  /**
   * Sentry Client 접근 (최신 API 사용)
   */
  public getClient() {
    return Sentry.getClient();
  }

  /**
   * Current Scope 접근 (Hub 대신)
   */
  public getCurrentScope() {
    return Sentry.getCurrentScope();
  }

  /**
   * Global Scope 접근
   */
  public getGlobalScope() {
    return Sentry.getGlobalScope();
  }

  /**
   * 직접 Exception 캡처 (SDK 방식)
   */
  public directCaptureException(error: Error): string | undefined {
    if (!this.isInitialized) return undefined;
    return Sentry.captureException(error);
  }

  /**
   * 강제 플러시
   */
  public flush(timeout: number = 2000): Promise<boolean> {
    if (!this.isInitialized) return Promise.resolve(false);
    return Sentry.flush(timeout);
  }
}

// 전역 인스턴스
export const sentryService = new FrontendSentryService();

// React Hook
export function useSentry() {
  const captureError = (error: Error, context?: ErrorContext) => {
    sentryService.captureError(error, context);
  };

  const captureMessage = (message: string, level: Sentry.SeverityLevel = 'info', context?: ErrorContext) => {
    sentryService.captureMessage(message, level, context);
  };

  const setUser = (user: UserContext) => {
    sentryService.setUser(user);
  };

  const clearUser = () => {
    sentryService.clearUser();
  };

  const addBreadcrumb = (message: string, category?: string, level?: Sentry.SeverityLevel, data?: any) => {
    sentryService.addBreadcrumb(message, category, level, data);
  };

  return {
    captureError,
    captureMessage,
    setUser,
    clearUser,
    addBreadcrumb,
    isReady: sentryService.isReady(),
    config: sentryService.getConfig(),
  };
}

// 유틸리티 함수들
export const withSentryProfiling = <T extends (...args: any[]) => any>(
  fn: T,
  name: string,
  component?: string
): T => {
  return ((...args: any[]) => {
    // Sentry v8의 새로운 API 사용
    return Sentry.startSpan(
      { name: `${component || 'function'}.${name}`, op: 'function' },
      (span) => {
        try {
          const result = fn(...args);
          
          // Promise인 경우 처리
          if (result instanceof Promise) {
            return result
              .then((res) => {
                span?.setStatus({ code: 1 }); // ok
                return res;
              })
              .catch((error) => {
                span?.setStatus({ code: 2 }); // error
                sentryService.captureError(error, { component, action: name });
                throw error;
              });
          }
          
          // 동기 함수인 경우
          span?.setStatus({ code: 1 }); // ok
          return result;
          
        } catch (error) {
          span?.setStatus({ code: 2 }); // error
          sentryService.captureError(error as Error, { component, action: name });
          throw error;
        }
      }
    );
  }) as T;
};

// 환경변수 타입 확장
declare global {
  interface Window {
    ENV?: {
      SENTRY_DSN?: string;
      NODE_ENV?: string;
      ENVIRONMENT?: string;
      SENTRY_TRACES_SAMPLE_RATE?: string;
      SENTRY_SEND_DEFAULT_PII?: string;
      SENTRY_DEBUG?: string;
    };
  }
}

// Import.meta 환경변수 타입 확장 (Vite/Remix)
interface ImportMetaEnv {
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_ENVIRONMENT?: string;
  readonly VITE_SENTRY_TRACES_SAMPLE_RATE?: string;
  readonly VITE_SENTRY_SEND_DEFAULT_PII?: string;
  readonly VITE_SENTRY_DEBUG?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}