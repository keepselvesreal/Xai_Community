/**
 * 입주 서비스 업체 목록 페이지 확장 통계 표시 테스트
 * 
 * TDD Red 단계 - 실패하는 테스트 작성
 */

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RemixStub } from '@remix-run/testing';
import ServicesPage from '../../app/routes/services';

// Mock API 함수들
const mockListPosts = vi.fn();

// API 모킹
vi.mock('../../app/lib/api', () => ({
  api: {
    listPosts: (...args: any[]) => mockListPosts(...args),
  }
}));

// 테스트용 서비스 목록 데이터 (확장 통계 포함)
const mockServicesListData = {
  items: [
    {
      _id: 'service-1',
      slug: 'cleaning-service-1',
      title: '프리미엄 청소 서비스',
      metadata: {
        type: 'moving services',
        category: '청소',
        company_info: {
          company_name: '프리미엄 청소',
          contact_phone: '010-1111-2222'
        }
      },
      stats: {
        view_count: 250,
        like_count: 15,
        dislike_count: 2,
        comment_count: 18,
        bookmark_count: 25
      },
      // 확장 통계 (목록 API에서 추가로 제공되어야 함)
      extended_stats: {
        inquiry_count: 8,
        review_count: 10,
        general_comment_count: 0
      },
      author: {
        user_handle: 'premium_clean',
        display_name: '프리미엄 청소'
      },
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      _id: 'service-2',
      slug: 'moving-service-1', 
      title: '안전한 이사 서비스',
      metadata: {
        type: 'moving services',
        category: '이사',
        company_info: {
          company_name: '안전이사',
          contact_phone: '010-3333-4444'
        }
      },
      stats: {
        view_count: 180,
        like_count: 12,
        dislike_count: 1,
        comment_count: 15,
        bookmark_count: 20
      },
      extended_stats: {
        inquiry_count: 12,
        review_count: 3,
        general_comment_count: 0
      },
      author: {
        user_handle: 'safe_moving',
        display_name: '안전이사'
      },
      created_at: '2024-01-02T00:00:00Z'
    }
  ],
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1
};

// Mock loader 데이터
const mockLoaderData = {
  posts: mockServicesListData,
  pageTitle: '입주 서비스 업체',
  searchParams: {
    category: undefined,
    sort: 'latest',
    search: ''
  }
};

describe('ServicesPage 확장 통계 표시', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListPosts.mockResolvedValue(mockServicesListData);
  });

  it('서비스 목록에서 관심 수가 표시되어야 한다', async () => {
    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services']}
        initialLoaderData={{
          'routes/services': mockLoaderData
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 첫 번째 서비스의 관심 수 확인
    expect(screen.getByText(/관심 25/)).toBeInTheDocument();
    
    // 두 번째 서비스의 관심 수 확인
    expect(screen.getByText(/관심 20/)).toBeInTheDocument();
  });

  it('서비스 목록에서 문의 수가 표시되어야 한다', async () => {
    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services']}
        initialLoaderData={{
          'routes/services': mockLoaderData
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 첫 번째 서비스의 문의 수 확인
    expect(screen.getByText(/문의 8/)).toBeInTheDocument();
    
    // 두 번째 서비스의 문의 수 확인
    expect(screen.getByText(/문의 12/)).toBeInTheDocument();
  });

  it('서비스 목록에서 후기 수가 표시되어야 한다', async () => {
    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services']}
        initialLoaderData={{
          'routes/services': mockLoaderData
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 첫 번째 서비스의 후기 수 확인
    expect(screen.getByText(/후기 10/)).toBeInTheDocument();
    
    // 두 번째 서비스의 후기 수 확인  
    expect(screen.getByText(/후기 3/)).toBeInTheDocument();
  });

  it('기존 통계와 확장 통계가 모두 표시되어야 한다', async () => {
    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services']}
        initialLoaderData={{
          'routes/services': mockLoaderData
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 첫 번째 서비스의 모든 통계 확인
    expect(screen.getByText(/조회 250/)).toBeInTheDocument();
    expect(screen.getByText(/관심 25/)).toBeInTheDocument();
    expect(screen.getByText(/문의 8/)).toBeInTheDocument();
    expect(screen.getByText(/후기 10/)).toBeInTheDocument();
  });

  it('문의수 기준 정렬이 동작해야 한다', async () => {
    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services?sort=inquiry_count']}
        initialLoaderData={{
          'routes/services': {
            ...mockLoaderData,
            searchParams: {
              ...mockLoaderData.searchParams,
              sort: 'inquiry_count'
            }
          }
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 정렬 옵션에서 문의수가 선택되어 있는지 확인
    const sortSelect = screen.getByRole('combobox', { name: /정렬/ });
    expect(sortSelect).toHaveValue('inquiry_count');
  });

  it('후기수 기준 정렬이 동작해야 한다', async () => {
    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services?sort=review_count']}
        initialLoaderData={{
          'routes/services': {
            ...mockLoaderData,
            searchParams: {
              ...mockLoaderData.searchParams,
              sort: 'review_count'
            }
          }
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 정렬 옵션에서 후기수가 선택되어 있는지 확인
    const sortSelect = screen.getByRole('combobox', { name: /정렬/ });
    expect(sortSelect).toHaveValue('review_count');
  });

  it('확장 통계가 없는 경우 0으로 표시되어야 한다', async () => {
    const dataWithoutExtendedStats = {
      ...mockServicesListData,
      items: mockServicesListData.items.map(item => ({
        ...item,
        extended_stats: undefined
      }))
    };

    const RemixStubApp = () => (
      <RemixStub
        initialEntries={['/services']}
        initialLoaderData={{
          'routes/services': {
            ...mockLoaderData,
            posts: dataWithoutExtendedStats
          }
        }}
      >
        <ServicesPage />
      </RemixStub>
    );

    render(<RemixStubApp />);

    // 확장 통계가 없을 때 0으로 표시되는지 확인
    expect(screen.getByText(/문의 0/)).toBeInTheDocument();
    expect(screen.getByText(/후기 0/)).toBeInTheDocument();
  });
});