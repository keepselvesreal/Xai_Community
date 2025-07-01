import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { createRemixStub } from '@remix-run/testing';
import Services from '~/routes/services';
import { fetchServices, fetchServicesByCategory, searchServices } from '~/lib/services-api';
import type { MockService } from '~/types';
import type { Post, PaginatedResponse } from '~/types';

// Mock API functions
vi.mock('~/lib/services-api', () => ({
  fetchServices: vi.fn(),
  fetchServicesByCategory: vi.fn(),
  searchServices: vi.fn(),
  convertPostsToServiceResponses: vi.fn((posts) => posts.map(post => ({
    ...post,
    serviceData: JSON.parse(post.content),
    originalContent: post.content
  }))),
  convertServicePostToMockService: vi.fn()
}));

// Mock 서비스 데이터
const mockServicePost1: Post = {
  id: '1',
  title: '이사 서비스',
  content: JSON.stringify({
    company: {
      name: '빠른이사 서비스',
      description: '빠르고 안전한 이사 서비스를 제공합니다.',
      contact: '02-3456-7890',
      availableHours: '평일 08:00-20:00'
    },
    services: [
      { name: '원룸 이사', price: 150000, description: '원룸 이사 서비스' },
      { name: '투룸 이사', price: 250000, specialPrice: 300000, description: '투룸 이사 서비스' }
    ]
  }),
  slug: 'moving-service-1',
  service: 'residential_community',
  metadata: {
    type: 'service',
    category: '이사'
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  stats: {
    view_count: 89,
    like_count: 15,
    dislike_count: 1,
    comment_count: 5,
    bookmark_count: 10
  }
};

const mockServicePost2: Post = {
  id: '2',
  title: '청소 서비스',
  content: JSON.stringify({
    company: {
      name: '청준 청소 대행',
      description: '아파트 전문 청소 서비스를 제공합니다.',
      contact: '02-8765-4321',
      availableHours: '평일 09:00-18:00'
    },
    services: [
      { name: '의류 청소', price: 35000, description: '의류 전문 청소' }
    ]
  }),
  slug: 'cleaning-service-1',
  service: 'residential_community',
  metadata: {
    type: 'service',
    category: '청소'
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  stats: {
    view_count: 67,
    like_count: 12,
    dislike_count: 0,
    comment_count: 3,
    bookmark_count: 8
  }
};

const mockServicePost3: Post = {
  id: '3',
  title: '에어컨 서비스',
  content: JSON.stringify({
    company: {
      name: '시원한 에어컨 서비스',
      description: '에어컨 전문 설치, 수리, 청소 서비스를 제공합니다.',
      contact: '02-9876-5432',
      availableHours: '평일 09:00-18:00'
    },
    services: [
      { name: '에어컨 청소', price: 80000, description: '에어컨 전문 청소' },
      { name: '에어컨 설치', price: 120000, specialPrice: 150000, description: '에어컨 설치 서비스' }
    ]
  }),
  slug: 'aircon-service-1',
  service: 'residential_community',
  metadata: {
    type: 'service',
    category: '에어컨'
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  stats: {
    view_count: 234,
    like_count: 45,
    dislike_count: 2,
    comment_count: 15,
    bookmark_count: 30
  }
};

const mockResponse: PaginatedResponse<Post> = {
  items: [mockServicePost1, mockServicePost2, mockServicePost3],
  total: 3,
  page: 1,
  size: 50,
  pages: 1
};

describe('입주업체서비스 기능 테스트', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('서비스 목록 조회', async () => {
    // API 응답 설정
    vi.mocked(fetchServices).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    // 서비스 목록이 렌더링되는지 확인
    await waitFor(() => {
      expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
      expect(screen.getByText('청준 청소 대행')).toBeInTheDocument();
      expect(screen.getByText('시원한 에어컨 서비스')).toBeInTheDocument();
    });

    // API 호출 확인
    expect(fetchServices).toHaveBeenCalledWith({ page: 1, size: 50 });
  });

  test('카테고리별 필터링 - 이사', async () => {
    // 초기 목록 로드
    vi.mocked(fetchServices).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    // 이사 카테고리 필터링 응답
    vi.mocked(fetchServicesByCategory).mockResolvedValueOnce({
      success: true,
      data: {
        items: [mockServicePost1],
        total: 1,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    await waitFor(() => {
      expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
    });

    // 이사 카테고리 필터 클릭
    const movingButton = screen.getByRole('button', { name: '이사' });
    fireEvent.click(movingButton);

    // 이사 서비스만 표시되는지 확인
    await waitFor(() => {
      expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
      expect(screen.queryByText('청준 청소 대행')).not.toBeInTheDocument();
      expect(screen.queryByText('시원한 에어컨 서비스')).not.toBeInTheDocument();
    });

    expect(fetchServicesByCategory).toHaveBeenCalledWith('이사', { page: 1, size: 50 });
  });

  test('검색 기능', async () => {
    // 초기 목록 로드
    vi.mocked(fetchServices).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    // 검색 결과
    vi.mocked(searchServices).mockResolvedValueOnce({
      success: true,
      data: {
        items: [mockServicePost3],
        total: 1,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    await waitFor(() => {
      expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
    });

    // 검색어 입력 및 제출
    const searchInput = screen.getByPlaceholderText('서비스 검색...');
    fireEvent.change(searchInput, { target: { value: '에어컨' } });
    
    const searchForm = searchInput.closest('form');
    fireEvent.submit(searchForm!);

    // 검색 결과 확인
    await waitFor(() => {
      expect(screen.getByText('시원한 에어컨 서비스')).toBeInTheDocument();
      expect(screen.queryByText('빠른이사 서비스')).not.toBeInTheDocument();
      expect(screen.queryByText('청준 청소 대행')).not.toBeInTheDocument();
    });

    expect(searchServices).toHaveBeenCalledWith('에어컨', { page: 1, size: 50 });
  });

  test('정렬 기능 - 조회수순', async () => {
    vi.mocked(fetchServices).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    await waitFor(() => {
      expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
    });

    // 조회수순 정렬 선택
    const sortSelect = screen.getByRole('combobox');
    fireEvent.change(sortSelect, { target: { value: 'views' } });

    // 정렬 결과 확인 (조회수가 많은 순서대로)
    await waitFor(() => {
      const serviceCards = screen.getAllByRole('article').filter(el => 
        el.textContent?.includes('서비스')
      );
      expect(serviceCards[0]).toHaveTextContent('시원한 에어컨 서비스'); // 234 views
      expect(serviceCards[1]).toHaveTextContent('빠른이사 서비스'); // 89 views
      expect(serviceCards[2]).toHaveTextContent('청준 청소 대행'); // 67 views
    });
  });

  test('서비스 카드 정보 표시', async () => {
    vi.mocked(fetchServices).mockResolvedValueOnce({
      success: true,
      data: {
        items: [mockServicePost1],
        total: 1,
        page: 1,
        size: 50,
        pages: 1
      },
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    await waitFor(() => {
      // 업체명
      expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
      
      // 서비스 항목
      expect(screen.getByText('원룸 이사')).toBeInTheDocument();
      expect(screen.getByText('150,000원')).toBeInTheDocument();
      expect(screen.getByText('투룸 이사')).toBeInTheDocument();
      expect(screen.getByText('250,000원')).toBeInTheDocument();
      
      // 연락처
      expect(screen.getByText('02-3456-7890')).toBeInTheDocument();
      expect(screen.getByText('평일 08:00-20:00')).toBeInTheDocument();
      
      // 통계 정보
      expect(screen.getByText(/89/)).toBeInTheDocument(); // 조회수
      expect(screen.getByText(/문의 10/)).toBeInTheDocument(); // 문의수
    });
  });

  test('빈 목록 상태', async () => {
    vi.mocked(fetchServices).mockResolvedValueOnce({
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
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    // 빈 상태 메시지 확인
    await waitFor(() => {
      expect(screen.getByText('서비스가 없습니다')).toBeInTheDocument();
      expect(screen.getByText('등록된 서비스가 없습니다.')).toBeInTheDocument();
    });
  });

  test('API 오류 처리', async () => {
    vi.mocked(fetchServices).mockRejectedValueOnce(
      new Error('서버 연결 실패')
    );

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    // 에러 메시지 확인
    await waitFor(() => {
      expect(screen.getByText(/서비스 데이터를 불러올 수 없어 기본 데이터를 표시합니다/)).toBeInTheDocument();
    });
  });

  test('업체 등록 버튼', async () => {
    vi.mocked(fetchServices).mockResolvedValueOnce({
      success: true,
      data: mockResponse,
      timestamp: new Date().toISOString()
    });

    const RemixStub = createRemixStub([
      {
        path: '/services',
        Component: Services
      }
    ]);

    render(<RemixStub initialEntries={['/services']} />);

    // 업체 등록 버튼 확인
    const registerButton = screen.getByRole('link', { name: '📝 업체 등록' });
    expect(registerButton).toBeInTheDocument();
    expect(registerButton).toHaveAttribute('href', '/services/write');
  });
});