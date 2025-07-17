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

describe('UnifiedPostListItem 기본 기능 테스트', () => {
  it('컴포넌트가 렌더링되고 모든 필수 요소가 표시된다', () => {
    const post = createMockPost();
    
    const { container } = render(<UnifiedPostListItem post={post} />);
    
    // 기본 구조 확인
    expect(container.querySelector('.post-item')).toBeInTheDocument();
    expect(container.querySelector('.post-category-area')).toBeInTheDocument();
    expect(container.querySelector('.post-title-area')).toBeInTheDocument();
    expect(container.querySelector('.post-badge-area')).toBeInTheDocument();
    expect(container.querySelector('.post-tags-area')).toBeInTheDocument();
    expect(container.querySelector('.post-meta-area')).toBeInTheDocument();
  });

  it('카테고리가 올바르게 표시된다', () => {
    const post = createMockPost({
      metadata: { category: '생활정보', tags: [], type: 'board' }
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('생활정보')).toBeInTheDocument();
  });

  it('제목이 올바르게 표시된다', () => {
    const post = createMockPost({
      title: '테스트 제목입니다'
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('테스트 제목입니다')).toBeInTheDocument();
  });

  it('태그가 올바르게 표시된다', () => {
    const post = createMockPost({
      metadata: { 
        category: '일반', 
        tags: ['태그1', '태그2'], 
        type: 'board' 
      }
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('#태그1')).toBeInTheDocument();
    expect(screen.getByText('#태그2')).toBeInTheDocument();
  });

  it('3개 이상의 태그가 있을 때 카운터가 표시된다', () => {
    const post = createMockPost({
      metadata: { 
        category: '일반', 
        tags: ['태그1', '태그2', '태그3', '태그4'], 
        type: 'board' 
      }
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('#태그1')).toBeInTheDocument();
    expect(screen.getByText('#태그2')).toBeInTheDocument();
    expect(screen.getByText('+2')).toBeInTheDocument();
    expect(screen.queryByText('#태그3')).not.toBeInTheDocument();
  });

  it('작성자 정보가 올바르게 표시된다', () => {
    const post = createMockPost({
      author: {
        id: 'author-1',
        display_name: '김철수',
        user_handle: 'kim',
        name: '김철수'
      }
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('김철수')).toBeInTheDocument();
  });

  it('통계 정보가 올바르게 표시된다', () => {
    const post = createMockPost({
      stats: {
        view_count: 1500,
        like_count: 25,
        dislike_count: 3,
        comment_count: 12,
        bookmark_count: 8
      }
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('👁️ 1.5K')).toBeInTheDocument();
    expect(screen.getByText('👍 25')).toBeInTheDocument();
    expect(screen.getByText('👎 3')).toBeInTheDocument();
    expect(screen.getByText('💬 12')).toBeInTheDocument();
    expect(screen.getByText('🔖 8')).toBeInTheDocument();
  });

  it('24시간 이내 게시글에 NEW 배지가 표시된다', () => {
    const now = new Date();
    const recentTime = new Date(now.getTime() - 12 * 60 * 60 * 1000); // 12시간 전
    
    const post = createMockPost({
      created_at: recentTime.toISOString()
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.getByText('NEW')).toBeInTheDocument();
  });

  it('24시간 이후 게시글에는 NEW 배지가 표시되지 않는다', () => {
    const now = new Date();
    const oldTime = new Date(now.getTime() - 25 * 60 * 60 * 1000); // 25시간 전
    
    const post = createMockPost({
      created_at: oldTime.toISOString()
    });
    
    render(<UnifiedPostListItem post={post} />);
    
    expect(screen.queryByText('NEW')).not.toBeInTheDocument();
  });

  it('클릭 핸들러가 올바르게 동작한다', () => {
    let clickedPost: Post | null = null;
    const handleClick = (post: Post) => {
      clickedPost = post;
    };
    
    const post = createMockPost();
    
    const { container } = render(
      <UnifiedPostListItem post={post} onClick={handleClick} />
    );
    
    const postItem = container.querySelector('.post-item');
    postItem?.click();
    
    expect(clickedPost).toBe(post);
  });
});