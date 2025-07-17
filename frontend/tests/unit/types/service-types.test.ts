import { describe, test, expect } from 'vitest';
import type { Service } from '~/types/service-types';
import type { BaseListItem } from '~/types/listTypes';
import { serviceToBaseListItem } from '~/types/listTypes';
import { convertPostToService } from '~/types/service-types';

describe('Service와 BaseListItem 호환성 테스트', () => {
  const service: Service = {
    id: '1',
    name: '빠른이사 서비스',
    category: '이사',
    rating: 4.8,
    description: '빠르고 안전한 이사 서비스를 제공합니다.',
    company: {
      name: '빠른이사 서비스',
      contact: '02-3456-7890',
      availableHours: '평일 08:00-20:00',
      description: '빠르고 안전한 이사 서비스를 제공합니다.'
    },
    services: [
      { name: '원룸 이사', price: 150000, description: '원룸 이사 서비스' },
      { name: '투룸 이사', price: 250000, specialPrice: 200000, description: '투룸 이사 서비스' }
    ],
    stats: { views: 89, inquiries: 15, reviews: 42 },
    verified: true,
    contact: {
      phone: '02-3456-7890',
      hours: '평일 08:00-20:00',
      address: '서울시 강남구 xx동',
      email: 'quick@moving.com'
    },
    reviews: [],
    created_at: '2024-01-01T00:00:00Z'
  };

  test('Service를 BaseListItem으로 변환', () => {
    const baseItem = serviceToBaseListItem(service as any);

    // 필수 필드 확인
    expect(baseItem.id).toBe('1');
    expect(baseItem.title).toBe('빠른이사 서비스');
    expect(baseItem.created_at).toBe('2024-01-01T00:00:00Z');
  });

  test('통계 정보 변환', () => {
    const baseItem = serviceToBaseListItem(service as any);

    expect(baseItem.stats).toBeDefined();
    expect(baseItem.stats?.view_count).toBe(89);
    expect(baseItem.stats?.like_count).toBe(13); // 89 * 0.15
    expect(baseItem.stats?.dislike_count).toBe(2); // 89 * 0.03
    expect(baseItem.stats?.comment_count).toBe(42); // reviews 수
    expect(baseItem.stats?.bookmark_count).toBe(10); // 89 * 0.12
  });

  test('통계 정보가 없는 경우', () => {
    const serviceWithoutStats: Service = {
      ...service,
      stats: { views: 0, inquiries: 0, reviews: 0 }
    };

    const baseItem = serviceToBaseListItem(serviceWithoutStats as any);

    expect(baseItem.stats).toBeDefined();
    expect(baseItem.stats?.view_count).toBe(0);
    expect(baseItem.stats?.like_count).toBe(0);
    expect(baseItem.stats?.dislike_count).toBe(0);
    expect(baseItem.stats?.comment_count).toBe(0);
    expect(baseItem.stats?.bookmark_count).toBe(0);
  });

  test('created_at 필드 처리', () => {
    // Service는 항상 created_at을 가지고 있음
    const baseItem = serviceToBaseListItem(service as any);
    expect(baseItem.created_at).toBe('2024-01-01T00:00:00Z');
  });

  test('Post to Service 변환 테스트', () => {
    const mockPost = {
      id: 'test-id',
      content: JSON.stringify({
        company: {
          name: '테스트 서비스',
          contact: '010-1234-5678',
          availableHours: '09:00-18:00',
          description: '테스트 설명'
        },
        services: [
          { name: '테스트 서비스', price: 100000, description: '테스트' }
        ]
      }),
      metadata: { type: 'moving services', category: '이사' },
      stats: { view_count: 50, comment_count: 5 },
      view_count: 50,
      comment_count: 5,
      created_at: '2024-01-01T00:00:00Z'
    };

    const service = convertPostToService(mockPost);
    
    expect(service).not.toBeNull();
    if (service) {
      expect(service.id).toBe('test-id');
      expect(service.name).toBe('테스트 서비스');
      expect(service.category).toBe('이사');
      expect(service.serviceStats?.views).toBe(50);
      expect(service.serviceStats?.reviews).toBe(0); // comment_count는 리뷰가 아니므로 0
    }
  });
});