/**
 * 서비스 API 함수 테스트 (TDD RED 단계)
 */

// Vitest globals are available through vitest.config.ts

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Services API Functions', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllMocks();
  });

  test('fetchServices가 올바른 API 엔드포인트를 호출해야 한다', async () => {
    const { fetchServices } = await import('./services-api');
    
    // Mock successful API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      text: () => Promise.resolve(JSON.stringify({
        items: [],
        total: 0,
        page: 1,
        size: 20,
        pages: 1
      }))
    });

    await fetchServices({ page: 1, size: 20 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/posts/'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    );
  });

  test('fetchServicesByCategory가 카테고리 필터를 적용해야 한다', async () => {
    const { fetchServicesByCategory } = await import('./services-api');
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      text: () => Promise.resolve(JSON.stringify({ items: [], total: 0, page: 1, size: 20, pages: 1 }))
    });

    await fetchServicesByCategory('이사', { page: 1 });

    // fetchServices를 내부적으로 호출하는지 확인
    expect(mockFetch).toHaveBeenCalled();
  });

  test('createService가 올바른 POST 요청을 생성해야 한다', async () => {
    const { createService } = await import('./services-api');
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      text: () => Promise.resolve(JSON.stringify({
        id: '1',
        title: '테스트 업체',
        content: '{}',
        slug: 'test-service'
      }))
    });

    const serviceData = {
      servicePost: {
        company: {
          name: '테스트 업체',
          contact: '02-1234-5678',
          availableHours: '09:00-18:00',
          description: '테스트 설명'
        },
        services: [
          { name: '테스트 서비스', price: 100000 }
        ]
      },
      category: '이사' as const
    };

    await createService(serviceData);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/posts'),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('테스트 업체')
      })
    );
  });

  test('searchServices가 검색 쿼리를 포함해야 한다', async () => {
    const { searchServices } = await import('./services-api');
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      text: () => Promise.resolve(JSON.stringify({ items: [], total: 0, page: 1, size: 20, pages: 1 }))
    });

    await searchServices('이사', { page: 1 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('search='),
      expect.any(Object)
    );
  });

  test('getServiceById가 특정 ID로 서비스를 조회해야 한다', async () => {
    const { getServiceById } = await import('./services-api');
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      headers: new Map([['content-type', 'application/json']]),
      text: () => Promise.resolve(JSON.stringify({
        id: 'test-id',
        title: '테스트 서비스',
        content: '{}'
      }))
    });

    await getServiceById('test-id');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/posts/test-id'),
      expect.any(Object)
    );
  });
});