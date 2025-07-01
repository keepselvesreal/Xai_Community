/**
 * End-to-End 서비스 플로우 테스트 (TDD RED 단계)
 */

// Vitest globals are available through vitest.config.ts

// Mock all external dependencies
vi.mock('../../app/lib/services-api');
vi.mock('../../app/contexts/AuthContext');
vi.mock('../../app/contexts/NotificationContext');

describe('Services Complete Flow E2E Test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('전체 서비스 등록 → 목록 조회 → 필터링 → 검색 플로우', async () => {
    // 1. 서비스 등록
    const { createService } = await import('../../app/lib/services-api');
    const { convertFormDataToServicePost } = await import('../../app/types/service-types');
    
    const mockFormData = {
      companyName: '테스트 이사업체',
      contact: '02-1234-5678',
      availableHours: '09:00-18:00',
      description: '안전하고 빠른 이사 서비스'
    };
    
    const mockServices = [
      {
        serviceName: '원룸 이사',
        price: '150000',
        specialPrice: '130000',
        hasSpecialPrice: true
      },
      {
        serviceName: '투룸 이사',
        price: '300000',
        hasSpecialPrice: false
      }
    ];

    // 폼 데이터를 ServicePost로 변환
    const servicePost = convertFormDataToServicePost(mockFormData, mockServices);
    
    expect(servicePost.company.name).toBe('테스트 이사업체');
    expect(servicePost.services).toHaveLength(2);
    expect(servicePost.services[0].specialPrice).toBe(130000);
    expect(servicePost.services[1].specialPrice).toBeUndefined();

    // 2. 서비스 목록 조회
    const { fetchServices } = await import('../../app/lib/services-api');
    
    // Mock API 응답
    vi.mocked(fetchServices).mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: '1',
            title: '테스트 이사업체',
            content: JSON.stringify(servicePost),
            metadata: { category: '이사' },
            created_at: new Date().toISOString()
          }
        ],
        total: 1,
        page: 1,
        size: 20,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const servicesResponse = await fetchServices({ page: 1, size: 20 });
    expect(servicesResponse.success).toBe(true);
    expect(servicesResponse.data?.items).toHaveLength(1);

    // 3. 카테고리 필터링
    const { fetchServicesByCategory } = await import('../../app/lib/services-api');
    
    vi.mocked(fetchServicesByCategory).mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: '1',
            title: '테스트 이사업체',
            content: JSON.stringify(servicePost),
            metadata: { category: '이사' },
            created_at: new Date().toISOString()
          }
        ],
        total: 1,
        page: 1,
        size: 20,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const categoryResponse = await fetchServicesByCategory('이사', { page: 1 });
    expect(categoryResponse.success).toBe(true);
    expect(categoryResponse.data?.items).toHaveLength(1);

    // 4. 검색 기능
    const { searchServices } = await import('../../app/lib/services-api');
    
    vi.mocked(searchServices).mockResolvedValue({
      success: true,
      data: {
        items: [
          {
            id: '1',
            title: '테스트 이사업체',
            content: JSON.stringify(servicePost),
            metadata: { category: '이사' },
            created_at: new Date().toISOString()
          }
        ],
        total: 1,
        page: 1,
        size: 20,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const searchResponse = await searchServices('이사', { page: 1 });
    expect(searchResponse.success).toBe(true);
    expect(searchResponse.data?.items).toHaveLength(1);
  });

  test('서비스 데이터 변환 및 파싱 무결성', async () => {
    const { 
      serializeServicePost, 
      parseServicePost, 
      convertServicePostToMockService 
    } = await import('../../app/types/service-types');

    // 원본 서비스 데이터
    const originalServicePost = {
      company: {
        name: '믿을만한 청소업체',
        contact: '02-9876-5432',
        availableHours: '24시간',
        description: '전문 청소 서비스'
      },
      services: [
        {
          name: '일반 청소',
          price: 50000,
          specialPrice: 40000,
          description: '기본 청소 서비스'
        }
      ]
    };

    // 직렬화 → 파싱 테스트
    const serialized = serializeServicePost(originalServicePost);
    const parsed = parseServicePost(serialized);
    
    expect(parsed).toEqual(originalServicePost);

    // MockService 변환 테스트
    const mockService = convertServicePostToMockService(originalServicePost, 1, '청소');
    
    expect(mockService.name).toBe('믿을만한 청소업체');
    expect(mockService.category).toBe('청소');
    expect(mockService.services[0].price).toBe('50,000원');
    expect(mockService.services[0].originalPrice).toBe('40,000원');
  });

  test('API 에러 처리 및 Fallback 동작', async () => {
    const { fetchServices } = await import('../../app/lib/services-api');
    
    // API 실패 시나리오
    vi.mocked(fetchServices).mockResolvedValue({
      success: false,
      error: 'Network error',
      timestamp: new Date().toISOString()
    });

    const failedResponse = await fetchServices();
    expect(failedResponse.success).toBe(false);
    expect(failedResponse.error).toBe('Network error');

    // Fallback 데이터 사용 로직 테스트는 컴포넌트 레벨에서 처리
  });
});