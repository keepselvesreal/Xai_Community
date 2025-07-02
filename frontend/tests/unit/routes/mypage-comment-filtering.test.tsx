/**
 * 마이페이지 댓글 필터링 테스트
 * 페이지 타입별로 댓글이 올바르게 분류되는지 확인
 */

import { describe, it, expect } from 'vitest';
import type { ActivityItem } from '~/types';

// 마이페이지에서 사용하는 댓글 필터링 함수 복사
const getCommentsByPageType = (comments: ActivityItem[], pageType: string): ActivityItem[] => {
  if (!comments) return [];
  
  return comments.filter(comment => {
    if (!comment.route_path) return false;
    
    switch (pageType) {
      case 'board':
        return comment.route_path.startsWith('/board-post/') && !comment.subtype;
      case 'info':
        return comment.route_path.startsWith('/property-info/') && !comment.subtype;
      case 'services':
        return comment.route_path.startsWith('/moving-services-post/') && !comment.subtype;
      case 'tips':
        return comment.route_path.startsWith('/expert-tips/') && !comment.subtype;
      default:
        return false;
    }
  });
};

describe('마이페이지 댓글 페이지 타입별 필터링', () => {
  const mockComments: ActivityItem[] = [
    // 게시판 댓글
    {
      id: '1',
      content: '게시판 댓글',
      created_at: '2024-01-01T10:00:00Z',
      route_path: '/board-post/test-board-slug'
    },
    // 정보 페이지 댓글
    {
      id: '2',
      content: '정보 페이지 댓글',
      created_at: '2024-01-01T11:00:00Z',
      route_path: '/property-info/test-info-slug'
    },
    // 서비스 페이지 일반 댓글
    {
      id: '3',
      content: '서비스 페이지 일반 댓글',
      created_at: '2024-01-01T12:00:00Z',
      route_path: '/moving-services-post/test-service-slug'
    },
    // 서비스 페이지 문의 댓글 (제외되어야 함)
    {
      id: '4',
      content: '서비스 문의 댓글',
      created_at: '2024-01-01T13:00:00Z',
      route_path: '/moving-services-post/test-service-slug',
      subtype: 'inquiry'
    },
    // 서비스 페이지 후기 댓글 (제외되어야 함)
    {
      id: '5',
      content: '서비스 후기 댓글',
      created_at: '2024-01-01T14:00:00Z',
      route_path: '/moving-services-post/test-service-slug',
      subtype: 'review'
    },
    // 전문가 꿀정보 댓글
    {
      id: '6',
      content: '전문가 꿀정보 댓글',
      created_at: '2024-01-01T15:00:00Z',
      route_path: '/expert-tips/test-tips-slug'
    },
    // 잘못된 라우트 경로 (제외되어야 함)
    {
      id: '7',
      content: '잘못된 경로 댓글',
      created_at: '2024-01-01T16:00:00Z',
      route_path: '/unknown-page/test-slug'
    },
    // route_path가 없는 댓글 (제외되어야 함)
    {
      id: '8',
      content: '경로 없는 댓글',
      created_at: '2024-01-01T17:00:00Z',
      route_path: ''
    }
  ];

  it('게시판 댓글만 올바르게 필터링해야 한다', () => {
    const boardComments = getCommentsByPageType(mockComments, 'board');
    
    expect(boardComments).toHaveLength(1);
    expect(boardComments[0].id).toBe('1');
    expect(boardComments[0].content).toBe('게시판 댓글');
    expect(boardComments[0].route_path).toBe('/board-post/test-board-slug');
  });

  it('정보 페이지 댓글만 올바르게 필터링해야 한다', () => {
    const infoComments = getCommentsByPageType(mockComments, 'info');
    
    expect(infoComments).toHaveLength(1);
    expect(infoComments[0].id).toBe('2');
    expect(infoComments[0].content).toBe('정보 페이지 댓글');
    expect(infoComments[0].route_path).toBe('/property-info/test-info-slug');
  });

  it('서비스 페이지 일반 댓글만 필터링하고 문의/후기는 제외해야 한다', () => {
    const serviceComments = getCommentsByPageType(mockComments, 'services');
    
    expect(serviceComments).toHaveLength(1);
    expect(serviceComments[0].id).toBe('3');
    expect(serviceComments[0].content).toBe('서비스 페이지 일반 댓글');
    expect(serviceComments[0].route_path).toBe('/moving-services-post/test-service-slug');
    expect(serviceComments[0].subtype).toBeUndefined();
  });

  it('전문가 꿀정보 댓글만 올바르게 필터링해야 한다', () => {
    const tipsComments = getCommentsByPageType(mockComments, 'tips');
    
    expect(tipsComments).toHaveLength(1);
    expect(tipsComments[0].id).toBe('6');
    expect(tipsComments[0].content).toBe('전문가 꿀정보 댓글');
    expect(tipsComments[0].route_path).toBe('/expert-tips/test-tips-slug');
  });

  it('존재하지 않는 페이지 타입의 경우 빈 배열을 반환해야 한다', () => {
    const unknownComments = getCommentsByPageType(mockComments, 'unknown');
    
    expect(unknownComments).toHaveLength(0);
  });

  it('댓글 배열이 null이나 undefined인 경우 빈 배열을 반환해야 한다', () => {
    expect(getCommentsByPageType(null as any, 'board')).toHaveLength(0);
    expect(getCommentsByPageType(undefined as any, 'board')).toHaveLength(0);
  });

  it('문의 댓글은 어떤 페이지 타입 필터에도 포함되지 않아야 한다', () => {
    const inquiryComment = mockComments.find(c => c.subtype === 'inquiry');
    expect(inquiryComment).toBeDefined();

    expect(getCommentsByPageType([inquiryComment!], 'board')).toHaveLength(0);
    expect(getCommentsByPageType([inquiryComment!], 'info')).toHaveLength(0);
    expect(getCommentsByPageType([inquiryComment!], 'services')).toHaveLength(0);
    expect(getCommentsByPageType([inquiryComment!], 'tips')).toHaveLength(0);
  });

  it('후기 댓글은 어떤 페이지 타입 필터에도 포함되지 않아야 한다', () => {
    const reviewComment = mockComments.find(c => c.subtype === 'review');
    expect(reviewComment).toBeDefined();

    expect(getCommentsByPageType([reviewComment!], 'board')).toHaveLength(0);
    expect(getCommentsByPageType([reviewComment!], 'info')).toHaveLength(0);
    expect(getCommentsByPageType([reviewComment!], 'services')).toHaveLength(0);
    expect(getCommentsByPageType([reviewComment!], 'tips')).toHaveLength(0);
  });
});