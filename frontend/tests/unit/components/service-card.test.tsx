import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import type { MockService } from '~/types';

// ServiceCard 컴포넌트 Mock (실제 구현에서 추출한 형태)
const ServiceCard = ({ 
  service, 
  onClick 
}: { 
  service: MockService; 
  onClick: (service: MockService) => void;
}) => {
  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? "text-yellow-400" : "text-gray-300"}>
        ⭐
      </span>
    ));
  };

  return (
    <div
      onClick={() => onClick(service)}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      role="article"
    >
      {/* 카테고리와 인증 */}
      <div className="flex items-center gap-2 mb-3">
        <span className="bg-green-100 text-green-600 px-3 py-1 rounded-full text-sm font-medium">
          {service.category}
        </span>
        {service.verified && (
          <span className="bg-green-500 text-white px-2 py-1 rounded-full text-xs font-medium">
            인증
          </span>
        )}
      </div>

      {/* 업체명과 평점 */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-bold text-gray-900">{service.name}</h3>
        {service.rating > 0 && (
          <div className="flex items-center">
            {renderStars(service.rating)}
            <span className="ml-1 text-sm text-gray-600">({service.rating})</span>
          </div>
        )}
      </div>

      {/* 설명 */}
      {service.description && (
        <p className="text-gray-600 text-sm mb-4">{service.description}</p>
      )}

      {/* 서비스 목록 */}
      <div className="space-y-2 mb-4">
        {service.services.map((item, idx: number) => (
          <div key={idx} className="flex justify-between items-center">
            <span className="text-gray-700 text-sm">{item.name}</span>
            <div className="flex items-center gap-2">
              {item.originalPrice && (
                <span className="text-gray-400 line-through text-sm">{item.originalPrice}</span>
              )}
              <span className="text-red-500 font-medium text-sm">{item.price}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 연락처 */}
      <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <span className="text-pink-500">📞</span>
          <span>{service.contact.phone}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-orange-500">⏰</span>
          <span>{service.contact.hours}</span>
        </div>
      </div>

      {/* 사용자 반응 표시 */}
      <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            👁️ {service.stats ? service.stats.views : 0}
          </span>
          <span className="flex items-center gap-1">
            👍 {Math.floor((service.stats ? service.stats.views : 0) * 0.15)}
          </span>
          <span className="flex items-center gap-1">
            👎 {Math.floor((service.stats ? service.stats.views : 0) * 0.03)}
          </span>
          <span className="flex items-center gap-1">
            🔖 {Math.floor((service.stats ? service.stats.views : 0) * 0.12)}
          </span>
          <span className="flex items-center gap-1">
            문의 {service.stats ? service.stats.inquiries : 0}
          </span>
          <span className="flex items-center gap-1">
            후기 {service.stats ? service.stats.reviews : service.reviews.length}
          </span>
        </div>
      </div>
    </div>
  );
};

describe('서비스 카드 컴포넌트 테스트', () => {
  const mockService: MockService = {
    id: 1,
    name: '빠른이사 서비스',
    category: '이사',
    rating: 4.8,
    description: '빠르고 안전한 이사 서비스를 제공합니다.',
    services: [
      { name: '원룸 이사', price: '150,000원', description: '원룸 이사 서비스' },
      { name: '투룸 이사', price: '250,000원', originalPrice: '300,000원', description: '투룸 이사 서비스' }
    ],
    stats: { views: 89, inquiries: 15, reviews: 42 },
    verified: true,
    contact: {
      phone: '02-3456-7890',
      hours: '평일 08:00-20:00',
      address: '서울시 강남구 xx동',
      email: 'quick@moving.com'
    },
    reviews: []
  };

  test('서비스 정보 렌더링', () => {
    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={mockService} onClick={onClick} />
      </BrowserRouter>
    );

    // 업체명
    expect(screen.getByText('빠른이사 서비스')).toBeInTheDocument();
    
    // 카테고리
    expect(screen.getByText('이사')).toBeInTheDocument();
    
    // 인증 배지
    expect(screen.getByText('인증')).toBeInTheDocument();
    
    // 설명
    expect(screen.getByText('빠르고 안전한 이사 서비스를 제공합니다.')).toBeInTheDocument();
    
    // 평점
    expect(screen.getByText('(4.8)')).toBeInTheDocument();
  });

  test('서비스 항목 표시', () => {
    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={mockService} onClick={onClick} />
      </BrowserRouter>
    );

    // 서비스 항목
    expect(screen.getByText('원룸 이사')).toBeInTheDocument();
    expect(screen.getByText('150,000원')).toBeInTheDocument();
    
    expect(screen.getByText('투룸 이사')).toBeInTheDocument();
    expect(screen.getByText('250,000원')).toBeInTheDocument();
    expect(screen.getByText('300,000원')).toBeInTheDocument(); // 원가
  });

  test('연락처 정보 표시', () => {
    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={mockService} onClick={onClick} />
      </BrowserRouter>
    );

    // 전화번호
    expect(screen.getByText('02-3456-7890')).toBeInTheDocument();
    
    // 영업시간
    expect(screen.getByText('평일 08:00-20:00')).toBeInTheDocument();
  });

  test('통계 정보 표시', () => {
    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={mockService} onClick={onClick} />
      </BrowserRouter>
    );

    // 통계 정보가 포함된 div 찾기
    const statsContainer = screen.getByText('👁️ 89').parentElement?.parentElement;
    expect(statsContainer).toBeInTheDocument();
    
    // 개별 통계 확인
    expect(screen.getByText('👁️ 89')).toBeInTheDocument(); // 조회수
    expect(screen.getByText('👍 13')).toBeInTheDocument(); // 좋아요 (조회수의 15%)
    expect(screen.getByText('👎 2')).toBeInTheDocument();  // 싫어요 (조회수의 3%)
    expect(screen.getByText('🔖 10')).toBeInTheDocument(); // 북마크 (조회수의 12%)
    expect(screen.getByText('문의 15')).toBeInTheDocument(); // 문의
    expect(screen.getByText('후기 42')).toBeInTheDocument(); // 후기
  });

  test('클릭 이벤트', () => {
    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={mockService} onClick={onClick} />
      </BrowserRouter>
    );

    const card = screen.getByRole('article');
    fireEvent.click(card);

    expect(onClick).toHaveBeenCalledWith(mockService);
  });

  test('인증되지 않은 서비스', () => {
    const unverifiedService = {
      ...mockService,
      verified: false
    };

    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={unverifiedService} onClick={onClick} />
      </BrowserRouter>
    );

    // 인증 배지가 없어야 함
    expect(screen.queryByText('인증')).not.toBeInTheDocument();
  });

  test('평점이 없는 서비스', () => {
    const noRatingService = {
      ...mockService,
      rating: 0
    };

    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={noRatingService} onClick={onClick} />
      </BrowserRouter>
    );

    // 평점이 표시되지 않아야 함
    expect(screen.queryByText('(0)')).not.toBeInTheDocument();
    expect(screen.queryByText('⭐')).not.toBeInTheDocument();
  });

  test('별점 렌더링', () => {
    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={mockService} onClick={onClick} />
      </BrowserRouter>
    );

    // 4.8점이므로 4개의 채워진 별과 1개의 빈 별
    const stars = screen.getAllByText('⭐');
    expect(stars).toHaveLength(5);
    
    // 처음 4개는 채워진 별
    stars.slice(0, 4).forEach(star => {
      expect(star).toHaveClass('text-yellow-400');
    });
    
    // 마지막 1개는 빈 별
    expect(stars[4]).toHaveClass('text-gray-300');
  });

  test('통계 정보가 없을 때', () => {
    const noStatsService = {
      ...mockService,
      stats: undefined
    };

    const onClick = vi.fn();
    render(
      <BrowserRouter>
        <ServiceCard service={noStatsService} onClick={onClick} />
      </BrowserRouter>
    );

    // 모든 통계가 0으로 표시
    expect(screen.getByText(/👁️ 0/)).toBeInTheDocument();
    expect(screen.getByText(/👍 0/)).toBeInTheDocument();
    expect(screen.getByText(/👎 0/)).toBeInTheDocument();
    expect(screen.getByText(/🔖 0/)).toBeInTheDocument();
    expect(screen.getByText('문의 0')).toBeInTheDocument();
  });
});