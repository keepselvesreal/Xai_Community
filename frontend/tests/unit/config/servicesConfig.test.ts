import { describe, test, expect, vi } from 'vitest';
import { servicesConfig } from '~/config/pageConfigs';
import type { MockService } from '~/types';

describe('servicesConfig 설정 테스트', () => {
  test('기본 설정 구조', () => {
    expect(servicesConfig.title).toBe('입주업체서비스');
    expect(servicesConfig.writeButtonText).toBe('📝 업체 등록');
    expect(servicesConfig.writeButtonLink).toBe('/services/write');
    expect(servicesConfig.searchPlaceholder).toBe('서비스 검색...');
  });

  test('API 설정', () => {
    expect(servicesConfig.apiEndpoint).toBe('/api/services');
    expect(servicesConfig.apiFilters).toEqual({
      page: 1,
      size: 50
    });
  });

  test('카테고리 설정', () => {
    expect(servicesConfig.categories).toHaveLength(4);
    expect(servicesConfig.categories).toEqual([
      { value: 'all', label: '전체' },
      { value: 'moving', label: '이사' },
      { value: 'cleaning', label: '청소' },
      { value: 'aircon', label: '에어컨' }
    ]);
  });

  test('정렬 옵션', () => {
    expect(servicesConfig.sortOptions).toHaveLength(5);
    expect(servicesConfig.sortOptions).toEqual([
      { value: 'latest', label: '최신순' },
      { value: 'views', label: '조회수' },
      { value: 'saves', label: '저장수' },
      { value: 'reviews', label: '후기수' },
      { value: 'inquiries', label: '문의수' }
    ]);
  });

  test('레이아웃 설정', () => {
    expect(servicesConfig.cardLayout).toBe('grid');
  });

  test('필터 함수', () => {
    const mockService: MockService = {
      id: 1,
      name: '테스트 서비스',
      category: '이사',
      rating: 4.5,
      description: '테스트 설명',
      services: [],
      stats: { views: 100, inquiries: 10, reviews: 5 },
      verified: true,
      contact: {
        phone: '010-1234-5678',
        hours: '09:00-18:00',
        address: '서울',
        email: 'test@test.com'
      },
      reviews: []
    };

    // 전체 카테고리
    expect(servicesConfig.filterFn(mockService, 'all', '')).toBe(true);
    
    // 일치하는 카테고리
    expect(servicesConfig.filterFn(mockService, 'moving', '')).toBe(true);
    
    // 일치하지 않는 카테고리
    expect(servicesConfig.filterFn(mockService, 'cleaning', '')).toBe(false);
    
    // 검색어 테스트
    expect(servicesConfig.filterFn(mockService, 'all', '테스트')).toBe(true);
    expect(servicesConfig.filterFn(mockService, 'all', '없는단어')).toBe(false);
  });

  test('정렬 함수', () => {
    const service1: MockService = {
      id: 1,
      name: '서비스1',
      category: '이사',
      rating: 4.5,
      description: '',
      services: [],
      stats: { views: 100, inquiries: 10, reviews: 5 },
      verified: true,
      contact: { phone: '', hours: '', address: '', email: '' },
      reviews: []
    };

    const service2: MockService = {
      id: 2,
      name: '서비스2',
      category: '청소',
      rating: 4.0,
      description: '',
      services: [],
      stats: { views: 200, inquiries: 5, reviews: 10 },
      verified: false,
      contact: { phone: '', hours: '', address: '', email: '' },
      reviews: []
    };

    // 최신순 (ID가 높은 것이 최신)
    expect(servicesConfig.sortFn(service1, service2, 'latest')).toBeGreaterThan(0);
    
    // 조회수순
    expect(servicesConfig.sortFn(service1, service2, 'views')).toBeGreaterThan(0);
    
    // 문의수순
    expect(servicesConfig.sortFn(service1, service2, 'inquiries')).toBeLessThan(0);
    
    // 후기수순
    expect(servicesConfig.sortFn(service1, service2, 'reviews')).toBeGreaterThan(0);
  });

  test('renderCard 함수 존재 확인', () => {
    expect(servicesConfig.renderCard).toBeDefined();
    expect(typeof servicesConfig.renderCard).toBe('function');
  });
});