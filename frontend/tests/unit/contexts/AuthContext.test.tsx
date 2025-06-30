/**
 * AuthContext 테스트
 * TDD Red 단계: AuthContext의 로그인 플로우 개선을 위한 테스트
 */

import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '~/contexts/AuthContext';
import { mockLocalStorage, mockToken, mockUser, createMockApiResponse } from '../../utils/test-utils';
import * as api from '~/lib/api';

// Mock the API client
jest.mock('~/lib/api');
const mockApiClient = api.apiClient as jest.Mocked<typeof api.apiClient>;

describe('AuthContext', () => {
  let mockStorage: ReturnType<typeof mockLocalStorage>;

  beforeEach(() => {
    mockStorage = mockLocalStorage();
    Object.defineProperty(window, 'localStorage', {
      value: mockStorage,
      writable: true,
    });
    
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  describe('Initialization', () => {
    test('should initialize with no user when no token stored', async () => {
      // Arrange
      mockStorage.getItem.mockReturnValue(null);

      // Act
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Assert
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    test('should load user from API when valid token exists', async () => {
      // Arrange
      mockStorage.getItem.mockReturnValue(mockToken);
      mockApiClient.getCurrentUser.mockResolvedValue(createMockApiResponse(mockUser));

      // Act
      const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });

      // Wait for async initialization
      await waitForNextUpdate();

      // Assert
      expect(mockApiClient.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe(mockToken);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    test('should logout when token is invalid', async () => {
      // Arrange
      mockStorage.getItem.mockReturnValue(mockToken);
      mockApiClient.getCurrentUser.mockResolvedValue(createMockApiResponse(null, false));

      // Act
      const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });

      // Wait for async initialization
      await waitForNextUpdate();

      // Assert
      expect(mockApiClient.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockStorage.removeItem).toHaveBeenCalledWith('authToken');
    });
  });

  describe('Login Process', () => {
    test('should login successfully and store only token', async () => {
      // Arrange
      const credentials = { email: 'test@example.com', password: 'password123' };
      const loginResponse = {
        access_token: mockToken,
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        user: mockUser,
      };
      
      mockApiClient.login.mockResolvedValue(createMockApiResponse(loginResponse));

      // Act
      const { result } = renderHook(() => useAuth(), { wrapper });
      
      await act(async () => {
        await result.current.login(credentials);
      });

      // Assert
      expect(mockApiClient.login).toHaveBeenCalledWith(credentials);
      expect(mockStorage.setItem).toHaveBeenCalledWith('authToken', mockToken);
      expect(result.current.token).toBe(mockToken);
      // User should NOT be set immediately after login (will be set after /auth/profile call)
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    test('should handle login failure', async () => {
      // Arrange
      const credentials = { email: 'test@example.com', password: 'wrongpassword' };
      mockApiClient.login.mockResolvedValue(createMockApiResponse(null, false));

      // Act & Assert
      const { result } = renderHook(() => useAuth(), { wrapper });
      
      await expect(act(async () => {
        await result.current.login(credentials);
      })).rejects.toThrow();

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout Process', () => {
    test('should logout and clear all auth state', async () => {
      // Arrange: Start with authenticated state
      mockStorage.getItem.mockReturnValue(mockToken);
      mockApiClient.getCurrentUser.mockResolvedValue(createMockApiResponse(mockUser));

      const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
      await waitForNextUpdate(); // Wait for initialization

      // Act
      act(() => {
        result.current.logout();
      });

      // Assert
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockStorage.removeItem).toHaveBeenCalledWith('authToken');
      expect(mockApiClient.logout).toHaveBeenCalled();
    });
  });

  describe('getCurrentUser Integration', () => {
    test('should call getCurrentUser after page reload with stored token', async () => {
      // Arrange
      mockStorage.getItem.mockReturnValue(mockToken);
      mockApiClient.getCurrentUser.mockResolvedValue(createMockApiResponse(mockUser));

      // Act
      const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
      await waitForNextUpdate();

      // Assert
      expect(mockApiClient.getCurrentUser).toHaveBeenCalledTimes(1);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    test('should handle getCurrentUser failure gracefully', async () => {
      // Arrange
      mockStorage.getItem.mockReturnValue(mockToken);
      mockApiClient.getCurrentUser.mockRejectedValue(new Error('Network error'));

      // Act
      const { result, waitForNextUpdate } = renderHook(() => useAuth(), { wrapper });
      await waitForNextUpdate();

      // Assert
      expect(mockApiClient.getCurrentUser).toHaveBeenCalledTimes(1);
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockStorage.removeItem).toHaveBeenCalledWith('authToken');
    });
  });

  describe('Auth State Consistency', () => {
    test('isAuthenticated should be true only when both user and token exist', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Initially: no user, no token
      expect(result.current.isAuthenticated).toBe(false);

      // After setting token but before getting user
      act(() => {
        // Simulate token being set during login
        result.current.token = mockToken;
      });
      expect(result.current.isAuthenticated).toBe(false); // Still false because no user

      // After getting user info
      act(() => {
        result.current.user = mockUser;
      });
      expect(result.current.isAuthenticated).toBe(true); // Now true because both exist
    });
  });
});

// Note: These tests define the expected behavior for improved AuthContext
// The implementation will be updated to match these tests