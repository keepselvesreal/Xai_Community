/**
 * React Testing Library 커스텀 설정
 * 모든 테스트에서 공통으로 사용할 렌더링 함수와 Provider 설정
 */
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '~/contexts/AuthContext';
import { NotificationProvider } from '~/contexts/NotificationContext';
import { ThemeProvider } from '~/contexts/ThemeContext';

// 모든 Provider를 포함하는 Wrapper 컴포넌트
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

// 커스텀 render 함수
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Testing Library의 모든 export를 다시 export
export * from '@testing-library/react';

// 커스텀 render를 기본 render로 override
export { customRender as render };

// 테스트용 유틸리티 함수들
export const mockLocalStorage = () => {
  const storage: { [key: string]: string } = {};
  
  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key]);
    }),
  };
};

// 테스트용 사용자 데이터
export const mockUser = {
  id: '507f1f77bcf86cd799439011',
  email: 'test@example.com',
  user_handle: 'testuser',
  display_name: 'Test User',
  status: 'active' as const,
  created_at: '2023-01-01T00:00:00.000Z',
  updated_at: '2023-01-01T00:00:00.000Z',
};

// 테스트용 JWT 토큰 (유효한 형식)
export const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTEiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJpYXQiOjE2NzI1MzEyMDAsImV4cCI6OTk5OTk5OTk5OSwidHlwZSI6ImFjY2VzcyJ9.test-signature';

// API 응답 모킹 헬퍼
export const createMockApiResponse = <T,>(data: T, success = true) => ({
  success,
  data: success ? data : undefined,
  error: success ? undefined : 'Mock error',
  timestamp: new Date().toISOString(),
});