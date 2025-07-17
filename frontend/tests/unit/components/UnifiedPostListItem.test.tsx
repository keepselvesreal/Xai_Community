import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import type { Post } from '~/types';
import { UnifiedPostListItem } from '~/components/common/UnifiedPostListItem';

// 테스트용 모사 데이터 생성 함수
const createMockPost = (overrides: Partial<Post> = {}): Post => ({
  id: 'test-post-1',
  title: '기본 제목',
  content: '기본 내용',
  slug: 'test-post-1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  author: {
    id: 'author-1',
    display_name: '작성자',
    user_handle: 'author',
    name: '작성자'
  },
  metadata: {
    category: '일반',
    tags: ['태그1', '태그2'],
    type: 'board'
  },
  stats: {
    view_count: 100,
    like_count: 10,
    dislike_count: 1,
    comment_count: 5,
    bookmark_count: 3
  },
  ...overrides
});

describe('UnifiedPostListItem 레이아웃 일관성 테스트', () => {
  describe('카테고리 태그 길이별 일관성 테스트', () => {
    it('짧은 카테고리명 "일반"에 대해 올바른 레이아웃을 유지한다', () => {
      const post = createMockPost({
        metadata: { category: '일반', tags: ['태그1'], type: 'board' }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const categoryArea = container.querySelector('.post-category-area');
      const titleArea = container.querySelector('.post-title-area');
      
      // CSS 클래스가 올바르게 적용되었는지 확인
      expect(postItem).toHaveClass('post-item');
      expect(categoryArea).toBeInTheDocument();
      expect(titleArea).toBeInTheDocument();
      
      // 카테고리 태그가 존재하고 올바른 클래스를 가지는지 확인
      const categoryTag = container.querySelector('.post-tag');
      expect(categoryTag).toHaveClass('post-tag');
      expect(categoryTag).toHaveTextContent('일반');
    });

    it('긴 카테고리명 "생활정보및팁"에 대해서도 동일한 레이아웃을 유지한다', () => {
      const post = createMockPost({
        metadata: { category: '생활정보및팁', tags: ['태그1'], type: 'board' }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const categoryTag = container.querySelector('.post-tag');
      
      // 동일한 높이와 카테고리 태그 크기 유지
      expect(postItem).toHaveStyle({ height: '88px' });
      expect(categoryTag).toHaveStyle({ width: '100px', height: '24px' });
    });

    it('매우 긴 카테고리명도 ellipsis로 처리되어 레이아웃이 깨지지 않는다', () => {
      const post = createMockPost({
        metadata: { 
          category: '매우매우매우긴카테고리명테스트용', 
          tags: ['태그1'], 
          type: 'board' 
        }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const categoryTag = container.querySelector('.post-tag');
      
      expect(categoryTag).toHaveStyle({ 
        width: '100px', 
        height: '24px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      });
    });
  });

  describe('제목 길이별 일관성 테스트', () => {
    it('짧은 제목에 대해 올바른 레이아웃을 유지한다', () => {
      const post = createMockPost({
        title: '짧은 제목'
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const titleText = container.querySelector('.post-title-text');
      
      expect(titleText).toHaveStyle({
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      });
    });

    it('매우 긴 제목도 ellipsis로 처리되어 한 줄을 유지한다', () => {
      const post = createMockPost({
        title: '이것은 매우 긴 제목입니다. 이 제목은 한 줄을 넘어갈 정도로 길어서 ellipsis 처리가 되어야 합니다. 그래야 레이아웃이 일관되게 유지됩니다.'
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const titleText = container.querySelector('.post-title-text');
      
      // 높이는 여전히 88px로 고정
      expect(postItem).toHaveStyle({ height: '88px' });
      expect(titleText).toHaveStyle({
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      });
    });
  });

  describe('태그 개수별 일관성 테스트', () => {
    it('태그가 없을 때도 올바른 레이아웃을 유지한다', () => {
      const post = createMockPost({
        metadata: { category: '일반', tags: [], type: 'board' }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const tagsArea = container.querySelector('.post-tags-area');
      
      expect(postItem).toHaveStyle({ height: '88px' });
      expect(tagsArea).toBeInTheDocument();
    });

    it('태그가 1개일 때 올바른 레이아웃을 유지한다', () => {
      const post = createMockPost({
        metadata: { category: '일반', tags: ['태그1'], type: 'board' }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const userTags = container.querySelectorAll('.user-tag');
      
      expect(userTags).toHaveLength(1);
      expect(userTags[0]).toHaveStyle({ width: '70px', height: '20px' });
    });

    it('태그가 2개일 때 올바른 레이아웃을 유지한다', () => {
      const post = createMockPost({
        metadata: { category: '일반', tags: ['태그1', '태그2'], type: 'board' }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const userTags = container.querySelectorAll('.user-tag');
      
      expect(postItem).toHaveStyle({ height: '88px' });
      expect(userTags).toHaveLength(2);
      userTags.forEach(tag => {
        expect(tag).toHaveStyle({ width: '70px', height: '20px' });
      });
    });

    it('태그가 3개 이상일 때 2개만 표시하고 카운터를 보여준다', () => {
      const post = createMockPost({
        metadata: { 
          category: '일반', 
          tags: ['태그1', '태그2', '태그3', '태그4', '태그5'], 
          type: 'board' 
        }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const userTags = container.querySelectorAll('.user-tag');
      const tagCounter = container.querySelector('.tag-counter');
      
      expect(postItem).toHaveStyle({ height: '88px' });
      expect(userTags).toHaveLength(2); // 최대 2개만 표시
      expect(tagCounter).toHaveTextContent('+3'); // 나머지 3개
    });
  });

  describe('사용자명 길이별 일관성 테스트', () => {
    it('짧은 사용자명에 대해 올바른 레이아웃을 유지한다', () => {
      const post = createMockPost({
        author: {
          id: 'author-1',
          display_name: '김철수',
          user_handle: 'kim',
          name: '김철수'
        }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const authorName = container.querySelector('.author-name');
      
      expect(authorName).toHaveStyle({
        width: '60px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      });
    });

    it('긴 사용자명도 ellipsis로 처리되어 고정 크기를 유지한다', () => {
      const post = createMockPost({
        author: {
          id: 'author-1',
          display_name: '매우긴사용자이름테스트용계정',
          user_handle: 'longnameuser',
          name: '매우긴사용자이름테스트용계정'
        }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const authorName = container.querySelector('.author-name');
      
      expect(postItem).toHaveStyle({ height: '88px' });
      expect(authorName).toHaveStyle({
        width: '60px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap'
      });
    });
  });

  describe('통계 데이터 표시 일관성 테스트', () => {
    it('모든 통계 아이콘이 고정 크기를 가진다', () => {
      const post = createMockPost({
        stats: {
          view_count: 1234,
          like_count: 56,
          dislike_count: 7,
          comment_count: 89,
          bookmark_count: 12
        }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const statIcons = container.querySelectorAll('.stat-icon');
      
      expect(statIcons).toHaveLength(5); // 조회수, 좋아요, 싫어요, 댓글, 북마크
      statIcons.forEach(icon => {
        expect(icon).toHaveStyle({
          width: '42px',
          height: '16px',
          flexShrink: '0'
        });
      });
    });

    it('큰 숫자도 포맷팅되어 레이아웃이 깨지지 않는다', () => {
      const post = createMockPost({
        stats: {
          view_count: 999999,
          like_count: 50000,
          dislike_count: 1000,
          comment_count: 25000,
          bookmark_count: 5000
        }
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      const statIcons = container.querySelectorAll('.stat-icon');
      
      expect(postItem).toHaveStyle({ height: '88px' });
      statIcons.forEach(icon => {
        expect(icon).toHaveStyle({ width: '42px', height: '16px' });
      });
    });
  });

  describe('NEW 배지 표시 일관성 테스트', () => {
    it('24시간 이내 게시글에 NEW 배지가 표시된다', () => {
      const now = new Date();
      const recentTime = new Date(now.getTime() - 12 * 60 * 60 * 1000); // 12시간 전
      
      const post = createMockPost({
        created_at: recentTime.toISOString()
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const newBadge = container.querySelector('.badge-new');
      
      expect(newBadge).toBeInTheDocument();
      expect(newBadge).toHaveStyle({
        width: '32px',
        height: '16px'
      });
    });

    it('24시간 이후 게시글에는 NEW 배지가 표시되지 않는다', () => {
      const now = new Date();
      const oldTime = new Date(now.getTime() - 25 * 60 * 60 * 1000); // 25시간 전
      
      const post = createMockPost({
        created_at: oldTime.toISOString()
      });
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const newBadge = container.querySelector('.badge-new');
      
      expect(newBadge).not.toBeInTheDocument();
    });
  });

  describe('전체 컴포넌트 구조 일관성 테스트', () => {
    it('모든 영역이 올바른 그리드 구조를 가진다', () => {
      const post = createMockPost();
      
      const { container } = render(<UnifiedPostListItem post={post} />);
      const postItem = container.querySelector('.post-item');
      
      expect(postItem).toHaveStyle({
        display: 'grid',
        gridTemplateAreas: '"category title badge" "tags meta meta"',
        gridTemplateColumns: '120px 1fr 60px',
        gridTemplateRows: '40px 48px',
        height: '88px'
      });
    });

    it('다양한 조건에서도 그리드 구조가 유지된다', () => {
      const scenarios = [
        { title: '짧은 제목', category: '일반', tags: [] },
        { title: '매우 긴 제목입니다매우 긴 제목입니다매우 긴 제목입니다', category: '생활정보', tags: ['태그1', '태그2', '태그3'] },
        { title: '중간 길이의 제목', category: '이야기', tags: ['태그1'] }
      ];

      scenarios.forEach((scenario, index) => {
        const post = createMockPost({
          id: `test-${index}`,
          title: scenario.title,
          metadata: {
            category: scenario.category,
            tags: scenario.tags,
            type: 'board'
          }
        });

        const { container } = render(<UnifiedPostListItem post={post} />);
        const postItem = container.querySelector('.post-item');
        
        expect(postItem).toHaveStyle({ height: '88px' });
        
        // 모든 필요한 영역이 존재하는지 확인
        expect(container.querySelector('.post-category-area')).toBeInTheDocument();
        expect(container.querySelector('.post-title-area')).toBeInTheDocument();
        expect(container.querySelector('.post-badge-area')).toBeInTheDocument();
        expect(container.querySelector('.post-tags-area')).toBeInTheDocument();
        expect(container.querySelector('.post-meta-area')).toBeInTheDocument();
      });
    });
  });
});