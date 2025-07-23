/**
 * API 클라이언트 유틸리티 (에러 리포팅 통합)
 * 
 * 작업 시간: 2025-07-23 14:45:00 KST
 * 작업 버전: v1.0.0
 * 주요 컴포넌트들:
 * - ApiClient: 에러 리포팅이 통합된 API 클라이언트 클래스
 * - ApiRequestConfig: API 요청 설정 인터페이스
 * 
 * 주요 함수들:
 * - request: 공통 API 요청 메소드 (line 45-120)
 * - get, post, put, delete: HTTP 메소드별 래퍼 함수들 (line 130-160)
 * 
 * 관련 파일들:
 * - app/utils/errorReporter.ts: 에러 리포팅 유틸리티
 * - backend/nadle_backend/routers/client_errors.py: 서버 측 에러 수집 API
 */

import { reportNetworkError, reportTimeoutError } from './errorReporter';

interface ApiRequestConfig {
  timeout?: number;
  retries?: number;
  componentName?: string;
  action?: string;
  additionalInfo?: Record<string, any>;
}

interface ApiResponse<T = any> {
  data: T;
  status: number;
  headers: Headers;
}

class ApiClient {
  private baseURL: string;
  private defaultTimeout: number;

  constructor(baseURL: string = '', defaultTimeout: number = 10000) {
    this.baseURL = baseURL;
    this.defaultTimeout = defaultTimeout;
  }

  /**
   * 공통 API 요청 메소드 (에러 리포팅 통합)
   */
  async request<T = any>(
    endpoint: string,
    options: RequestInit & ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      timeout = this.defaultTimeout,
      retries = 0,
      componentName,
      action,
      additionalInfo,
      ...fetchOptions
    } = options;

    const url = `${this.baseURL}${endpoint}`;
    const startTime = Date.now();

    // AbortController로 타임아웃 처리
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // HTTP 에러 상태 처리
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        
        // 네트워크 에러로 리포팅
        await reportNetworkError(error, url, response.status, {
          componentName,
          action,
          additionalInfo: {
            ...additionalInfo,
            method: fetchOptions.method || 'GET',
            requestBody: fetchOptions.body,
            responseHeaders: Object.fromEntries(response.headers.entries()),
          }
        });

        throw error;
      }

      const data = await response.json();

      return {
        data,
        status: response.status,
        headers: response.headers,
      };

    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        // 타임아웃 에러 처리
        if (error.name === 'AbortError') {
          const timeoutDuration = Date.now() - startTime;
          await reportTimeoutError(url, timeoutDuration, {
            componentName,
            action,
            additionalInfo: {
              ...additionalInfo,
              method: fetchOptions.method || 'GET',
              requestBody: fetchOptions.body,
              expectedTimeout: timeout,
            }
          });

          throw new Error(`Request timeout after ${timeout}ms`);
        }

        // 네트워크 에러 처리
        if (error.message.includes('fetch')) {
          await reportNetworkError(error, url, undefined, {
            componentName,
            action,
            additionalInfo: {
              ...additionalInfo,
              method: fetchOptions.method || 'GET',
              requestBody: fetchOptions.body,
              isNetworkError: true,
            }
          });
        }
      }

      // 재시도 로직
      if (retries > 0) {
        console.warn(`API request failed, retrying... (${retries} attempts left)`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1초 대기
        
        return this.request(endpoint, {
          ...options,
          retries: retries - 1,
        });
      }

      throw error;
    }
  }

  /**
   * GET 요청
   */
  async get<T = any>(
    endpoint: string,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'GET',
    });
  }

  /**
   * POST 요청
   */
  async post<T = any>(
    endpoint: string,
    data?: any,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...config,
      },
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT 요청
   */
  async put<T = any>(
    endpoint: string,
    data?: any,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...config,
      },
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE 요청
   */
  async delete<T = any>(
    endpoint: string,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'DELETE',
    });
  }
}

// 기본 API 클라이언트 인스턴스
export const apiClient = new ApiClient();

// 인증이 필요한 요청을 위한 헬퍼 함수
export const createAuthenticatedClient = (token: string) => {
  const client = new ApiClient();
  
  // 원본 request 메소드를 래핑하여 Authorization 헤더 추가
  const originalRequest = client.request.bind(client);
  client.request = (endpoint: string, options: RequestInit & ApiRequestConfig = {}) => {
    return originalRequest(endpoint, {
      ...options,
      headers: {
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });
  };

  return client;
};

export default apiClient;