/**
 * 프론트엔드 에러 로깅 시스템
 * 
 * Sentry 대체용 자체 에러 로깅 및 Discord 알림 시스템
 */

export interface ErrorContext {
  userId?: string;
  sessionId?: string;
  url?: string;
  userAgent?: string;
  timestamp?: string;
  component?: string;
  action?: string;
  additionalData?: Record<string, any>;
}

export interface ErrorInfo {
  message: string;
  stack?: string;
  type: 'javascript' | 'unhandled-rejection' | 'resource' | 'network' | 'custom';
  severity: 'low' | 'medium' | 'high' | 'critical';
  context?: ErrorContext;
}

export interface PerformanceInfo {
  operation: string;
  duration: number;
  component?: string;
  isSlowOperation?: boolean;
  memoryUsage?: number;
  additionalMetrics?: Record<string, any>;
}

class FrontendErrorLogger {
  private discordWebhookUrl: string | null = null;
  private isEnabled: boolean = true;
  private errorQueue: ErrorInfo[] = [];
  private performanceQueue: PerformanceInfo[] = [];
  private maxQueueSize: number = 100;
  private flushInterval: number = 30000; // 30초
  private retryCount: number = 0;
  private maxRetries: number = 3;

  constructor() {
    this.setupErrorHandlers();
    this.setupPerformanceMonitoring();
    this.startPeriodicFlush();
  }

  /**
   * 에러 로거 초기화
   */
  public initialize(config: {
    discordWebhookUrl?: string;
    isEnabled?: boolean;
    maxQueueSize?: number;
    flushInterval?: number;
  }) {
    this.discordWebhookUrl = config.discordWebhookUrl || null;
    this.isEnabled = config.isEnabled ?? true;
    this.maxQueueSize = config.maxQueueSize || 100;
    this.flushInterval = config.flushInterval || 30000;
  }

  /**
   * 전역 에러 핸들러 설정
   */
  private setupErrorHandlers() {
    // JavaScript 에러 처리
    window.addEventListener('error', (event) => {
      this.logError({
        message: event.message,
        stack: event.error?.stack,
        type: 'javascript',
        severity: 'high',
        context: {
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          component: 'global',
          additionalData: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
          }
        }
      });
    });

