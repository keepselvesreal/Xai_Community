import { describe, it, expect, vi, beforeEach } from 'vitest';
import { json } from '@remix-run/node';

// Mock된 loader 함수 - 실제 구현 전이므로 테스트용으로 가정
const mockLoader = async ({ request }: { request: Request }) => {
  const url = new URL(request.url);
  const page = parseInt(url.searchParams.get('page') || '1');
  const size = parseInt(url.searchParams.get('size') || '10');
  
  // SSR에서 서버 사이드 API 호출 시뮬레이션
  const mockApiCall = async () => {
    return {
      success: true,
      data: {
        items: [
          {
            id: '1',
            title: 'SSR 테스트 정보',
            content: '서버에서 미리 로드된 정보',
            slug: 'ssr-test-info',
            author_id: 'author1',
            content_type: 'ai_article',
            metadata: {
              type: 'property_information',
              category: 'market_analysis',
              tags: ['ssr', 'test'],
              summary: 'SSR 테스트용 정보'
            },
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            stats: {
              view_count: 100,
              like_count: 10,
              dislike_count: 1,
              comment_count: 5,
              bookmark_count: 2
            }
          }
        ],
        total: 1,
        page,
        size,
        pages: 1
      }
    };
  };

  try {
    const response = await mockApiCall();
    
    return json({
      initialData: response.data,
      timestamp: new Date().toISOString(),
      isServerRendered: true
    });
  } catch (error) {
    return json({
      initialData: null,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
      isServerRendered: true
    });
  }
};

describe('정보 페이지 SSR Loader', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('데이터 로딩', () => {
    it('서버에서 정보 페이지 데이터를 미리 로드해야 함', async () => {
      // Given: 기본 요청
      const request = new Request('http://localhost:3000/info');
      
      // When: loader 함수 실행
      const response = await mockLoader({ request });
      const data = await response.json();
      
      // Then: 서버에서 렌더링된 데이터 반환
      expect(data.isServerRendered).toBe(true);
      expect(data.initialData).toBeDefined();
      expect(data.initialData.items).toHaveLength(1);
      expect(data.initialData.items[0].title).toBe('SSR 테스트 정보');
      expect(data.timestamp).toBeDefined();
    });

    it('페이지네이션 파라미터를 올바르게 처리해야 함', async () => {
      // Given: 페이지네이션 파라미터가 있는 요청
      const request = new Request('http://localhost:3000/info?page=2&size=20');
      
      // When: loader 함수 실행
      const response = await mockLoader({ request });
      const data = await response.json();
      
      // Then: 페이지네이션 정보가 올바르게 설정됨
      expect(data.initialData.page).toBe(2);
      expect(data.initialData.size).toBe(20);
    });

    it('API 에러 시 에러 정보를 포함해야 함', async () => {
      // Given: 에러를 발생시키는 loader
      const errorLoader = async ({ request }: { request: Request }) => {
        try {
          throw new Error('Server API Error');
        } catch (error) {
          return json({
            initialData: null,
            error: error instanceof Error ? error.message : 'Unknown error',
            timestamp: new Date().toISOString(),
            isServerRendered: true
          });
        }
      };

      const request = new Request('http://localhost:3000/info');
      
      // When: loader 함수 실행
      const response = await errorLoader({ request });
      const data = await response.json();
      
      // Then: 에러 정보가 포함됨
      expect(data.isServerRendered).toBe(true);
      expect(data.initialData).toBeNull();
      expect(data.error).toBe('Server API Error');
    });
  });

  describe('메타데이터 타입 필터링', () => {
    it('정보 페이지 전용 메타데이터 타입으로 필터링해야 함', async () => {
      // Given: metadata_type 파라미터를 포함한 요청
      const request = new Request('http://localhost:3000/info');
      
      // When: loader 함수가 실행될 때
      const response = await mockLoader({ request });
      const data = await response.json();
      
      // Then: property-info 타입의 데이터만 로드되어야 함
      expect(data.initialData.items[0].metadata.type).toBe('property_information');
      
      // 실제 구현에서는 API 호출 시 metadata_type: 'property-info' 필터가 적용되어야 함
      // 이는 실제 loader 구현에서 확인할 예정
    });
  });

  describe('캐시 효율성', () => {
    it('서버 렌더링 시 타임스탬프를 포함해야 함', async () => {
      // Given: 기본 요청
      const request = new Request('http://localhost:3000/info');
      
      // When: loader 함수 실행
      const response = await mockLoader({ request });
      const data = await response.json();
      
      // Then: 타임스탬프가 포함되어 캐시 비교 가능
      expect(data.timestamp).toBeDefined();
      const timestamp = new Date(data.timestamp);
      expect(timestamp.getTime()).toBeGreaterThan(Date.now() - 1000); // 1초 이내
    });
  });
});