/**
 * 데이터 변환 유틸리티 함수 테스트 (TDD RED 단계)
 */

// Vitest globals are available through vitest.config.ts

describe('Service Data Conversion Utilities', () => {
  test('convertMockServiceToServicePost가 올바르게 변환해야 한다', async () => {
    const { convertMockServiceToServicePost } = await import('../../app/types/service-types');
    
    const mockService = {
      id: 1,
      name: "빠른이사 서비스",
      category: "이사",
      rating: 4.8,
      description: "빠르고 안전한 이사 서비스를 제공합니다.",
      services: [
        { name: "원룸 이사", price: "150,000원", description: "원룸 이사 서비스" },
        { name: "투룸 이사", price: "300,000원", originalPrice: "250,000원", description: "투룸 이사 서비스" }
      ],
      stats: { views: 89, inquiries: 15, reviews: 42 },
      verified: true,
      contact: {
        phone: "02-3456-7890",
        hours: "평일 08:00-20:00", 
        address: "서울시 강남구 xx동",
        email: "quick@moving.com"
      },
      reviews: []
    };

    const result = convertMockServiceToServicePost(mockService);
    
    expect(result.company.name).toBe("빠른이사 서비스");
    expect(result.company.contact).toBe("02-3456-7890");
    expect(result.company.availableHours).toBe("평일 08:00-20:00");
    expect(result.company.description).toBe("빠르고 안전한 이사 서비스를 제공합니다.");
    
    expect(result.services).toHaveLength(2);
    expect(result.services[0].name).toBe("원룸 이사");
    expect(result.services[0].price).toBe(150000);
    expect(result.services[0].specialPrice).toBeUndefined();
    
    expect(result.services[1].name).toBe("투룸 이사");
    expect(result.services[1].price).toBe(300000);
    expect(result.services[1].specialPrice).toBe(250000);
  });

  test('convertServicePostToMockService가 올바르게 역변환해야 한다', async () => {
    const { convertServicePostToMockService } = await import('../../app/types/service-types');
    
    const servicePost = {
      company: {
        name: "시원한 에어컨 서비스",
        contact: "02-9876-5432",
        availableHours: "평일 09:00-18:00",
        description: "에어컨 전문 설치, 수리, 청소 서비스를 제공합니다."
      },
      services: [
        {
          name: "에어컨 청소",
          price: 80000,
          description: "에어컨 전문 청소"
        },
        {
          name: "에어컨 설치", 
          price: 150000,
          specialPrice: 120000,
          description: "에어컨 설치 서비스"
        }
      ]
    };

    const result = convertServicePostToMockService(servicePost, 4, "에어컨");
    
    expect(result.id).toBe(4);
    expect(result.name).toBe("시원한 에어컨 서비스");
    expect(result.category).toBe("에어컨");
    expect(result.description).toBe("에어컨 전문 설치, 수리, 청소 서비스를 제공합니다.");
    
    expect(result.contact.phone).toBe("02-9876-5432");
    expect(result.contact.hours).toBe("평일 09:00-18:00");
    
    expect(result.services).toHaveLength(2);
    expect(result.services[0].name).toBe("에어컨 청소");
    expect(result.services[0].price).toBe("80,000원");
    expect(result.services[0].originalPrice).toBeUndefined();
    
    expect(result.services[1].name).toBe("에어컨 설치");
    expect(result.services[1].price).toBe("150,000원");
    expect(result.services[1].originalPrice).toBe("120,000원");
  });

  test('가격 문자열 파싱이 올바르게 동작해야 한다', async () => {
    const { convertMockServiceToServicePost } = await import('../../app/types/service-types');
    
    const mockService = {
      id: 1,
      name: "테스트",
      category: "이사",
      rating: 4.0,
      description: "테스트",
      services: [
        { name: "서비스1", price: "100,000원~", description: "" },
        { name: "서비스2", price: "원룸 250,000원", description: "" },
        { name: "서비스3", price: "abc123,456원def", description: "" }
      ],
      stats: { views: 0, inquiries: 0, reviews: 0 },
      verified: false,
      contact: { phone: "", hours: "", address: "", email: "" },
      reviews: []
    };

    const result = convertMockServiceToServicePost(mockService);
    
    expect(result.services[0].price).toBe(100000);  // "100,000원~" -> 100000
    expect(result.services[1].price).toBe(250000);  // "원룸 250,000원" -> 250000  
    expect(result.services[2].price).toBe(123456);  // "abc123,456원def" -> 123456
  });

  test('빈 서비스 배열이나 잘못된 데이터를 처리해야 한다', async () => {
    const { convertMockServiceToServicePost } = await import('../../app/types/service-types');
    
    const mockServiceWithEmptyServices = {
      id: 1,
      name: "테스트",
      category: "이사",
      rating: 4.0,
      description: "테스트",
      services: [],
      stats: { views: 0, inquiries: 0, reviews: 0 },
      verified: false,
      contact: { phone: "02-1234-5678", hours: "09:00-18:00", address: "", email: "" },
      reviews: []
    };

    const result = convertMockServiceToServicePost(mockServiceWithEmptyServices);
    
    expect(result.services).toHaveLength(0);
    expect(result.company.name).toBe("테스트");
  });

  test('숫자가 없는 가격 문자열의 경우 0으로 설정되어야 한다', async () => {
    const { convertMockServiceToServicePost } = await import('../../app/types/service-types');
    
    const mockService = {
      id: 1,
      name: "테스트",
      category: "이사", 
      rating: 4.0,
      description: "테스트",
      services: [
        { name: "서비스1", price: "상담후결정", description: "" },
        { name: "서비스2", price: "문의바람", description: "" }
      ],
      stats: { views: 0, inquiries: 0, reviews: 0 },
      verified: false,
      contact: { phone: "02-1234-5678", hours: "09:00-18:00", address: "", email: "" },
      reviews: []
    };

    const result = convertMockServiceToServicePost(mockService);
    
    expect(result.services[0].price).toBe(0);  // "상담후결정" -> 0
    expect(result.services[1].price).toBe(0);  // "문의바람" -> 0
  });

  test('카테고리 매핑 함수들이 올바르게 동작해야 한다', async () => {
    const { mapCategoryToServiceCategory, mapServiceCategoryToEnglish } = await import('../../app/types/service-types');
    
    // 영문 -> 한글
    expect(mapCategoryToServiceCategory('moving')).toBe('이사');
    expect(mapCategoryToServiceCategory('cleaning')).toBe('청소');
    expect(mapCategoryToServiceCategory('aircon')).toBe('에어컨');
    
    // 한글 -> 한글 (동일값)
    expect(mapCategoryToServiceCategory('이사')).toBe('이사');
    expect(mapCategoryToServiceCategory('청소')).toBe('청소');
    expect(mapCategoryToServiceCategory('에어컨')).toBe('에어컨');
    
    // 잘못된 카테고리
    expect(mapCategoryToServiceCategory('invalid')).toBeUndefined();
    
    // 한글 -> 영문
    expect(mapServiceCategoryToEnglish('이사')).toBe('moving');
    expect(mapServiceCategoryToEnglish('청소')).toBe('cleaning');
    expect(mapServiceCategoryToEnglish('에어컨')).toBe('aircon');
  });

  test('폼 데이터를 ServicePost로 변환해야 한다', async () => {
    const { convertFormDataToServicePost } = await import('../../app/types/service-types');
    
    const formData = {
      companyName: "  테스트 업체  ",
      contact: "  02-1234-5678  ",
      availableHours: "  09:00-18:00  ",
      description: "  테스트 설명  "
    };
    
    const services = [
      {
        serviceName: "  원룸 이사  ",
        price: "150000",
        specialPrice: "120000",
        hasSpecialPrice: true
      },
      {
        serviceName: "투룸 이사",
        price: "300000",
        hasSpecialPrice: false
      },
      {
        serviceName: "", // 빈 서비스명 - 필터링되어야 함
        price: "100000"
      }
    ];

    const result = convertFormDataToServicePost(formData, services);
    
    // 공백 제거 확인
    expect(result.company.name).toBe("테스트 업체");
    expect(result.company.contact).toBe("02-1234-5678");
    expect(result.company.availableHours).toBe("09:00-18:00");
    expect(result.company.description).toBe("테스트 설명");
    
    // 유효한 서비스만 포함되어야 함
    expect(result.services).toHaveLength(2);
    
    expect(result.services[0].name).toBe("원룸 이사");
    expect(result.services[0].price).toBe(150000);
    expect(result.services[0].specialPrice).toBe(120000);
    
    expect(result.services[1].name).toBe("투룸 이사");
    expect(result.services[1].price).toBe(300000);
    expect(result.services[1].specialPrice).toBeUndefined();
  });

  test('ServicePost 유틸리티 함수들이 올바르게 동작해야 한다', async () => {
    const { getServiceCount, getMinPrice, getMaxPrice, getSpecialPriceCount } = await import('../../app/types/service-types');
    
    const servicePost = {
      company: {
        name: "테스트 업체",
        contact: "02-1234-5678",
        availableHours: "09:00-18:00",
        description: "테스트"
      },
      services: [
        { name: "서비스1", price: 100000 },
        { name: "서비스2", price: 200000, specialPrice: 180000 },
        { name: "서비스3", price: 50000, specialPrice: 40000 }
      ]
    };

    expect(getServiceCount(servicePost)).toBe(3);
    expect(getMinPrice(servicePost)).toBe(40000); // 특가 포함 최저가
    expect(getMaxPrice(servicePost)).toBe(200000); // 일반가 최고가
    expect(getSpecialPriceCount(servicePost)).toBe(2); // 특가가 있는 서비스 2개
  });

  test('빈 서비스 배열에서 유틸리티 함수들이 올바르게 동작해야 한다', async () => {
    const { getServiceCount, getMinPrice, getMaxPrice, getSpecialPriceCount } = await import('../../app/types/service-types');
    
    const emptyServicePost = {
      company: {
        name: "테스트 업체",
        contact: "02-1234-5678",
        availableHours: "09:00-18:00",
        description: "테스트"
      },
      services: []
    };

    expect(getServiceCount(emptyServicePost)).toBe(0);
    expect(getMinPrice(emptyServicePost)).toBe(0);
    expect(getMaxPrice(emptyServicePost)).toBe(0);
    expect(getSpecialPriceCount(emptyServicePost)).toBe(0);
  });
});