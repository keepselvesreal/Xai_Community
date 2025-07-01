import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createRemixStub } from '@remix-run/testing';
import Board from '~/routes/board';
import { apiClient } from '~/lib/api';
import type { Post, PaginatedResponse } from '~/types';

// Mock API client
vi.mock('~/lib/api', () => ({
  apiClient: {
    getPosts: vi.fn()
  }
}));

// Mock data
const mockPosts: Post[] = [
  {
    id: '1',
    title: '첫 번째 게시글',
    content: '게시글 내용입니다.',
    slug: 'first-post',
    service: 'residential_community',
    metadata: {
      type: 'board',
      category: '입주 정보',
      tags: ['태그1', '태그2']
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    stats: {
      view_count: 100,
      like_count: 20,
      dislike_count: 2,
      comment_count: 15,
      bookmark_count: 10
    }
  },
  {
    id: '2',
    title: '생활 정보 게시글',
    content: '생활 정보 관련 내용입니다.',
    slug: 'life-info-post',
    service: 'residential_community',
    metadata: {
      type: 'board',
      category: '생활 정보',
      tags: ['생활', '정보']
    },
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1일 전
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    stats: {
      view_count: 50,
      like_count: 10,
      dislike_count: 1,
      comment_count: 5,
      bookmark_count: 3
    }
  },
  {
    id: '3',
    title: '이야기 게시글',
    content: '재미있는 이야기입니다.',
    slug: 'story-post',
    service: 'residential_community',
    metadata: {
      type: 'board',
      category: '이야기',
      tags: ['이야기']
    },
    created_at: new Date(Date.now() - 172800000).toISOString(), // 2일 전
    updated_at: new Date(Date.now() - 172800000).toISOString(),
    stats: {
      view_count: 200,
      like_count: 50,
      dislike_count: 5,
      comment_count: 30,
      bookmark_count: 25
    }
  }
];

const mockResponse: PaginatedResponse<Post> = {
  items: mockPosts,
  total: mockPosts.length,
  page: 1,
  size: 50,
  pages: 1
};

describe('게시판 기능 테스트', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('게시글 목록 조회', async () => {
    // API 응답 설정
    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    // 로딩 상태 확인
    expect(screen.getByRole('status')).toBeInTheDocument();

    // 게시글 목록 렌더링 확인
    await waitFor(() => {
      expect(screen.getByText('첫 번째 게시글')).toBeInTheDocument();
      expect(screen.getByText('생활 정보 게시글')).toBeInTheDocument();
      expect(screen.getByText('이야기 게시글')).toBeInTheDocument();
    });

    // API 호출 확인
    expect(apiClient.getPosts).toHaveBeenCalledWith({
      service: 'residential_community',
      metadata_type: 'board',
      sortBy: 'created_at',
      page: 1,
      size: 50
    });
  });

  test('카테고리별 필터링', async () => {
    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    await waitFor(() => {
      expect(screen.getByText('첫 번째 게시글')).toBeInTheDocument();
    });

    // 생활 정보 카테고리 필터 클릭
    const lifeButton = screen.getByRole('button', { name: '생활 정보' });
    fireEvent.click(lifeButton);

    // 생활 정보 게시글만 표시되는지 확인
    await waitFor(() => {
      expect(screen.getByText('생활 정보 게시글')).toBeInTheDocument();
      expect(screen.queryByText('첫 번째 게시글')).not.toBeInTheDocument();
      expect(screen.queryByText('이야기 게시글')).not.toBeInTheDocument();
    });

    // 전체 카테고리로 복귀
    const allButton = screen.getByRole('button', { name: '전체' });
    fireEvent.click(allButton);

    await waitFor(() => {
      expect(screen.getByText('첫 번째 게시글')).toBeInTheDocument();
      expect(screen.getByText('생활 정보 게시글')).toBeInTheDocument();
      expect(screen.getByText('이야기 게시글')).toBeInTheDocument();
    });
  });

  test('검색 기능', async () => {
    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    await waitFor(() => {
      expect(screen.getByText('첫 번째 게시글')).toBeInTheDocument();
    });

    // 검색어 입력
    const searchInput = screen.getByPlaceholderText('게시글 검색...');
    fireEvent.change(searchInput, { target: { value: '생활' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

    // 검색 결과 확인
    await waitFor(() => {
      expect(screen.getByText('생활 정보 게시글')).toBeInTheDocument();
      expect(screen.queryByText('첫 번째 게시글')).not.toBeInTheDocument();
      expect(screen.queryByText('이야기 게시글')).not.toBeInTheDocument();
    });
  });

  test('정렬 기능', async () => {
    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    await waitFor(() => {
      expect(screen.getByText('첫 번째 게시글')).toBeInTheDocument();
    });

    // 조회수순 정렬 선택
    const sortSelect = screen.getByRole('combobox');
    fireEvent.change(sortSelect, { target: { value: 'views' } });

    // 정렬 결과 확인 (조회수가 많은 순서대로)
    await waitFor(() => {
      const posts = screen.getAllByRole('article');
      expect(posts[0]).toHaveTextContent('이야기 게시글'); // 200 views
      expect(posts[1]).toHaveTextContent('첫 번째 게시글'); // 100 views
      expect(posts[2]).toHaveTextContent('생활 정보 게시글'); // 50 views
    });
  });

  test('로딩 및 에러 상태', async () => {
    // 에러 응답 설정
    vi.mocked(apiClient.getPosts).mockRejectedValueOnce(
      new Error('네트워크 오류')
    );

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    // 로딩 상태 확인
    expect(screen.getByRole('status')).toBeInTheDocument();

    // 에러 상태 확인
    await waitFor(() => {
      expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
      expect(screen.getByText(/네트워크 오류/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '다시 시도' })).toBeInTheDocument();
    });

    // 다시 시도 버튼 클릭
    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    fireEvent.click(screen.getByRole('button', { name: '다시 시도' }));

    // 성공적으로 로드되는지 확인
    await waitFor(() => {
      expect(screen.getByText('첫 번째 게시글')).toBeInTheDocument();
    });
  });

  test('빈 목록 상태', async () => {
    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: {
        items: [],
        total: 0,
        page: 1,
        size: 50,
        pages: 0
      },
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    // 빈 상태 메시지 확인
    await waitFor(() => {
      expect(screen.getByText('게시글이 없습니다')).toBeInTheDocument();
      expect(screen.getByText('첫 번째 게시글을 작성해보세요!')).toBeInTheDocument();
    });
  });

  test('NEW 배지 표시 (24시간 이내 게시글)', async () => {
    const recentPost: Post = {
      ...mockPosts[0],
      id: '4',
      title: '방금 작성한 게시글',
      created_at: new Date().toISOString() // 현재 시간
    };

    vi.mocked(apiClient.getPosts).mockResolvedValueOnce({
      success: true,
      data: {
        ...mockResponse,
        items: [recentPost, ...mockPosts]
      },
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/board',
        Component: Board
      }
    ]);

    render(<RemixStub initialEntries={['/board']} />);

    await waitFor(() => {
      expect(screen.getByText('방금 작성한 게시글')).toBeInTheDocument();
      // NEW 배지가 최근 게시글에만 표시되는지 확인
      const recentPostElement = screen.getByText('방금 작성한 게시글').closest('div');
      expect(recentPostElement).toHaveTextContent('NEW');
    });
  });
});