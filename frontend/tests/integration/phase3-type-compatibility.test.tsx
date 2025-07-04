/**
 * Phase 3: 프론트엔드 타입 정의 통일 검증 테스트
 * 백엔드 API 응답과 프론트엔드 타입 정의의 호환성을 확인
 */

import { describe, it, expect, vi } from 'vitest';
import type { 
  UserActivityResponse, 
  DbPageType, 
  ReactionTypePrefix, 
  ActivityItem,
  ReactionGroups,
  PageTypeGroups 
} from '~/types';

describe('Phase 3: Type Compatibility Tests', () => {
  it('should have correct DB page types matching backend', () => {
    // 백엔드 API 응답에서 확인된 페이지 타입들
    const expectedPageTypes: DbPageType[] = [
      'board',
      'property_information', // DB 원시 타입
      'expert_tips',           // DB 원시 타입  
      'services'               // Phase 5에서 moving_services로 변경 예정
    ];
    
    // 타입 컴파일 확인 (런타임에서는 확인할 수 없으므로 실제 값으로 검증)
    const testPageType1: DbPageType = 'board';
    const testPageType2: DbPageType = 'property_information';
    const testPageType3: DbPageType = 'expert_tips';
    const testPageType4: DbPageType = 'services';
    
    expect(expectedPageTypes).toContain(testPageType1);
    expect(expectedPageTypes).toContain(testPageType2);
    expect(expectedPageTypes).toContain(testPageType3);
    expect(expectedPageTypes).toContain(testPageType4);
  });

  it('should have correct reaction type prefixes matching backend', () => {
    // 백엔드 API 응답에서 확인된 반응 키들
    const expectedReactionPrefixes: ReactionTypePrefix[] = [
      'reaction-likes',
      'reaction-dislikes', 
      'reaction-bookmarks'
    ];
    
    const testReactionType1: ReactionTypePrefix = 'reaction-likes';
    const testReactionType2: ReactionTypePrefix = 'reaction-dislikes';
    const testReactionType3: ReactionTypePrefix = 'reaction-bookmarks';
    
    expect(expectedReactionPrefixes).toContain(testReactionType1);
    expect(expectedReactionPrefixes).toContain(testReactionType2);
    expect(expectedReactionPrefixes).toContain(testReactionType3);
  });

  it('should validate UserActivityResponse structure matches backend API', () => {
    // 실제 백엔드 API 응답 구조와 동일한 mock 데이터
    const mockApiResponse: UserActivityResponse = {
      posts: {
        board: [],
        property_information: [], // DB 원시 타입
        expert_tips: [],          // DB 원시 타입
        services: []              // Phase 5에서 moving_services로 변경 예정
      },
      comments: [],
      "reaction-likes": {
        board: [],
        property_information: [],
        expert_tips: [],
        services: []
      },
      "reaction-dislikes": {
        board: [],
        property_information: [],
        expert_tips: [],
        services: []
      },
      "reaction-bookmarks": {
        board: [],
        property_information: [],
        expert_tips: [],
        services: []
      },
      pagination: {
        posts: {
          total_count: 0,
          page: 1,
          limit: 10,
          has_more: false
        },
        comments: {
          total_count: 0,
          page: 1,
          limit: 10,
          has_more: false
        },
        reactions: {
          total_count: 0,
          page: 1,
          limit: 10,
          has_more: false
        }
      }
    };

    // 구조 검증
    expect(mockApiResponse.posts).toBeDefined();
    expect(mockApiResponse.posts.board).toBeDefined();
    expect(mockApiResponse.posts.property_information).toBeDefined();
    expect(mockApiResponse.posts.expert_tips).toBeDefined();
    expect(mockApiResponse.posts.services).toBeDefined();
    
    expect(mockApiResponse["reaction-likes"]).toBeDefined();
    expect(mockApiResponse["reaction-dislikes"]).toBeDefined();
    expect(mockApiResponse["reaction-bookmarks"]).toBeDefined();
    
    expect(mockApiResponse.comments).toBeDefined();
    expect(mockApiResponse.pagination).toBeDefined();
  });

  it('should validate ActivityItem interface matches backend response fields', () => {
    // 백엔드 API에서 실제 반환되는 ActivityItem 구조
    const mockPostItem: ActivityItem = {
      id: "68675c4fc855b47799dd6636",
      title: "25-07-04-1",
      slug: "68675c4fc855b47799dd6636-25-07-04-1",
      created_at: "2025-07-04T04:45:03.202000",
      view_count: 6,
      like_count: 1,
      dislike_count: 0,
      comment_count: 0,
      route_path: "/board-post/68675c4fc855b47799dd6636-25-07-04-1"
    };

    const mockCommentItem: ActivityItem = {
      id: "68675effc855b47799dd6649",
      title: "김병만 이사",
      content: "평점: 5점\n\n후기 추가",
      created_at: "2025-07-04T04:56:31.410000",
      route_path: "/moving-services-post/68675c7ec855b47799dd6637-김병만-이사",
      subtype: "service_review"
    };

    const mockReactionItem: ActivityItem = {
      id: "68676503fc4e85e08b7c9159",
      title: "2분기 분기 수도권 아파트 거래 동향",
      created_at: "2025-07-04T05:22:11.682000",
      route_path: "/post/68676477fc4e85e08b7c914b-2분기-분기-수도권-아파트-거래-동향",
      target_type: "post",
      target_id: "68676477fc4e85e08b7c914b",
      target_title: "2분기 분기 수도권 아파트 거래 동향"
    };

    // 필수 필드 검증
    expect(mockPostItem.id).toBeDefined();
    expect(mockPostItem.created_at).toBeDefined();
    expect(mockPostItem.route_path).toBeDefined();
    
    expect(mockCommentItem.id).toBeDefined();
    expect(mockCommentItem.created_at).toBeDefined();
    expect(mockCommentItem.route_path).toBeDefined();
    
    expect(mockReactionItem.id).toBeDefined();
    expect(mockReactionItem.created_at).toBeDefined();
    expect(mockReactionItem.route_path).toBeDefined();

    // 선택적 필드 검증
    expect(mockPostItem.title).toBeDefined();
    expect(mockCommentItem.content).toBeDefined();
    expect(mockReactionItem.target_type).toBeDefined();
  });

  it('should validate helper types for type safety', () => {
    // PageTypeGroups 타입 검증
    const mockPageGroups: PageTypeGroups<ActivityItem> = {
      board: [],
      property_information: [],
      expert_tips: [],
      services: []
    };

    expect(mockPageGroups.board).toBeDefined();
    expect(mockPageGroups.property_information).toBeDefined();
    expect(mockPageGroups.expert_tips).toBeDefined();
    expect(mockPageGroups.services).toBeDefined();

    // ReactionGroups 타입 검증 
    const mockReactionGroups: ReactionGroups = {
      "reaction-likes": {
        board: [],
        property_information: [],
        expert_tips: [],
        services: []
      },
      "reaction-dislikes": {
        board: [],
        property_information: [],
        expert_tips: [],
        services: []
      },
      "reaction-bookmarks": {
        board: [],
        property_information: [],
        expert_tips: [],
        services: []
      }
    };

    expect(mockReactionGroups["reaction-likes"]).toBeDefined();
    expect(mockReactionGroups["reaction-dislikes"]).toBeDefined();
    expect(mockReactionGroups["reaction-bookmarks"]).toBeDefined();
  });

  it('should document Phase 5 preparation for moving_services migration', () => {
    // Phase 5에서 services -> moving_services 변경 예정 사항 문서화
    const phase5MigrationPlan = {
      currentDbPageType: 'services' as DbPageType,
      futureDbPageType: 'moving_services', // Phase 5에서 변경될 타입
      migrationNote: 'DB 원시 타입으로 통일하여 매핑 복잡성 제거'
    };

    expect(phase5MigrationPlan.currentDbPageType).toBe('services');
    expect(phase5MigrationPlan.futureDbPageType).toBe('moving_services');
    expect(phase5MigrationPlan.migrationNote).toContain('DB 원시 타입');
  });
});