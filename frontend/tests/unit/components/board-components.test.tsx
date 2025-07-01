import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import type { Post } from '~/types';
import { formatRelativeTime, formatNumber } from '~/lib/utils';

// Mock 컴포넌트 - 게시글 카드 부분만 추출하여 테스트
const PostCardInBoard = ({ post }: { post: Post }) => {
  const getTagColor = (category: string) => {
    switch (category) {
      case '입주 정보':
      case '입주정보':
      case 'info': 
        return 'post-tag-info';
      case '생활 정보':
      case '생활정보':
      case 'life': 
        return 'post-tag-life';
      case '이야기':
      case 'story': 
        return 'post-tag-story';
      default: 
        return 'post-tag-info';
    }
  };

  const isNew = new Date().getTime() - new Date(post.created_at).getTime() < 24 * 60 * 60 * 1000;

  return (
    <div className="post-item flex items-start cursor-pointer">
      <div className="flex-1">
        {/* 카테고리와 제목 (같은 줄) */}
        <div className="post-title flex items-center gap-2 mb-2">
          <span className={`post-tag ${getTagColor(post.metadata?.category || 'info')}`}>
            {post.metadata?.category || '일반'}
          </span>
          <span className="text-var-primary font-medium text-lg">
            {post.title}
          </span>
          {/* 새 게시글 표시 (24시간 이내) */}
          {isNew && (
            <span className="badge-new">NEW</span>
          )}
        </div>
        
        {/* 하단: 태그 및 작성자/시간/통계 */}
        <div className="post-meta flex items-center justify-between text-sm text-var-muted">
          {/* 좌측: 사용자 태그 */}
          <div className="flex items-center gap-1">
            {post.metadata?.tags && post.metadata.tags.length > 0 ? (
              <>
                {post.metadata.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-200"
                  >
                    #{tag}
                  </span>
                ))}
                {post.metadata.tags.length > 3 && (
                  <span className="text-xs text-var-muted px-1">
                    +{post.metadata.tags.length - 3}
                  </span>
                )}
              </>
            ) : (
              <div></div>
            )}
          </div>
          
          {/* 우측: 작성자, 시간, 통계 */}
          <div className="flex items-center gap-2">
            <span className="text-var-secondary">
              {post.author?.display_name || post.author?.user_handle || '익명'}
            </span>
            <span>·</span>
            <span>{formatRelativeTime(post.created_at)}</span>
            <span>·</span>
            <span className="stat-icon text-var-muted">
              👁️ {formatNumber(post.stats?.view_count || post.stats?.views || 0)}
            </span>
            <span className="stat-icon text-var-muted">
              👍 {formatNumber(post.stats?.like_count || post.stats?.likes || 0)}
            </span>
            <span className="stat-icon text-var-muted">
              👎 {formatNumber(post.stats?.dislike_count || post.stats?.dislikes || 0)}
            </span>
            <span className="stat-icon text-var-muted">
              💬 {formatNumber(post.stats?.comment_count || post.stats?.comments || 0)}
            </span>
            <span className="stat-icon text-var-muted">
              🔖 {formatNumber(post.stats?.bookmark_count || post.stats?.bookmarks || 0)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

describe('게시판 컴포넌트 단위 테스트', () => {
  test('게시글 카드 렌더링', () => {
    const mockPost: Post = {
      id: '1',
      title: '테스트 게시글',
      content: '내용',
      slug: 'test-post',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '입주 정보',
        tags: ['태그1', '태그2']
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      author: {
        id: 'user1',
        email: 'test@example.com',
        user_handle: 'testuser',
        display_name: '테스트 사용자',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    };

    render(
      <BrowserRouter>
        <PostCardInBoard post={mockPost} />
      </BrowserRouter>
    );

    // 제목 렌더링 확인
    expect(screen.getByText('테스트 게시글')).toBeInTheDocument();
    
    // 카테고리 표시 확인
    expect(screen.getByText('입주 정보')).toBeInTheDocument();
    
    // 태그 표시 확인
    expect(screen.getByText('#태그1')).toBeInTheDocument();
    expect(screen.getByText('#태그2')).toBeInTheDocument();
    
    // 작성자 표시 확인
    expect(screen.getByText('테스트 사용자')).toBeInTheDocument();
  });

  test('통계 정보(조회수, 좋아요 등) 표시', () => {
    const mockPost: Post = {
      id: '1',
      title: '통계 테스트',
      content: '내용',
      slug: 'stats-test',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '생활 정보'
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      stats: {
        view_count: 1234,
        like_count: 567,
        dislike_count: 89,
        comment_count: 123,
        bookmark_count: 456
      }
    };

    render(
      <BrowserRouter>
        <PostCardInBoard post={mockPost} />
      </BrowserRouter>
    );

    // 통계 숫자 포맷팅 확인
    expect(screen.getByText(/1\.2K/)).toBeInTheDocument(); // 조회수
    expect(screen.getByText(/567/)).toBeInTheDocument(); // 좋아요
    expect(screen.getByText(/89/)).toBeInTheDocument(); // 싫어요
    expect(screen.getByText(/123/)).toBeInTheDocument(); // 댓글
    expect(screen.getByText(/456/)).toBeInTheDocument(); // 북마크
  });

  test('카테고리 태그 색상', () => {
    const categories = [
      { name: '입주 정보', expectedClass: 'post-tag-info' },
      { name: '생활 정보', expectedClass: 'post-tag-life' },
      { name: '이야기', expectedClass: 'post-tag-story' }
    ];

    categories.forEach(({ name, expectedClass }) => {
      const mockPost: Post = {
        id: '1',
        title: '카테고리 테스트',
        content: '내용',
        slug: 'category-test',
        service: 'residential_community',
        metadata: {
          type: 'board',
          category: name
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const { container } = render(
        <BrowserRouter>
          <PostCardInBoard post={mockPost} />
        </BrowserRouter>
      );

      const categoryTag = screen.getByText(name);
      expect(categoryTag).toHaveClass(expectedClass);
      
      // 정리
      container.remove();
    });
  });

  test('NEW 배지 표시 (24시간 이내)', () => {
    const recentPost: Post = {
      id: '1',
      title: '최신 게시글',
      content: '내용',
      slug: 'new-post',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '이야기'
      },
      created_at: new Date().toISOString(), // 현재 시간
      updated_at: new Date().toISOString()
    };

    const oldPost: Post = {
      id: '2',
      title: '오래된 게시글',
      content: '내용',
      slug: 'old-post',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '이야기'
      },
      created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(), // 2일 전
      updated_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString()
    };

    // 최신 게시글 테스트
    const { container: container1 } = render(
      <BrowserRouter>
        <PostCardInBoard post={recentPost} />
      </BrowserRouter>
    );

    expect(screen.getByText('NEW')).toBeInTheDocument();
    container1.remove();

    // 오래된 게시글 테스트
    render(
      <BrowserRouter>
        <PostCardInBoard post={oldPost} />
      </BrowserRouter>
    );

    expect(screen.queryByText('NEW')).not.toBeInTheDocument();
  });

  test('태그가 3개 초과일 때 추가 표시', () => {
    const mockPost: Post = {
      id: '1',
      title: '많은 태그 게시글',
      content: '내용',
      slug: 'many-tags',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '생활 정보',
        tags: ['태그1', '태그2', '태그3', '태그4', '태그5']
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    render(
      <BrowserRouter>
        <PostCardInBoard post={mockPost} />
      </BrowserRouter>
    );

    // 처음 3개 태그만 표시
    expect(screen.getByText('#태그1')).toBeInTheDocument();
    expect(screen.getByText('#태그2')).toBeInTheDocument();
    expect(screen.getByText('#태그3')).toBeInTheDocument();
    
    // 나머지는 숫자로 표시
    expect(screen.getByText('+2')).toBeInTheDocument();
    
    // 4번째, 5번째 태그는 표시되지 않음
    expect(screen.queryByText('#태그4')).not.toBeInTheDocument();
    expect(screen.queryByText('#태그5')).not.toBeInTheDocument();
  });

  test('작성자 정보 없을 때 익명 표시', () => {
    const mockPost: Post = {
      id: '1',
      title: '익명 게시글',
      content: '내용',
      slug: 'anonymous-post',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '이야기'
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
      // author 필드 없음
    };

    render(
      <BrowserRouter>
        <PostCardInBoard post={mockPost} />
      </BrowserRouter>
    );

    expect(screen.getByText('익명')).toBeInTheDocument();
  });

  test('통계 정보 없을 때 0 표시', () => {
    const mockPost: Post = {
      id: '1',
      title: '통계 없는 게시글',
      content: '내용',
      slug: 'no-stats-post',
      service: 'residential_community',
      metadata: {
        type: 'board',
        category: '생활 정보'
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
      // stats 필드 없음
    };

    render(
      <BrowserRouter>
        <PostCardInBoard post={mockPost} />
      </BrowserRouter>
    );

    // 모든 통계가 0으로 표시되는지 확인
    const zeros = screen.getAllByText('0');
    expect(zeros).toHaveLength(5); // 조회수, 좋아요, 싫어요, 댓글, 북마크
  });
});