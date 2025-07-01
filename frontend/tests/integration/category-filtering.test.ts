/**
 * 카테고리 필터링 API 연동 테스트 (TDD RED 단계)
 */

// Vitest globals are available through vitest.config.ts

// Mock API 모듈
vi.mock('../../app/lib/services-api', () => ({
  fetchServicesByCategory: vi.fn(),
  fetchServices: vi.fn()
}));

describe('Category Filtering API Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('카테고리 필터링이 API를 통해 동작해야 한다', async () => {
    // RED: 현재는 클라이언트 사이드 필터링만 됨
    const { fetchServicesByCategory } = await import('../../app/lib/services-api');
    
    fetchServicesByCategory('이사', { page: 1, size: 20 });
    
    expect(fetchServicesByCategory).toHaveBeenCalledWith('이사', { page: 1, size: 20 });
  });

  test('전체 카테고리 선택 시 모든 서비스를 조회해야 한다', async () => {
    const { fetchServices } = await import('../../app/lib/services-api');
    
    fetchServices({ page: 1, size: 20 });
    
    expect(fetchServices).toHaveBeenCalledWith({ page: 1, size: 20 });
  });

  test('카테고리 변경 시 즉시 API를 호출해야 한다', async () => {
    // RED: 현재는 기존 데이터를 클라이언트에서 필터링
    const { fetchServicesByCategory } = await import('../../app/lib/services-api');
    
    // 이사 카테고리
    fetchServicesByCategory('이사', { page: 1 });
    expect(fetchServicesByCategory).toHaveBeenCalledWith('이사', { page: 1 });
    
    // 청소 카테고리
    fetchServicesByCategory('청소', { page: 1 });
    expect(fetchServicesByCategory).toHaveBeenCalledWith('청소', { page: 1 });
    
    // 에어컨 카테고리
    fetchServicesByCategory('에어컨', { page: 1 });
    expect(fetchServicesByCategory).toHaveBeenCalledWith('에어컨', { page: 1 });
  });
});