import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ListSkeleton } from '~/components/common/ListSkeleton';

describe('ListSkeleton', () => {
  it('기본 리스트 스켈레톤을 렌더링한다', () => {
    render(<ListSkeleton />);
    
    const skeleton = screen.getByTestId('list-skeleton');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('animate-pulse');
  });

  it('지정된 개수만큼 리스트 아이템을 렌더링한다', () => {
    render(<ListSkeleton count={5} />);
    
    const items = screen.getAllByTestId('list-skeleton-item');
    expect(items).toHaveLength(5);
  });

  it('각 리스트 아이템이 올바른 스타일을 가진다', () => {
    render(<ListSkeleton />);
    
    const items = screen.getAllByTestId('list-skeleton-item');
    expect(items[0]).toHaveClass('flex', 'items-center', 'p-4', 'border-b');
  });

  it('아바타 영역 스켈레톤을 포함한다', () => {
    render(<ListSkeleton />);
    
    const avatars = screen.getAllByTestId('skeleton-avatar');
    expect(avatars[0]).toBeInTheDocument();
    expect(avatars[0]).toHaveClass('w-10', 'h-10', 'bg-gray-200', 'rounded-full');
  });

  it('텍스트 영역 스켈레톤을 포함한다', () => {
    render(<ListSkeleton />);
    
    const textAreas = screen.getAllByTestId('skeleton-text-area');
    expect(textAreas[0]).toBeInTheDocument();
    expect(textAreas[0]).toHaveClass('flex-1', 'ml-3');
  });

  it('제목과 설명 스켈레톤을 포함한다', () => {
    render(<ListSkeleton />);
    
    const titles = screen.getAllByTestId('skeleton-list-title');
    const descriptions = screen.getAllByTestId('skeleton-list-description');
    
    expect(titles[0]).toBeInTheDocument();
    expect(descriptions[0]).toBeInTheDocument();
    expect(titles[0]).toHaveClass('h-4', 'bg-gray-200', 'rounded');
    expect(descriptions[0]).toHaveClass('h-3', 'bg-gray-200', 'rounded');
  });

  it('액션 버튼 영역 스켈레톤을 포함한다', () => {
    render(<ListSkeleton />);
    
    const actions = screen.getAllByTestId('skeleton-action');
    expect(actions[0]).toBeInTheDocument();
    expect(actions[0]).toHaveClass('w-8', 'h-8', 'bg-gray-200', 'rounded');
  });
});