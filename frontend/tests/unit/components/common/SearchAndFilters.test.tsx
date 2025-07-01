import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SearchAndFilters } from '~/components/common/SearchAndFilters';
import type { SearchAndFiltersProps } from '~/types/listTypes';

describe('SearchAndFilters 컴포넌트', () => {
  const defaultProps: SearchAndFiltersProps = {
    writeButtonText: '✏️ 글쓰기',
    writeButtonLink: '/write',
    searchPlaceholder: '검색하세요...',
    searchQuery: '',
    onSearch: vi.fn(),
    isSearching: false
  };

  test('검색 입력 테스트', () => {
    const onSearch = vi.fn();
    render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} onSearch={onSearch} />
      </BrowserRouter>
    );

    const searchInput = screen.getByPlaceholderText('검색하세요...') as HTMLInputElement;
    expect(searchInput).toBeInTheDocument();

    // 검색어 입력
    fireEvent.change(searchInput, { target: { value: '테스트 검색' } });
    expect(onSearch).toHaveBeenCalledWith('테스트 검색');
  });

  test('글쓰기 버튼 테스트', () => {
    render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} />
      </BrowserRouter>
    );

    const writeButton = screen.getByRole('link', { name: '✏️ 글쓰기' });
    expect(writeButton).toBeInTheDocument();
    expect(writeButton).toHaveAttribute('href', '/write');
  });

  test('검색 중 상태 표시', () => {
    render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} isSearching={true} />
      </BrowserRouter>
    );

    // 검색 중일 때 로딩 인디케이터 표시
    expect(screen.getByTestId('search-loading')).toBeInTheDocument();
    
    // 검색 입력창이 비활성화되는지 확인
    const searchInput = screen.getByPlaceholderText('검색하세요...') as HTMLInputElement;
    expect(searchInput).toBeDisabled();
  });

  test('검색어가 있을 때 초기값 표시', () => {
    render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} searchQuery="초기 검색어" />
      </BrowserRouter>
    );

    const searchInput = screen.getByPlaceholderText('검색하세요...') as HTMLInputElement;
    expect(searchInput.value).toBe('초기 검색어');
  });

  test('엔터키로 검색 제출', () => {
    const onSearch = vi.fn();
    render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} onSearch={onSearch} />
      </BrowserRouter>
    );

    const searchInput = screen.getByPlaceholderText('검색하세요...');
    
    // 검색어 입력 후 엔터키 누르기
    fireEvent.change(searchInput, { target: { value: '엔터 테스트' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter' });

    expect(onSearch).toHaveBeenCalledWith('엔터 테스트');
  });

  test('반응형 레이아웃', () => {
    const { container } = render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} />
      </BrowserRouter>
    );

    // 컨테이너가 flex 레이아웃인지 확인
    const container_div = container.querySelector('.flex.justify-center');
    expect(container_div).toBeInTheDocument();

    // 모바일 반응형 클래스 확인
    expect(container_div).toHaveClass('gap-4');
  });

  test('커스텀 버튼 텍스트와 링크', () => {
    render(
      <BrowserRouter>
        <SearchAndFilters 
          {...defaultProps}
          writeButtonText="📝 업체 등록"
          writeButtonLink="/services/write"
        />
      </BrowserRouter>
    );

    const writeButton = screen.getByRole('link', { name: '📝 업체 등록' });
    expect(writeButton).toBeInTheDocument();
    expect(writeButton).toHaveAttribute('href', '/services/write');
  });

  test('검색 아이콘 표시', () => {
    render(
      <BrowserRouter>
        <SearchAndFilters {...defaultProps} />
      </BrowserRouter>
    );

    // 검색 아이콘이 표시되는지 확인
    expect(screen.getByText('🔍')).toBeInTheDocument();
  });
});