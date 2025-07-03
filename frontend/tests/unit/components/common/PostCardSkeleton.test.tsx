import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PostCardSkeleton } from '~/components/common/PostCardSkeleton';

describe('PostCardSkeleton', () => {
  it('기본 스켈레톤 카드를 렌더링한다', () => {
    render(<PostCardSkeleton />);
    
    const skeleton = screen.getByTestId('post-card-skeleton');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  it('여러 개의 스켈레톤 카드를 렌더링한다', () => {
    render(<PostCardSkeleton count={3} />);
    
    const skeletons = screen.getAllByTestId('post-card-skeleton');
    expect(skeletons).toHaveLength(3);
  });

  it('제목 영역 스켈레톤을 포함한다', () => {
    render(<PostCardSkeleton />);
    
    const titleSkeleton = screen.getByTestId('skeleton-title');
    expect(titleSkeleton).toBeInTheDocument();
    expect(titleSkeleton).toHaveClass('h-4', 'bg-gray-200', 'rounded');
  });

  it('내용 영역 스켈레톤을 포함한다', () => {
    render(<PostCardSkeleton />);
    
    const contentSkeleton = screen.getByTestId('skeleton-content');
    expect(contentSkeleton).toBeInTheDocument();
    expect(contentSkeleton).toHaveClass('h-3', 'bg-gray-200', 'rounded');
  });

  it('메타 정보 영역 스켈레톤을 포함한다', () => {
    render(<PostCardSkeleton />);
    
    const metaSkeleton = screen.getByTestId('skeleton-meta');
    expect(metaSkeleton).toBeInTheDocument();
    expect(metaSkeleton).toHaveClass('h-3', 'bg-gray-200', 'rounded');
  });

  it('올바른 grid 레이아웃 클래스를 가진다', () => {
    render(<PostCardSkeleton count={4} />);
    
    const container = screen.getByTestId('post-card-skeleton-container');
    expect(container).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'gap-6');
  });

  it('개별 스켈레톤이 Card 스타일을 가진다', () => {
    render(<PostCardSkeleton />);
    
    const skeleton = screen.getByTestId('post-card-skeleton');
    expect(skeleton).toHaveClass('bg-white', 'rounded-lg', 'border', 'p-6');
  });
});