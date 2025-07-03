import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import apiClient from '~/lib/api';

// Mock apiClient
vi.mock('~/lib/api', () => ({
  default: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn()
  }
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
});

// 테스트용 컴포넌트
const TestComponent = () => {
  const { user, isLoading, isAuthenticated } = useAuth();
  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'ready'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user">{user ? user.display_name || user.email : 'no-user'}</div>
    </div>
  );
};

describe('AuthContext - 비차단형 인증 시스템', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('초기 로딩 상태', () => {
    it('비차단형으로 항상 ready 상태를 유지해야 함', async () => {
      // Given: 저장된 토큰이 없는 상태
      mockLocalStorage.getItem.mockReturnValue(null);

      // When: AuthProvider를 렌더링
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Then: 처음부터 ready 상태 (비차단형)
      expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      
      // And: 계속 ready 상태를 유지
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      }, { timeout: 50 });
    });

    it('저장된 토큰이 있어도 초기 UI가 차단되지 않아야 함', async () => {
      // Given: 유효한 토큰이 저장되어 있음
      mockLocalStorage.getItem.mockReturnValueOnce('valid-token');
      mockLocalStorage.getItem.mockReturnValueOnce('refresh-token');
      
      // API 호출을 의도적으로 지연시킴
      const mockGetCurrentUser = vi.mocked(apiClient.getCurrentUser);
      mockGetCurrentUser.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          success: true,
          data: { id: '1', email: 'test@example.com', display_name: 'Test User' }
        }), 500))
      );

      // When: AuthProvider를 렌더링
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Then: 짧은 시간 내에 ready 상태가 되어야 함 (비차단형)
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      }, { timeout: 200 });
      
      // And: 아직 사용자 정보는 로딩 중일 수 있음
      expect(screen.getByTestId('user')).toHaveTextContent('no-user');
    });
  });

  describe('백그라운드 인증', () => {
    it('저장된 토큰으로 백그라운드에서 사용자 정보를 로드해야 함', async () => {
      // Given: 유효한 토큰이 저장되어 있음
      mockLocalStorage.getItem.mockReturnValueOnce('valid-token');
      mockLocalStorage.getItem.mockReturnValueOnce('refresh-token');
      
      const mockUser = { id: '1', email: 'test@example.com', display_name: 'Test User' };
      const mockGetCurrentUser = vi.mocked(apiClient.getCurrentUser);
      mockGetCurrentUser.mockResolvedValue({
        success: true,
        data: mockUser
      });

      // When: AuthProvider를 렌더링
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Then: 초기에는 ready 상태
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // And: 백그라운드에서 사용자 정보가 로드됨
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('Test User');
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
      });
    });

    it('토큰이 유효하지 않으면 인증 상태를 정리해야 함', async () => {
      // Given: 저장된 토큰이 있지만 유효하지 않음
      mockLocalStorage.getItem.mockReturnValueOnce('invalid-token');
      mockLocalStorage.getItem.mockReturnValueOnce('refresh-token');
      
      const mockGetCurrentUser = vi.mocked(apiClient.getCurrentUser);
      mockGetCurrentUser.mockResolvedValue({
        success: false,
        error: 'Invalid token'
      });

      // When: AuthProvider를 렌더링
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Then: 초기에는 ready 상태
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // And: 백그라운드에서 인증 상태가 정리됨
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
        expect(screen.getByTestId('user')).toHaveTextContent('no-user');
      });

      // And: localStorage에서 토큰이 제거됨
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('authToken');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refreshToken');
    });
  });

  describe('UI 응답성', () => {
    it('인증 확인 중에도 페이지 컨텐츠가 표시되어야 함', async () => {
      // Given: 저장된 토큰이 있고 API 호출이 지연됨
      mockLocalStorage.getItem.mockReturnValueOnce('valid-token');
      const mockGetCurrentUser = vi.mocked(apiClient.getCurrentUser);
      
      let resolvePromise: (value: any) => void;
      mockGetCurrentUser.mockReturnValue(new Promise(resolve => {
        resolvePromise = resolve;
      }));

      // When: AuthProvider를 렌더링
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Then: API 호출이 완료되기 전에도 ready 상태
      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('ready');
      });

      // And: 사용자가 페이지와 상호작용할 수 있음
      expect(screen.getByTestId('user')).toHaveTextContent('no-user');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');

      // When: API 호출이 완료됨
      act(() => {
        resolvePromise!({
          success: true,
          data: { id: '1', email: 'test@example.com', display_name: 'Test User' }
        });
      });

      // Then: 인증 상태가 업데이트됨
      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user')).toHaveTextContent('Test User');
      });
    });
  });
});