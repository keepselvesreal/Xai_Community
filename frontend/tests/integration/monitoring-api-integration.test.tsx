/**
 * 모니터링 API 실제 연동 통합 테스트
 * 
 * 실제 백엔드 API와 연동하여 프론트엔드 API 클라이언트 테스트
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import {
  getSystemMetrics,
  getHealthStatus,
  getMonitoringDashboardData,
  getPopularEndpoints,
  getSlowRequests,
  checkMonitoringApiHealth,
  apiCallWithRetry,
} from '~/lib/monitoring-api';

// 실제 백엔드 서버가 실행 중인지 확인
const BACKEND_URL = 'http://localhost:8000';
const TEST_TIMEOUT = 10000; // 10초

describe('Monitoring API Real Integration Tests', () => {
  beforeAll(async () => {
    // 백엔드 서버가 실행 중인지 확인
    try {
      const response = await fetch(`${BACKEND_URL}/health`);
      if (!response.ok) {
        throw new Error('Backend server not responding');
      }
    } catch (error) {
      console.warn('⚠️  Backend server not available. Skipping real integration tests.');
      console.warn('   To run these tests, start the backend server:');
      console.warn('   cd ../backend && python -m uvicorn main:app --reload');
      throw error;
    }
  }, TEST_TIMEOUT);

  describe('Basic API Health Check', () => {
    it('should successfully check monitoring API health', async () => {
      // When: API 헬스 체크 수행
      const healthCheck = await checkMonitoringApiHealth();

      // Then: 성공적인 응답
      expect(healthCheck.isHealthy).toBe(true);
      expect(healthCheck.responseTime).toBeGreaterThan(0);
      expect(healthCheck.error).toBeUndefined();
    }, TEST_TIMEOUT);

    it('should handle API timeout gracefully', async () => {
      // Given: 매우 짧은 타임아웃 (비현실적)
      const originalFetch = global.fetch;
      global.fetch = vi.fn().mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 5000)) // 5초 지연
      );

      try {
        // When: 타임아웃이 예상되는 API 호출
        const healthCheck = await checkMonitoringApiHealth();

        // Then: 타임아웃 처리
        expect(healthCheck.isHealthy).toBe(false);
        expect(healthCheck.error).toBeDefined();
      } finally {
        global.fetch = originalFetch;
      }
    }, TEST_TIMEOUT);
  });

  describe('System Metrics API', () => {
    it('should fetch system metrics successfully', async () => {
      // When: 시스템 메트릭 조회
      const result = await getSystemMetrics();

      // Then: 성공적인 응답
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      if (result.data) {
        expect(result.data).toHaveProperty('endpoints');
        expect(result.data).toHaveProperty('status_codes');
        expect(result.data).toHaveProperty('timestamp');
        expect(typeof result.data.timestamp).toBe('number');
      }
    }, TEST_TIMEOUT);

    it('should handle empty metrics gracefully', async () => {
      // When: 메트릭 조회 (데이터가 없을 수도 있음)
      const result = await getSystemMetrics();

      // Then: 성공적인 응답 구조
      expect(result.success).toBe(true);
      if (result.data) {
        expect(typeof result.data.endpoints).toBe('object');
        expect(typeof result.data.status_codes).toBe('object');
      }
    }, TEST_TIMEOUT);
  });

  describe('Health Status API', () => {
    it('should fetch health status successfully', async () => {
      // When: 헬스 상태 조회
      const result = await getHealthStatus();

      // Then: 성공적인 응답
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      if (result.data) {
        expect(result.data).toHaveProperty('status');
        expect(['healthy', 'warning', 'critical']).toContain(result.data.status);
        expect(result.data).toHaveProperty('total_requests');
        expect(result.data).toHaveProperty('error_rate');
        expect(result.data).toHaveProperty('availability');
        expect(typeof result.data.total_requests).toBe('number');
        expect(typeof result.data.error_rate).toBe('number');
        expect(typeof result.data.availability).toBe('number');
      }
    }, TEST_TIMEOUT);

    it('should have valid health status values', async () => {
      // When: 헬스 상태 조회
      const result = await getHealthStatus();

      // Then: 유효한 값 범위
      if (result.success && result.data) {
        expect(result.data.error_rate).toBeGreaterThanOrEqual(0);
        expect(result.data.error_rate).toBeLessThanOrEqual(1);
        expect(result.data.availability).toBeGreaterThanOrEqual(0);
        expect(result.data.availability).toBeLessThanOrEqual(1);
        expect(result.data.total_requests).toBeGreaterThanOrEqual(0);
      }
    }, TEST_TIMEOUT);
  });

  describe('Popular Endpoints API', () => {
    it('should fetch popular endpoints successfully', async () => {
      // When: 인기 엔드포인트 조회
      const result = await getPopularEndpoints({ limit: 10 });

      // Then: 성공적인 응답
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      if (result.data) {
        expect(Array.isArray(result.data.popular_endpoints)).toBe(true);
        
        // 데이터가 있다면 구조 검증
        if (result.data.popular_endpoints.length > 0) {
          const firstEndpoint = result.data.popular_endpoints[0];
          expect(firstEndpoint).toHaveProperty('endpoint');
          expect(firstEndpoint).toHaveProperty('requests');
          expect(typeof firstEndpoint.endpoint).toBe('string');
          expect(typeof firstEndpoint.requests).toBe('number');
          expect(firstEndpoint.requests).toBeGreaterThan(0);
        }
      }
    }, TEST_TIMEOUT);

    it('should respect limit parameter', async () => {
      // When: 제한된 수의 엔드포인트 조회
      const result = await getPopularEndpoints({ limit: 3 });

      // Then: 제한 수 준수
      if (result.success && result.data) {
        expect(result.data.popular_endpoints.length).toBeLessThanOrEqual(3);
      }
    }, TEST_TIMEOUT);
  });

  describe('Slow Requests API', () => {
    it('should fetch slow requests successfully', async () => {
      // When: 느린 요청 조회
      const result = await getSlowRequests({ limit: 5 });

      // Then: 성공적인 응답
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      if (result.data) {
        expect(Array.isArray(result.data.slow_requests)).toBe(true);
        
        // 데이터가 있다면 구조 검증
        if (result.data.slow_requests.length > 0) {
          const firstRequest = result.data.slow_requests[0];
          expect(firstRequest).toHaveProperty('endpoint');
          expect(firstRequest).toHaveProperty('response_time');
          expect(firstRequest).toHaveProperty('timestamp');
          expect(firstRequest).toHaveProperty('status_code');
          expect(typeof firstRequest.response_time).toBe('number');
          expect(firstRequest.response_time).toBeGreaterThan(0);
        }
      }
    }, TEST_TIMEOUT);
  });

  describe('Dashboard Data API', () => {
    it('should fetch comprehensive dashboard data successfully', async () => {
      // When: 대시보드 데이터 조회
      const result = await getMonitoringDashboardData();

      // Then: 성공적인 응답
      expect(result.success).toBe(true);
      expect(result.data).toBeDefined();
      
      if (result.data) {
        expect(result.data).toHaveProperty('timestamp');
        expect(result.data).toHaveProperty('status');
        expect(result.data).toHaveProperty('data');
        expect(result.data.status).toBe('success');
        
        const dashboardData = result.data.data;
        if (dashboardData) {
          expect(dashboardData).toHaveProperty('metrics');
          expect(dashboardData).toHaveProperty('health');
          expect(dashboardData).toHaveProperty('popular_endpoints');
          expect(dashboardData).toHaveProperty('slow_requests');
        }
      }
    }, TEST_TIMEOUT);

    it('should have consistent timestamp format', async () => {
      // When: 대시보드 데이터 조회
      const result = await getMonitoringDashboardData();

      // Then: 타임스탬프 형식 검증
      if (result.success && result.data) {
        expect(typeof result.data.timestamp).toBe('number');
        expect(result.data.timestamp).toBeGreaterThan(0);
        
        // 타임스탬프가 합리적인 범위인지 확인 (Python time.time()는 초 단위)
        const now = Date.now() / 1000; // 초 단위로 변환
        const oneMinuteAgo = now - 60;
        expect(result.data.timestamp).toBeGreaterThan(oneMinuteAgo);
        expect(result.data.timestamp).toBeLessThanOrEqual(now + 1); // 1초 여유
      }
    }, TEST_TIMEOUT);
  });

  describe('Error Handling and Resilience', () => {
    it('should handle network errors gracefully', async () => {
      // Given: 잘못된 URL 사용
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'test';
      
      // API 클라이언트에서 잘못된 URL 사용하도록 임시 설정
      const originalFetch = global.fetch;
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

      try {
        // When: API 호출
        const result = await getSystemMetrics();

        // Then: 에러 처리
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
        expect(result.error?.message).toContain('Network error');
      } finally {
        global.fetch = originalFetch;
        process.env.NODE_ENV = originalEnv;
      }
    }, TEST_TIMEOUT);

    it('should retry failed requests with apiCallWithRetry', async () => {
      // Given: 처음에는 실패, 두 번째에는 성공하는 Mock
      let callCount = 0;
      const originalFetch = global.fetch;
      global.fetch = vi.fn().mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Temporary failure'));
        }
        return Promise.resolve(new Response(JSON.stringify({
          endpoints: {},
          status_codes: {},
          timestamp: Date.now()
        }), { status: 200 }));
      });

      try {
        // When: 재시도 기능 사용
        const result = await apiCallWithRetry(() => getSystemMetrics(), 3, 100);

        // Then: 재시도 후 성공
        expect(result.success).toBe(true);
        expect(callCount).toBe(2); // 첫 번째 실패, 두 번째 성공
      } finally {
        global.fetch = originalFetch;
      }
    }, TEST_TIMEOUT);

    it('should handle HTTP error status codes', async () => {
      // Given: 500 에러 응답
      const originalFetch = global.fetch;
      global.fetch = vi.fn().mockResolvedValue(
        new Response('Internal Server Error', { status: 500 })
      );

      try {
        // When: API 호출
        const result = await getSystemMetrics();

        // Then: 에러 처리
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
        expect(result.error?.message).toContain('500');
      } finally {
        global.fetch = originalFetch;
      }
    }, TEST_TIMEOUT);
  });

  describe('Performance and Response Time', () => {
    it('should complete API calls within reasonable time', async () => {
      // Given: 응답 시간 측정 시작
      const startTime = performance.now();

      // When: 여러 API 동시 호출
      const promises = [
        getSystemMetrics(),
        getHealthStatus(),
        getPopularEndpoints(),
        getSlowRequests(),
      ];

      const results = await Promise.all(promises);
      const endTime = performance.now();
      const totalTime = endTime - startTime;

      // Then: 합리적인 응답 시간
      expect(totalTime).toBeLessThan(5000); // 5초 이내
      
      // 모든 API 호출이 성공했는지 확인
      results.forEach(result => {
        expect(result.success).toBe(true);
      });
    }, TEST_TIMEOUT);

    it('should handle concurrent API calls correctly', async () => {
      // Given: 동시에 같은 API 여러 번 호출
      const concurrentCalls = Array(5).fill(null).map(() => getSystemMetrics());

      // When: 동시 호출 실행
      const results = await Promise.all(concurrentCalls);

      // Then: 모든 호출이 성공
      results.forEach(result => {
        expect(result.success).toBe(true);
      });

      // 응답 데이터 구조가 일관적인지 확인
      const successfulResults = results.filter(r => r.success && r.data);
      if (successfulResults.length > 1) {
        const firstResult = successfulResults[0].data!;
        successfulResults.forEach(result => {
          expect(result.data).toHaveProperty('endpoints');
          expect(result.data).toHaveProperty('status_codes');
          expect(result.data).toHaveProperty('timestamp');
        });
      }
    }, TEST_TIMEOUT);
  });

  afterAll(async () => {
    // 테스트 완료 후 정리 작업 (필요시)
    console.log('✅ Real API integration tests completed');
  });
});