    // Promise rejection 에러 처리
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        message: event.reason?.message || 'Unhandled Promise Rejection',
        stack: event.reason?.stack,
        type: 'unhandled-rejection',
        severity: 'high',
        context: {
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          component: 'global',
          additionalData: {
            reason: event.reason
          }
        }
      });
    });

    // 리소스 로딩 에러 처리
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        const element = event.target as HTMLElement;
        this.logError({
          message: `Resource loading failed: ${element.tagName}`,
          type: 'resource',
          severity: 'medium',
          context: {
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            component: 'resource-loader',
            additionalData: {
              tagName: element.tagName,
              src: (element as any).src || (element as any).href,
              outerHTML: element.outerHTML
            }
          }
        });
      }
    }, true);
  }

  /**
   * 성능 모니터링 설정
   */
  private setupPerformanceMonitoring() {
    // Navigation Timing API 사용
    window.addEventListener('load', () => {
      setTimeout(() => {
        const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (perfData) {
          this.logPerformance({
            operation: 'page-load',
            duration: perfData.loadEventEnd - perfData.navigationStart,
            component: 'navigation',
            isSlowOperation: (perfData.loadEventEnd - perfData.navigationStart) > 3000,
            additionalMetrics: {
              domContentLoaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
              firstContentfulPaint: this.getFirstContentfulPaint(),
              resourceLoadTime: perfData.loadEventEnd - perfData.domContentLoadedEventEnd
            }
          });
        }
      }, 0);
    });

    // Long Task API 사용 (지원되는 경우)
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) { // 50ms 이상의 긴 작업
              this.logPerformance({
                operation: 'long-task',
                duration: entry.duration,
                component: 'performance-observer',
                isSlowOperation: true,
                additionalMetrics: {
                  startTime: entry.startTime,
                  entryType: entry.entryType
                }
              });
            }
          }
        });
        observer.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        console.warn('Long Task API not supported');
      }
    }
  }

  /**
   * First Contentful Paint 측정
   */
  private getFirstContentfulPaint(): number | null {
    const perfEntries = performance.getEntriesByType('paint');
    const fcp = perfEntries.find(entry => entry.name === 'first-contentful-paint');
    return fcp ? fcp.startTime : null;
  }

  /**
   * 주기적 데이터 플러시
   */
  private startPeriodicFlush() {
    setInterval(() => {
      this.flushLogs();
    }, this.flushInterval);
  }

  /**
   * 에러 로그 기록
   */
  public logError(errorInfo: ErrorInfo) {
    if (!this.isEnabled) return;

    // 큐에 추가
    this.errorQueue.push(errorInfo);

    // 큐 크기 제한
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue.shift();
    }

    // 심각한 에러는 즉시 전송
    if (errorInfo.severity === 'critical') {
      this.flushLogs();
    }

    // 콘솔에도 출력
    console.error('[ErrorLogger]', errorInfo);
  }

  /**
   * 네트워크 에러 로그
   */
  public logNetworkError(url: string, method: string, status: number, message: string) {
    this.logError({
      message: `Network error: ${method} ${url} - ${message}`,
      type: 'network',
      severity: status >= 500 ? 'high' : 'medium',
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        component: 'network',
        additionalData: {
          requestUrl: url,
          method,
          status,
          responseMessage: message
        }
      }
    });
  }

  /**
   * 커스텀 에러 로그
   */
  public logCustomError(
    message: string,
    severity: ErrorInfo['severity'] = 'medium',
    component?: string,
    additionalData?: Record<string, any>
  ) {
    this.logError({
      message,
      type: 'custom',
      severity,
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        component,
        additionalData
      }
    });
  }

  /**
   * 성능 로그 기록
   */
  public logPerformance(performanceInfo: PerformanceInfo) {
    if (!this.isEnabled) return;

    // 큐에 추가
    this.performanceQueue.push(performanceInfo);

    // 큐 크기 제한
    if (this.performanceQueue.length > this.maxQueueSize) {
      this.performanceQueue.shift();
    }

    // 콘솔에도 출력 (느린 작업만)
    if (performanceInfo.isSlowOperation) {
      console.warn('[PerformanceLogger]', performanceInfo);
    }
  }

  /**
   * 컴포넌트 성능 측정
   */
  public measureComponentPerformance(componentName: string, operation: () => void | Promise<void>) {
    const startTime = performance.now();
    
    const measure = () => {
      const duration = performance.now() - startTime;
      this.logPerformance({
        operation: `component-${componentName}`,
        duration,
        component: componentName,
        isSlowOperation: duration > 16.67, // 60fps 기준
        memoryUsage: (performance as any).memory?.usedJSHeapSize
      });
    };

    if (operation instanceof Promise) {
      return operation.finally(measure);
    } else {
      try {
        operation();
      } finally {
        measure();
      }
    }
  }

  /**
   * 로그 플러시 (Discord 전송)
   */
  private async flushLogs() {
    if (!this.discordWebhookUrl || (this.errorQueue.length === 0 && this.performanceQueue.length === 0)) {
      return;
    }

    const payload = {
      embeds: [] as any[]
    };

    // 에러 로그 처리
    if (this.errorQueue.length > 0) {
      const errorEmbed = {
        title: "🚨 Frontend Errors",
        color: 0xFF0000,
        timestamp: new Date().toISOString(),
        fields: this.errorQueue.slice(0, 10).map(error => ({
          name: `${error.type.toUpperCase()} - ${error.severity.toUpperCase()}`,
          value: `\`\`\`${error.message}\`\`\``,
          inline: false
        }))
      };

      if (this.errorQueue.length > 10) {
        errorEmbed.fields.push({
          name: "More Errors",
          value: `+ ${this.errorQueue.length - 10} more errors`,
          inline: false
        });
      }

      payload.embeds.push(errorEmbed);
    }

    // 성능 로그 처리 (느린 작업만)
    const slowOperations = this.performanceQueue.filter(p => p.isSlowOperation);
    if (slowOperations.length > 0) {
      const performanceEmbed = {
        title: "⚡ Performance Issues",
        color: 0xFFAA00,
        timestamp: new Date().toISOString(),
        fields: slowOperations.slice(0, 5).map(perf => ({
          name: perf.operation,
          value: `Duration: ${perf.duration.toFixed(2)}ms${perf.component ? ` | Component: ${perf.component}` : ''}`,
          inline: true
        }))
      };

      payload.embeds.push(performanceEmbed);
    }

    // Discord 전송
    if (payload.embeds.length > 0) {
      try {
        const response = await fetch(this.discordWebhookUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload)
        });

        if (response.ok) {
          // 성공적으로 전송된 로그 제거
          this.errorQueue.length = 0;
          this.performanceQueue.length = 0;
          this.retryCount = 0;
        } else {
          throw new Error(`Discord webhook failed: ${response.status}`);
        }
      } catch (error) {
        console.error('Failed to send logs to Discord:', error);
        
        // 재시도 로직
        if (this.retryCount < this.maxRetries) {
          this.retryCount++;
          setTimeout(() => this.flushLogs(), 5000 * this.retryCount);
        } else {
          // 최대 재시도 후 큐 비우기
          this.errorQueue.length = 0;
          this.performanceQueue.length = 0;
          this.retryCount = 0;
        }
      }
    }
  }

  /**
   * 사용자 컨텍스트 설정
   */
  public setUserContext(userId: string, sessionId?: string) {
    // 이후 모든 로그에 사용자 정보 포함
    const updateContext = (context: ErrorContext = {}) => {
      context.userId = userId;
      context.sessionId = sessionId;
      return context;
    };

    // 기존 큐의 로그에도 사용자 정보 추가
    this.errorQueue.forEach(error => {
      if (error.context) {
        updateContext(error.context);
      }
    });
  }

  /**
   * 에러 로거 비활성화
   */
  public disable() {
    this.isEnabled = false;
  }

  /**
   * 에러 로거 활성화
   */
  public enable() {
    this.isEnabled = true;
  }

  /**
   * 수동 플러시
   */
  public flush() {
    this.flushLogs();
  }
}

