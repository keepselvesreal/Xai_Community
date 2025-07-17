import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import GridPageLayout from '~/components/common/GridPageLayout';
import AuthContext from '~/contexts/AuthContext';
import NotificationContext from '~/contexts/NotificationContext';

// Mock 컴포넌트
vi.mock('~/components/layout/AppLayout', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div data-testid="app-layout">{children}</div>
}));

vi.mock('~/components/common/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>
}));

// Mock 데이터
const mockMovingServicesItems = [
  {
    id: '1',
    slug: 'service-1',
    title: '깔끔한 이사 서비스',
    category: '이사',
    verified: true,
    services: [
      { name: '원룸 이사', price: 80000, specialPrice: 60000 },
      { name: '투룸 이사', price: 120000, specialPrice: null },
      { name: '포장 서비스', price: 50000, specialPrice: 40000 }
    ],
    contact: {
      phone: '010-1234-5678',
      hours: '09:00-18:00'
    },
    stats: {
      views: 1250,
      bookmarks: 89,
      inquiries: 23,
      reviews: 45
    }
  },
  {
    id: '2',
    slug: 'service-2',
    title: '프리미엄 청소 전문',
    category: '청소',
    verified: false,
    services: [
      { name: '입주 청소', price: 150000, specialPrice: 120000 }
    ],
    contact: {
      phone: '010-9876-5432',
      hours: '08:00-19:00'
    },
    stats: {
      views: 890,
      bookmarks: 67,
      inquiries: 18,
      reviews: 34
    }
  }
];

const mockExpertTipsItems = [
  {
    id: '1',
    slug: 'tip-1',
    title: '욕실 곰팡이 완벽 제거하는 천연 세제 만들기',
    category: '청소/정리',
    isNew: true,
    expertIcon: '👨‍🔬',
    expertName: '청소 전문가 김정리',
    tags: ['곰팡이제거', '천연세제', '욕실청소'],
    stats: {
      views: 1234,
      likes: 89,
      dislikes: 12,
      comments: 23,
      bookmarks: 45
    }
  },
  {
    id: '2',
    slug: 'tip-2',
    title: '작은 공간을 넓어 보이게 하는 조명 배치 노하우',
    category: '인테리어',
    isNew: false,
    expertIcon: '💡',
    expertName: '인테리어 디자이너 박설계',
    tags: ['조명', '공간활용', '인테리어팁'],
    stats: {
      views: 856,
      likes: 67,
      dislikes: 8,
      comments: 15,
      bookmarks: 32
    }
  }
];

const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@test.com'
};

