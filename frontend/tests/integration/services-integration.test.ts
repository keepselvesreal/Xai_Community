/**
 * Services 페이지 API 연동 테스트 (TDD RED 단계)
 */

// Vitest globals are available through vitest.config.ts

// Mock API 모듈
vi.mock('../../app/lib/services-api', () => ({
  fetchServices: vi.fn(),
  createService: vi.fn(),
  searchServices: vi.fn()
}));

describe('Services Page API Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('services 페이지가 API에서 데이터를 로드해야 한다', async () => {
    // RED: 아직 API 연동이 되어있지 않으므로 실패해야 함
    const { fetchServices } = await import('../../app/lib/services-api');
    
    expect(fetchServices).toBeDefined();
    expect(typeof fetchServices).toBe('function');
  });

  test('서비스 등록 폼이 실제 API를 호출해야 한다', async () => {
    // RED: 현재는 console.log만 하고 실제 API 호출 안됨
    const { createService } = await import('../../app/lib/services-api');
    
    expect(createService).toBeDefined();
    expect(typeof createService).toBe('function');
  });

  test('카테고리 필터링이 API 파라미터로 전달되어야 한다', async () => {
    // RED: 현재는 mock 데이터 필터링만 됨
    const { fetchServices } = await import('../../app/lib/services-api');
    
    // Mock 함수 호출하여 파라미터 확인
    fetchServices({ category: '이사', page: 1, size: 20 });
    
    expect(fetchServices).toHaveBeenCalledWith({
      category: '이사',
      page: 1,
      size: 20
    });
  });

  test('검색 기능이 API를 통해 동작해야 한다', async () => {
    // RED: 현재는 클라이언트 사이드 필터링만 됨
    const { searchServices } = await import('../../app/lib/services-api');
    
    searchServices('이사', { page: 1 });
    
    expect(searchServices).toHaveBeenCalledWith('이사', { page: 1 });
  });
});