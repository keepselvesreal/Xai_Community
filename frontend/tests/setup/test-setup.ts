/**
 * 전역 테스트 설정
 * Jest/Vitest가 테스트를 실행하기 전에 로드되는 설정 파일
 */

// Jest 환경에서 fetch API 사용을 위한 polyfill
import 'whatwg-fetch';

// Local Storage mock
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  },
  writable: true,
});

// Session Storage mock
Object.defineProperty(window, 'sessionStorage', {
  value: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  },
  writable: true,
});

// Window.location mock
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:5173',
    origin: 'http://localhost:5173',
    pathname: '/',
    search: '',
    hash: '',
    reload: jest.fn(),
    assign: jest.fn(),
    replace: jest.fn(),
  },
  writable: true,
});

// Console 에러 필터링 (React 개발 모드 경고 제거)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError(...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// 각 테스트 후 mock 정리
afterEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

// 전역 테스트 타임아웃 설정
jest.setTimeout(10000);

// 테스트 환경 변수 설정
process.env.NODE_ENV = 'test';
process.env.API_BASE_URL = 'http://localhost:8000';