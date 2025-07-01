import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ItemCard } from '~/components/common/ItemCard';
import type { BaseListItem } from '~/types/listTypes';

// 테스트용 아이템 타입들
interface TestPost extends BaseListItem {
  content: string;
  category: string;
}

interface TestService extends BaseListItem {
  description: string;
  rating: number;
}

interface TestTip extends BaseListItem {
  expert_name: string;
  tags: string[];
}

describe('ItemCard 컴포넌트', () => {
  test('다양한 아이템 타입 렌더링 - Post 타입', () => {
    const post: TestPost = {
      id: '1',
      title: '게시글 제목',
      created_at: '2024-01-01T00:00:00Z',
      content: '게시글 내용',
      category: '일반',
      stats: {
        view_count: 100,
        like_count: 20,
        dislike_count: 2,
        comment_count: 15,
        bookmark_count: 10
      }
    };

    const renderCard = (item: TestPost) => (
      <div data-testid="post-card">
        <h3>{item.title}</h3>
        <p>{item.content}</p>
        <span>{item.category}</span>
      </div>
    );

    render(<ItemCard item={post} renderCard={renderCard} />);

    expect(screen.getByTestId('post-card')).toBeInTheDocument();
    expect(screen.getByText('게시글 제목')).toBeInTheDocument();
    expect(screen.getByText('게시글 내용')).toBeInTheDocument();
    expect(screen.getByText('일반')).toBeInTheDocument();
  });

  test('다양한 아이템 타입 렌더링 - Service 타입', () => {
    const service: TestService = {
      id: '2',
      title: '빠른이사 서비스',
      created_at: '2024-01-01T00:00:00Z',
      description: '안전하고 빠른 이사',
      rating: 4.8,
      stats: {
        view_count: 50
      }
    };

    const renderCard = (item: TestService) => (
      <div data-testid="service-card">
        <h3>{item.title}</h3>
        <p>{item.description}</p>
        <span>평점: {item.rating}</span>
      </div>
    );

    render(<ItemCard item={service} renderCard={renderCard} />);

    expect(screen.getByTestId('service-card')).toBeInTheDocument();
    expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
    expect(screen.getByText('안전하고 빠른 이사')).toBeInTheDocument();
    expect(screen.getByText('평점: 4.8')).toBeInTheDocument();
  });

  test('다양한 아이템 타입 렌더링 - Tip 타입', () => {
    const tip: TestTip = {
      id: '3',
      title: '겨울철 난방비 절약법',
      created_at: '2024-01-01T00:00:00Z',
      expert_name: '김전문가',
      tags: ['#절약', '#난방'],
      stats: {
        view_count: 200,
        like_count: 50
      }
    };

    const renderCard = (item: TestTip) => (
      <div data-testid="tip-card">
        <h3>{item.title}</h3>
        <p>전문가: {item.expert_name}</p>
        <div>
          {item.tags.map(tag => <span key={tag}>{tag}</span>)}
        </div>
      </div>
    );

    render(<ItemCard item={tip} renderCard={renderCard} />);

    expect(screen.getByTestId('tip-card')).toBeInTheDocument();
    expect(screen.getByText('겨울철 난방비 절약법')).toBeInTheDocument();
    expect(screen.getByText('전문가: 김전문가')).toBeInTheDocument();
    expect(screen.getByText('#절약')).toBeInTheDocument();
    expect(screen.getByText('#난방')).toBeInTheDocument();
  });

  test('통계 정보 표시', () => {
    const item: TestPost = {
      id: '1',
      title: '통계 테스트',
      created_at: '2024-01-01T00:00:00Z',
      content: '내용',
      category: '일반',
      stats: {
        view_count: 1234,
        like_count: 567,
        dislike_count: 89,
        comment_count: 123,
        bookmark_count: 456
      }
    };

    const renderCard = (item: TestPost) => (
      <div data-testid="stats-card">
        <div>조회수: {item.stats?.view_count}</div>
        <div>좋아요: {item.stats?.like_count}</div>
        <div>싫어요: {item.stats?.dislike_count}</div>
        <div>댓글: {item.stats?.comment_count}</div>
        <div>북마크: {item.stats?.bookmark_count}</div>
      </div>
    );

    render(<ItemCard item={item} renderCard={renderCard} />);

    expect(screen.getByText('조회수: 1234')).toBeInTheDocument();
    expect(screen.getByText('좋아요: 567')).toBeInTheDocument();
    expect(screen.getByText('싫어요: 89')).toBeInTheDocument();
    expect(screen.getByText('댓글: 123')).toBeInTheDocument();
    expect(screen.getByText('북마크: 456')).toBeInTheDocument();
  });

  test('클릭 이벤트 테스트', () => {
    const item: TestPost = {
      id: '1',
      title: '클릭 테스트',
      created_at: '2024-01-01T00:00:00Z',
      content: '내용',
      category: '일반'
    };

    const renderCard = (item: TestPost) => (
      <div data-testid="clickable-card">
        <h3>{item.title}</h3>
      </div>
    );

    const onClick = vi.fn();

    render(<ItemCard item={item} renderCard={renderCard} onClick={onClick} />);

    const card = screen.getByTestId('clickable-card');
    fireEvent.click(card);

    expect(onClick).toHaveBeenCalledWith(item);
  });

  test('클릭 핸들러가 없을 때', () => {
    const item: TestPost = {
      id: '1',
      title: '클릭 불가',
      created_at: '2024-01-01T00:00:00Z',
      content: '내용',
      category: '일반'
    };

    const renderCard = (item: TestPost) => (
      <div data-testid="non-clickable-card">
        <h3>{item.title}</h3>
      </div>
    );

    const { container } = render(<ItemCard item={item} renderCard={renderCard} />);

    // 클릭 핸들러가 없으면 cursor-pointer 클래스가 없어야 함
    expect(container.firstChild).not.toHaveClass('cursor-pointer');
  });

  test('통계 정보가 없을 때', () => {
    const item: TestPost = {
      id: '1',
      title: '통계 없음',
      created_at: '2024-01-01T00:00:00Z',
      content: '내용',
      category: '일반'
      // stats 필드 없음
    };

    const renderCard = (item: TestPost) => (
      <div data-testid="no-stats-card">
        <h3>{item.title}</h3>
        <div>조회수: {item.stats?.view_count || 0}</div>
      </div>
    );

    render(<ItemCard item={item} renderCard={renderCard} />);

    expect(screen.getByText('조회수: 0')).toBeInTheDocument();
  });
});