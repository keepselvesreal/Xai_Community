import { describe, test, expect } from 'vitest';
import type { Post, MockService, MockTip } from '~/types';
import type { BaseListItem, ItemStats, ListPageConfig } from '~/types/listTypes';

// 타입 호환성 테스트를 위한 헬퍼 함수
function isBaseListItem(item: any): item is BaseListItem {
  return (
    typeof item.id === 'string' &&
    typeof item.title === 'string' &&
    typeof item.created_at === 'string' &&
    (item.stats === undefined || typeof item.stats === 'object')
  );
}

describe('BaseListItem 인터페이스', () => {
  test('Post 타입과 호환성', () => {
    const post: Post = {
      id: '1',
      title: '테스트 게시글',
      content: '내용',
      slug: 'test-post',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '입주 정보'
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
      stats: {
        view_count: 100,
        like_count: 20,
        dislike_count: 2,
        comment_count: 15,
        bookmark_count: 10
      }
    };

    // Post가 BaseListItem의 요구사항을 충족하는지 확인
    expect(isBaseListItem(post)).toBe(true);
    expect(post.id).toBeDefined();
    expect(post.title).toBeDefined();
    expect(post.created_at).toBeDefined();
    expect(post.stats).toBeDefined();
  });

  test('MockService 타입과 호환성', () => {
    const service: MockService = {
      id: 1,
      name: '빠른이사 서비스', // name을 title로 매핑 필요
      category: '이사',
      rating: 4.8,
      description: '빠르고 안전한 이사 서비스',
      services: [],
      stats: {
        views: 100,
        inquiries: 10,
        reviews: 20
      },
      verified: true,
      contact: {
        phone: '02-1234-5678',
        hours: '평일 09:00-18:00',
        address: '서울시 강남구',
        email: 'test@example.com'
      },
      reviews: []
    };

    // MockService를 BaseListItem으로 변환하는 매핑 함수 테스트
    const mappedService: BaseListItem = {
      id: service.id.toString(),
      title: service.name, // name을 title로 매핑
      created_at: new Date().toISOString(), // 생성 시간 추가 필요
      stats: {
        view_count: service.stats.views,
        like_count: Math.floor(service.stats.views * 0.15),
        dislike_count: Math.floor(service.stats.views * 0.03),
        comment_count: service.stats.reviews,
        bookmark_count: Math.floor(service.stats.views * 0.12)
      }
    };

    expect(isBaseListItem(mappedService)).toBe(true);
  });

  test('MockTip 타입과 호환성', () => {
    const tip: MockTip = {
      id: 1,
      title: '겨울철 실내 화분 관리법',
      content: '실내 온도와 습도 조절을 통한 효과적인 식물 관리',
      expert_name: '김○○',
      expert_title: '원예 전문가',
      created_at: '2일 전',
      category: '원예',
      tags: ['#실내화분', '#겨울관리'],
      views_count: 245,
      likes_count: 32,
      saves_count: 18,
      is_new: true
    };

    // MockTip을 BaseListItem으로 변환하는 매핑 함수 테스트
    const mappedTip: BaseListItem = {
      id: tip.id.toString(),
      title: tip.title,
      created_at: new Date().toISOString(), // 상대 시간을 ISO 날짜로 변환 필요
      stats: {
        view_count: tip.views_count,
        like_count: tip.likes_count,
        dislike_count: Math.floor(tip.likes_count * 0.2),
        comment_count: Math.floor(tip.views_count * 0.1),
        bookmark_count: tip.saves_count
      }
    };

    expect(isBaseListItem(mappedTip)).toBe(true);
  });
});

describe('ItemStats 인터페이스', () => {
  test('통계 필드 정의', () => {
    const stats: ItemStats = {
      view_count: 100,
      like_count: 20,
      dislike_count: 2,
      comment_count: 15,
      bookmark_count: 10
    };

    expect(stats.view_count).toBeDefined();
    expect(stats.like_count).toBeDefined();
    expect(stats.dislike_count).toBeDefined();
    expect(stats.comment_count).toBeDefined();
    expect(stats.bookmark_count).toBeDefined();
  });

  test('선택적 필드 처리', () => {
    const minimalStats: ItemStats = {};

    expect(minimalStats.view_count).toBeUndefined();
    expect(minimalStats.like_count).toBeUndefined();
    
    // 기본값 처리 테스트
    const viewCount = minimalStats.view_count || 0;
    expect(viewCount).toBe(0);
  });
});

