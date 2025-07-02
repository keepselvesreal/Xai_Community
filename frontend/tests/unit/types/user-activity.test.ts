/**
 * TDD Red Phase: 타입 정의 테스트 (실패하는 테스트)
 * UserActivityResponse, ActivityItem, ActivitySummary 인터페이스 검증
 */

import { describe, it, expect } from 'vitest';
import type { 
  UserActivityResponse, 
  ActivityItem, 
  ActivitySummary 
} from '~/types';

describe('사용자 활동 조회 API 타입 정의', () => {
  describe('ActivitySummary 인터페이스', () => {
    it('필수 필드들이 올바른 타입을 가져야 한다', () => {
      const summary: ActivitySummary = {
        total_posts: 5,
        total_comments: 12,
        total_reactions: 8,
        most_active_page_type: 'board'
      };

      expect(typeof summary.total_posts).toBe('number');
      expect(typeof summary.total_comments).toBe('number');
      expect(typeof summary.total_reactions).toBe('number');
      expect(typeof summary.most_active_page_type).toBe('string');
    });

    it('most_active_page_type은 optional이어야 한다', () => {
      const summary: ActivitySummary = {
        total_posts: 0,
        total_comments: 0,
        total_reactions: 0
        // most_active_page_type 없어도 됨
      };

      expect(summary.most_active_page_type).toBeUndefined();
    });
  });

  describe('ActivityItem 인터페이스', () => {
    it('필수 필드들이 올바른 타입을 가져야 한다', () => {
      const item: ActivityItem = {
        id: '507f1f77bcf86cd799439011',
        created_at: '2024-01-01T10:00:00Z',
        route_path: '/board-post/test-slug'
      };

      expect(typeof item.id).toBe('string');
      expect(typeof item.created_at).toBe('string');
      expect(typeof item.route_path).toBe('string');
    });

    it('게시글 관련 optional 필드들이 올바른 타입을 가져야 한다', () => {
      const postItem: ActivityItem = {
        id: '507f1f77bcf86cd799439011',
        title: '테스트 게시글',
        slug: 'test-slug',
        created_at: '2024-01-01T10:00:00Z',
        like_count: 5,
        comment_count: 3,
        route_path: '/board-post/test-slug'
      };

      expect(typeof postItem.title).toBe('string');
      expect(typeof postItem.slug).toBe('string');
      expect(typeof postItem.like_count).toBe('number');
      expect(typeof postItem.comment_count).toBe('number');
    });

    it('댓글 관련 optional 필드들이 올바른 타입을 가져야 한다', () => {
      const commentItem: ActivityItem = {
        id: '507f1f77bcf86cd799439012',
        content: '테스트 댓글 내용',
        created_at: '2024-01-01T11:00:00Z',
        route_path: '/board-post/test-slug',
        subtype: 'inquiry'
      };

      expect(typeof commentItem.content).toBe('string');
      expect(typeof commentItem.subtype).toBe('string');
    });

    it('반응 관련 optional 필드들이 올바른 타입을 가져야 한다', () => {
      const reactionItem: ActivityItem = {
        id: '507f1f77bcf86cd799439013',
        created_at: '2024-01-01T12:00:00Z',
        route_path: '/board-post/test-slug',
        target_type: 'post',
        target_id: '507f1f77bcf86cd799439011',
        target_title: '반응한 게시글 제목'
      };

      expect(typeof reactionItem.target_type).toBe('string');
      expect(typeof reactionItem.target_id).toBe('string');
      expect(typeof reactionItem.target_title).toBe('string');
    });
  });

  describe('UserActivityResponse 인터페이스', () => {
    it('필수 필드들이 올바른 구조를 가져야 한다', () => {
      const response: UserActivityResponse = {
        posts: {
          board: [],
          info: [],
          services: [],
          tips: []
        },
        comments: [],
        reactions: {
          likes: [],
          bookmarks: [],
          dislikes: []
        },
        summary: {
          total_posts: 0,
          total_comments: 0,
          total_reactions: 0
        }
      };

      expect(typeof response.posts).toBe('object');
      expect(Array.isArray(response.posts.board)).toBe(true);
      expect(Array.isArray(response.posts.info)).toBe(true);
      expect(Array.isArray(response.posts.services)).toBe(true);
      expect(Array.isArray(response.posts.tips)).toBe(true);
      
      expect(Array.isArray(response.comments)).toBe(true);
      
      expect(typeof response.reactions).toBe('object');
      expect(Array.isArray(response.reactions.likes)).toBe(true);
      expect(Array.isArray(response.reactions.bookmarks)).toBe(true);
      expect(Array.isArray(response.reactions.dislikes)).toBe(true);
      
      expect(typeof response.summary).toBe('object');
    });

    it('실제 API 응답과 같은 구조의 데이터를 처리할 수 있어야 한다', () => {
      const apiResponse: UserActivityResponse = {
        posts: {
          board: [
            {
              id: '507f1f77bcf86cd799439012',
              title: '게시판 게시글',
              slug: 'board-post-slug',
              created_at: '2024-01-01T10:00:00Z',
              like_count: 5,
              comment_count: 3,
              route_path: '/board-post/board-post-slug'
            }
          ],
          info: [
            {
              id: '507f1f77bcf86cd799439013',
              title: '입주 정보 게시글',
              slug: 'info-post-slug',
              created_at: '2024-01-01T11:00:00Z',
              like_count: 2,
              comment_count: 1,
              route_path: '/property-info/info-post-slug'
            }
          ],
          services: [],
          tips: []
        },
        comments: [
          {
            id: '507f1f77bcf86cd799439020',
            content: '일반 댓글입니다',
            created_at: '2024-01-01T14:00:00Z',
            route_path: '/board-post/board-post-slug'
          },
          {
            id: '507f1f77bcf86cd799439021',
            content: '서비스 문의 댓글입니다',
            created_at: '2024-01-01T15:00:00Z',
            route_path: '/moving-services-post/services-post-slug',
            subtype: 'inquiry'
          }
        ],
        reactions: {
          likes: [
            {
              id: '507f1f77bcf86cd799439030',
              target_type: 'post',
              target_id: '507f1f77bcf86cd799439012',
              created_at: '2024-01-01T17:00:00Z',
              route_path: '/board-post/board-post-slug',
              target_title: '게시판 게시글'
            }
          ],
          bookmarks: [
            {
              id: '507f1f77bcf86cd799439032',
              target_type: 'post',
              target_id: '507f1f77bcf86cd799439013',
              created_at: '2024-01-01T19:00:00Z',
              route_path: '/property-info/info-post-slug',
              target_title: '입주 정보 게시글'
            }
          ],
          dislikes: []
        },
        summary: {
          total_posts: 2,
          total_comments: 2,
          total_reactions: 2,
          most_active_page_type: 'board'
        }
      };

      // 타입 체크가 통과해야 함
      expect(apiResponse).toBeDefined();
      expect(apiResponse.posts.board.length).toBe(1);
      expect(apiResponse.comments.length).toBe(2);
      expect(apiResponse.reactions.likes.length).toBe(1);
      expect(apiResponse.summary.total_posts).toBe(2);
    });
  });

  describe('타입 호환성 검증', () => {
    it('백엔드 API 응답과 프론트엔드 타입이 호환되어야 한다', () => {
      // 실제 백엔드 API 응답 형태 시뮬레이션
      const backendResponse = {
        posts: {
          board: [
            {
              id: '686488bec5a4a334eaf42b9c',
              title: '25-07-02-1',
              slug: '686488bec5a4a334eaf42b9c-25-07-02-1',
              created_at: '2025-07-02T01:17:50.232000',
              like_count: 0,
              comment_count: 9,
              route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1'
            }
          ],
          info: [],
          services: [],
          tips: []
        },
        comments: [
          {
            id: '686488c8c5a4a334eaf42b9e',
            content: '댓글1!',
            created_at: '2025-07-02T01:18:00.344000',
            route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1'
          }
        ],
        reactions: {
          likes: [
            {
              id: '686488c2c5a4a334eaf42b9d',
              target_type: 'post',
              target_id: '686488bec5a4a334eaf42b9c',
              created_at: '2025-07-02T01:17:54.806000',
              route_path: '/board-post/686488bec5a4a334eaf42b9c-25-07-02-1',
              target_title: '25-07-02-1'
            }
          ],
          bookmarks: [],
          dislikes: []
        },
        summary: {
          total_posts: 1,
          total_comments: 1,
          total_reactions: 1,
          most_active_page_type: 'board'
        }
      };

      // 타입 변환이 가능해야 함
      const typedResponse: UserActivityResponse = backendResponse;
      expect(typedResponse).toBeDefined();
      expect(typedResponse.posts.board[0].title).toBe('25-07-02-1');
    });
  });
});