// 테스트용 Wrapper 컴포넌트
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const authContextValue = {
    user: mockUser,
    login: vi.fn(),
    logout: vi.fn(),
    loading: false
  };

  const notificationContextValue = {
    showSuccess: vi.fn(),
    showError: vi.fn(),
    showInfo: vi.fn(),
    showWarning: vi.fn()
  };

  return (
    <BrowserRouter>
      <AuthContext.Provider value={authContextValue}>
        <NotificationContext.Provider value={notificationContextValue}>
          {children}
        </NotificationContext.Provider>
      </AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('GridPageLayout', () => {
  const defaultProps = {
    pageType: 'moving-services' as const,
    items: mockMovingServicesItems,
    onSearch: vi.fn(),
    onFilter: vi.fn(),
    onSort: vi.fn(),
    onLoadMore: vi.fn(),
    onActionClick: vi.fn(),
    user: mockUser,
    onLogout: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('컴포넌트 렌더링', () => {
    it('입주 서비스 페이지 타입으로 렌더링된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('📝 업체 등록하기')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('서비스 검색...')).toBeInTheDocument();
    });

    it('전문가 꿀정보 페이지 타입으로 렌더링된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout 
            {...defaultProps} 
            pageType="expert-tips"
            items={mockExpertTipsItems}
          />
        </TestWrapper>
      );

      expect(screen.getByText('✏️ 글쓰기')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('전문가 꿀정보를 검색하세요...')).toBeInTheDocument();
    });
  });

  describe('검색 기능', () => {
    it('검색어 입력 시 onSearch 콜백이 호출된다', async () => {
      const onSearch = vi.fn();
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} onSearch={onSearch} />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('서비스 검색...');
      fireEvent.change(searchInput, { target: { value: '이사' } });

      await waitFor(() => {
        expect(onSearch).toHaveBeenCalledWith('이사');
      });
    });
  });

  describe('필터 기능', () => {
    it('필터 버튼들이 올바르게 렌더링된다 - 입주 서비스', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      // 필터 버튼 영역에서만 확인
      const filterSection = screen.getByText('전체').closest('.flex.gap-2.flex-wrap');
      expect(filterSection).toBeInTheDocument();
      
      expect(screen.getByRole('button', { name: '전체' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '이사' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '청소' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '에어컨' })).toBeInTheDocument();
    });

    it('필터 버튼들이 올바르게 렌더링된다 - 전문가 꿀정보', () => {
      render(
        <TestWrapper>
          <GridPageLayout 
            {...defaultProps} 
            pageType="expert-tips"
            items={mockExpertTipsItems}
          />
        </TestWrapper>
      );

      expect(screen.getByRole('button', { name: '전체' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '청소/정리' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '인테리어' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '생활' })).toBeInTheDocument();
    });

    it('필터 버튼 클릭 시 onFilter 콜백이 호출된다', () => {
      const onFilter = vi.fn();
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} onFilter={onFilter} />
        </TestWrapper>
      );

      fireEvent.click(screen.getByRole('button', { name: '이사' }));
      expect(onFilter).toHaveBeenCalledWith('이사');
    });

    it('활성 필터가 올바르게 표시된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} activeFilter="이사" />
        </TestWrapper>
      );

      const activeButton = screen.getByRole('button', { name: '이사' });
      expect(activeButton).toHaveClass('bg-blue-500', 'text-white');
    });
  });

  describe('정렬 기능', () => {
    it('정렬 옵션들이 올바르게 렌더링된다 - 입주 서비스', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      const sortSelect = screen.getByRole('combobox');
      expect(sortSelect).toBeInTheDocument();
      
      // 옵션들 확인 - select 내부의 option 요소들 확인
      expect(screen.getByDisplayValue('최신순')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '조회수' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '관심순' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '후기순' })).toBeInTheDocument();
    });

    it('정렬 변경 시 onSort 콜백이 호출된다', () => {
      const onSort = vi.fn();
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} onSort={onSort} />
        </TestWrapper>
      );

      const sortSelect = screen.getByRole('combobox');
      fireEvent.change(sortSelect, { target: { value: 'views' } });
      
      expect(onSort).toHaveBeenCalledWith('views');
    });
  });

  describe('카드 렌더링', () => {
    it('입주 서비스 카드가 올바르게 렌더링된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      // 첫 번째 서비스 카드 확인
      expect(screen.getByText('깔끔한 이사 서비스 ⭐')).toBeInTheDocument();
      expect(screen.getAllByText('이사')[1]).toBeInTheDocument(); // 카드 내 카테고리 태그
      expect(screen.getByText('경험有')).toBeInTheDocument();
      expect(screen.getByText('원룸 이사')).toBeInTheDocument();
      expect(screen.getByText('010-1234-5678')).toBeInTheDocument();
      expect(screen.getByText('09:00-18:00')).toBeInTheDocument();
    });

    it('전문가 꿀정보 카드가 올바르게 렌더링된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout 
            {...defaultProps} 
            pageType="expert-tips"
            items={mockExpertTipsItems}
          />
        </TestWrapper>
      );

      expect(screen.getByText('욕실 곰팡이 완벽 제거하는 천연 세제 만들기')).toBeInTheDocument();
      expect(screen.getAllByText('청소/정리')[1]).toBeInTheDocument(); // 카드 내 카테고리 배지
      expect(screen.getByText('NEW')).toBeInTheDocument();
      expect(screen.getByText('청소 전문가 김정리')).toBeInTheDocument();
      expect(screen.getByText('#곰팡이제거')).toBeInTheDocument();
    });

    it('통계 정보가 올바르게 표시된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      // 카드 통계 정보가 올바르게 표시되는지 확인
      expect(screen.getByText(/👁️ 890/)).toBeInTheDocument(); // 조회수
      expect(screen.getByText(/관심 67/)).toBeInTheDocument(); // 관심
      expect(screen.getByText(/문의 18/)).toBeInTheDocument(); // 문의  
      expect(screen.getByText(/후기 34/)).toBeInTheDocument(); // 후기
    });
  });

  describe('더보기 기능', () => {
    it('hasMore가 true일 때 더보기 버튼이 표시된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} hasMore={true} />
        </TestWrapper>
      );

      expect(screen.getByText('더보기')).toBeInTheDocument();
    });

    it('더보기 버튼 클릭 시 onLoadMore 콜백이 호출된다', () => {
      const onLoadMore = vi.fn();
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} hasMore={true} onLoadMore={onLoadMore} />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('더보기'));
      expect(onLoadMore).toHaveBeenCalled();
    });

    it('hasMore가 false일 때 더보기 버튼이 표시되지 않는다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} hasMore={false} />
        </TestWrapper>
      );

      expect(screen.queryByText('더보기')).not.toBeInTheDocument();
    });
  });

  describe('로딩 상태', () => {
    it('loading이 true일 때 로딩 스피너가 표시된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} loading={true} />
        </TestWrapper>
      );

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });
  });

  describe('빈 상태', () => {
    it('아이템이 없을 때 빈 상태 메시지가 표시된다 - 입주 서비스', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} items={[]} />
        </TestWrapper>
      );

      expect(screen.getByText('등록된 서비스가 없습니다')).toBeInTheDocument();
      expect(screen.getByText('첫 번째 서비스를 등록해보세요!')).toBeInTheDocument();
    });

    it('아이템이 없을 때 빈 상태 메시지가 표시된다 - 전문가 꿀정보', () => {
      render(
        <TestWrapper>
          <GridPageLayout 
            {...defaultProps} 
            pageType="expert-tips"
            items={[]}
          />
        </TestWrapper>
      );

      expect(screen.getByText('작성된 꿀정보가 없습니다')).toBeInTheDocument();
      expect(screen.getByText('첫 번째 꿀정보를 작성해보세요!')).toBeInTheDocument();
    });
  });

  describe('액션 버튼', () => {
    it('액션 버튼 클릭 시 onActionClick 콜백이 호출된다', () => {
      const onActionClick = vi.fn();
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} onActionClick={onActionClick} />
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('📝 업체 등록하기'));
      expect(onActionClick).toHaveBeenCalled();
    });
  });

  describe('반응형 그리드', () => {
    it('그리드 레이아웃이 올바르게 적용된다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      const gridContainer = screen.getByRole('main').querySelector('.grid');
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
    });
  });

  describe('행별 색상 시스템', () => {
    it('카드들이 행별로 다른 색상 클래스를 가진다', () => {
      render(
        <TestWrapper>
          <GridPageLayout {...defaultProps} />
        </TestWrapper>
      );

      // 첫 번째 카드 (인덱스 0) - row-1
      const firstCard = screen.getByText('깔끔한 이사 서비스 ⭐').closest('.service-card');
      expect(firstCard).toHaveClass('row-1');

      // 두 번째 카드 (인덱스 1) - row-1 (같은 행)
      const secondCard = screen.getByText('프리미엄 청소 전문 ⭐').closest('.service-card');
      expect(secondCard).toHaveClass('row-1');
    });
  });
});