// 전역 인스턴스
export const errorLogger = new FrontendErrorLogger();

// React Hook
export function useErrorLogger() {
  const logError = (error: Error, component?: string, additionalData?: Record<string, any>) => {
    errorLogger.logError({
      message: error.message,
      stack: error.stack,
      type: 'custom',
      severity: 'medium',
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        component,
        additionalData
      }
    });
  };

  const logPerformance = (operation: string, duration: number, component?: string) => {
    errorLogger.logPerformance({
      operation,
      duration,
      component,
      isSlowOperation: duration > 100,
      memoryUsage: (performance as any).memory?.usedJSHeapSize
    });
  };

  return { logError, logPerformance };
}

// 유틸리티 함수들
export const withErrorBoundary = (Component: React.ComponentType<any>) => {
  return class extends React.Component {
    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      errorLogger.logError({
        message: error.message,
        stack: error.stack,
        type: 'javascript',
        severity: 'high',
        context: {
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          component: Component.name,
          additionalData: {
            errorInfo: errorInfo.componentStack
          }
        }
      });
    }

    render() {
      return React.createElement(Component, this.props);
    }
  };
};

export const measureAsync = async <T>(
  operation: () => Promise<T>,
  operationName: string,
  component?: string
): Promise<T> => {
  const startTime = performance.now();
  try {
    const result = await operation();
    const duration = performance.now() - startTime;
    
    errorLogger.logPerformance({
      operation: operationName,
      duration,
      component,
      isSlowOperation: duration > 1000,
      memoryUsage: (performance as any).memory?.usedJSHeapSize
    });
    
    return result;
  } catch (error) {
    const duration = performance.now() - startTime;
    
    errorLogger.logError({
      message: `Operation failed: ${operationName}`,
      stack: error instanceof Error ? error.stack : undefined,
      type: 'custom',
      severity: 'high',
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        component,
        additionalData: {
          operationName,
          duration,
          error: error instanceof Error ? error.message : String(error)
        }
      }
    });
    
    throw error;
  }
};