/**
 * Tip 타입 정의 및 변환 함수 테스트
 * TDD: MockTip → Tip 리팩토링을 위한 테스트
 */

import { describe, expect, it } from 'vitest';
import type { Tip } from '~/types';
import { tipToBaseListItem, parseRelativeDate } from '~/types/listTypes';

describe('Tip Type', () => {
  const mockTip: Tip = {
    id: 1,
    title: "겨울철 실내 화분 관리법",
    content: "실내 온도와 습도 조절을 통한 효과적인 식물 관리 방법을 알려드립니다.",
    slug: "winter-plant-care",
    expert_name: "김○○",
    expert_title: "클린 라이프 🌱 원예 전문가",
    created_at: "2일 전",
    category: "원예",
    tags: ["#실내화분", "#겨울관리", "#습도조절"],
    views_count: 245,
    likes_count: 32,
    saves_count: 18,
    is_new: true
  };

  it('should have all required properties', () => {
    expect(mockTip).toHaveProperty('id');
    expect(mockTip).toHaveProperty('title');
    expect(mockTip).toHaveProperty('content');
    expect(mockTip).toHaveProperty('slug');
    expect(mockTip).toHaveProperty('expert_name');
    expect(mockTip).toHaveProperty('expert_title');
    expect(mockTip).toHaveProperty('created_at');
    expect(mockTip).toHaveProperty('category');
    expect(mockTip).toHaveProperty('tags');
    expect(mockTip).toHaveProperty('views_count');
    expect(mockTip).toHaveProperty('likes_count');
    expect(mockTip).toHaveProperty('saves_count');
    expect(mockTip).toHaveProperty('is_new');
  });

  it('should convert to BaseListItem correctly', () => {
    const baseItem = tipToBaseListItem(mockTip);
    
    expect(baseItem).toEqual({
      id: '1',
      title: "겨울철 실내 화분 관리법",
      created_at: expect.any(String),
      stats: {
        view_count: 245,
        like_count: 32,
        dislike_count: Math.floor(32 * 0.2),
        comment_count: Math.floor(245 * 0.1),
        bookmark_count: 18
      }
    });
  });

  it('should handle string id conversion', () => {
    const baseItem = tipToBaseListItem(mockTip);
    expect(typeof baseItem.id).toBe('string');
    expect(baseItem.id).toBe('1');
  });

  it('should calculate derived stats correctly', () => {
    const baseItem = tipToBaseListItem(mockTip);
    
    expect(baseItem.stats?.view_count).toBe(245);
    expect(baseItem.stats?.like_count).toBe(32);
    expect(baseItem.stats?.dislike_count).toBe(6); // 32 * 0.2 = 6.4 → 6
    expect(baseItem.stats?.comment_count).toBe(24); // 245 * 0.1 = 24.5 → 24
    expect(baseItem.stats?.bookmark_count).toBe(18);
  });

  it('should handle relative date parsing', () => {
    const isoDate = parseRelativeDate("2일 전");
    expect(isoDate).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    
    const now = new Date();
    const parsedDate = new Date(isoDate);
    const diffInDays = Math.floor((now.getTime() - parsedDate.getTime()) / (1000 * 60 * 60 * 24));
    expect(diffInDays).toBeGreaterThanOrEqual(1);
    expect(diffInDays).toBeLessThanOrEqual(3);
  });
});

describe('Tip Data Validation', () => {
  it('should validate tip categories', () => {
    const validCategories = ['원예', '청소/정리', '인테리어', '생활', '절약', '반려동물'];
    
    validCategories.forEach(category => {
      const tip: Tip = {
        id: 1,
        title: "Test Tip",
        content: "Test content",
        expert_name: "전문가",
        expert_title: "테스트 전문가",
        created_at: "1일 전",
        category,
        tags: [],
        views_count: 0,
        likes_count: 0,
        saves_count: 0,
        is_new: false
      };
      
      expect(tip.category).toBe(category);
    });
  });

  it('should validate tag format', () => {
    const tip: Tip = {
      id: 1,
      title: "Test Tip",
      content: "Test content",
      expert_name: "전문가",
      expert_title: "테스트 전문가",
      created_at: "1일 전",
      category: "생활",
      tags: ["#태그1", "#태그2", "#태그3"],
      views_count: 0,
      likes_count: 0,
      saves_count: 0,
      is_new: false
    };
    
    tip.tags.forEach(tag => {
      expect(tag).toMatch(/^#/);
    });
  });
});