describe('ListPageConfig 인터페이스', () => {
  test('게시판 설정 구조', () => {
    const boardConfig: Partial<ListPageConfig<Post>> = {
      title: '게시판',
      writeButtonText: '✏️ 글쓰기',
      writeButtonLink: '/board/write',
      searchPlaceholder: '게시글 검색...',
      
      apiEndpoint: '/api/posts',
      apiFilters: {
        service: 'residential_community',
        metadata_type: 'board'
      },
      
      categories: [
        { value: 'all', label: '전체' },
        { value: 'info', label: '입주 정보' }
      ],
      
      sortOptions: [
        { value: 'latest', label: '최신순' },
        { value: 'views', label: '조회수' }
      ],
      
      cardLayout: 'list'
    };

    expect(boardConfig.title).toBe('게시판');
    expect(boardConfig.writeButtonText).toBe('✏️ 글쓰기');
    expect(boardConfig.apiEndpoint).toBe('/api/posts');
    expect(boardConfig.categories?.length).toBe(2);
    expect(boardConfig.sortOptions?.length).toBe(2);
    expect(boardConfig.cardLayout).toBe('list');
  });

  test('서비스 설정 구조', () => {
    const servicesConfig: Partial<ListPageConfig<MockService>> = {
      title: '입주업체서비스',
      writeButtonText: '📝 업체 등록',
      writeButtonLink: '/services/write',
      searchPlaceholder: '서비스 검색...',
      cardLayout: 'grid'
    };

    expect(servicesConfig.title).toBe('입주업체서비스');
    expect(servicesConfig.cardLayout).toBe('grid');
  });

  test('팁 설정 구조', () => {
    const tipsConfig: Partial<ListPageConfig<MockTip>> = {
      title: '전문가 꿀정보',
      writeButtonText: '✏️ 글쓰기',
      writeButtonLink: '/tips/write',
      searchPlaceholder: '전문가 꿀정보를 검색하세요...',
      cardLayout: 'card'
    };

    expect(tipsConfig.title).toBe('전문가 꿀정보');
    expect(tipsConfig.cardLayout).toBe('card');
  });
});

describe('타입 매핑 유틸리티', () => {
  test('Post를 BaseListItem으로 변환', () => {
    const post: Post = {
      id: '1',
      title: '테스트',
      content: '내용',
      slug: 'test',
      service: 'residential_community',
      metadata: { type: 'board', category: '일반' },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    };

    // 변환 함수 (실제 구현에서 만들 예정)
    const toBaseListItem = (post: Post): BaseListItem => ({
      id: post.id,
      title: post.title,
      created_at: post.created_at,
      stats: post.stats
    });

    const result = toBaseListItem(post);
    expect(result.id).toBe(post.id);
    expect(result.title).toBe(post.title);
    expect(result.created_at).toBe(post.created_at);
  });

  test('MockService를 BaseListItem으로 변환', () => {
    const service: MockService = {
      id: 1,
      name: '테스트 서비스',
      category: '이사',
      rating: 4.5,
      description: '설명',
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

    // 변환 함수
    const serviceToBaseListItem = (service: MockService): BaseListItem => ({
      id: service.id.toString(),
      title: service.name,
      created_at: new Date().toISOString(), // 실제로는 서비스 등록일 사용
      stats: {
        view_count: service.stats.views,
        like_count: Math.floor(service.stats.views * 0.15),
        dislike_count: Math.floor(service.stats.views * 0.03),
        comment_count: service.stats.reviews,
        bookmark_count: Math.floor(service.stats.views * 0.12)
      }
    });

    const result = serviceToBaseListItem(service);
    expect(result.id).toBe('1');
    expect(result.title).toBe('테스트 서비스');
    expect(result.stats?.view_count).toBe(100);
  });
});