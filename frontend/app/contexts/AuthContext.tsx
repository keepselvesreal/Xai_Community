import { createContext, useContext, useEffect, useState, useCallback } from "react";
import apiClient from "~/lib/api";
import { getLocalStorage, setLocalStorage, removeLocalStorage } from "~/lib/utils";
import { STORAGE_KEYS } from "~/lib/constants";
import type { AuthContextType, User, LoginRequest, RegisterRequest } from "~/types";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 초기 인증 상태 확인
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('AuthContext: Initializing auth...');
      // 직접 localStorage 사용하여 JSON.parse 회피
      const savedToken = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) : null;
      console.log('AuthContext: Saved token:', savedToken ? 'Found' : 'Not found');
      
      if (savedToken) {
        setToken(savedToken);
        try {
          console.log('AuthContext: Fetching current user...');
          const response = await apiClient.getCurrentUser();
          console.log('AuthContext: getCurrentUser response:', response);
          
          if (response.success && response.data) {
            console.log('AuthContext: User loaded successfully:', response.data);
            setUser(response.data);
          } else {
            console.log('AuthContext: Failed to get user - response not successful:', response);
            // 토큰이 유효하지 않은 경우
            logout();
          }
        } catch (error) {
          console.error("AuthContext: Failed to get current user - exception caught:", error);
          logout();
        }
      }
      
      setIsLoading(false);
      console.log('AuthContext: Initialization complete');
    };

    initializeAuth();
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      console.log('AuthContext: Attempting login...');
      const response = await apiClient.login(credentials);
      
      if (response.success && response.data) {
        const { access_token } = response.data;
        console.log('AuthContext: Login successful, token:', access_token ? 'Received' : 'Missing');
        
        // 토큰 저장 (직접 localStorage 사용하여 JSON.stringify 회피)
        setToken(access_token);
        if (typeof window !== 'undefined') {
          localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, access_token);
        }
        
        // 로그인 후 즉시 사용자 정보 로드
        console.log('AuthContext: Loading user info after login...');
        try {
          const userResponse = await apiClient.getCurrentUser();
          if (userResponse.success && userResponse.data) {
            console.log('AuthContext: User info loaded:', userResponse.data);
            setUser(userResponse.data);
          }
        } catch (error) {
          console.error("AuthContext: Failed to load user info after login:", error);
        }
        
        console.log('AuthContext: Login process complete');
      } else {
        throw new Error(response.error || "로그인에 실패했습니다.");
      }
    } catch (error) {
      console.error("AuthContext: Login failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (userData: RegisterRequest) => {
    setIsLoading(true);
    try {
      const response = await apiClient.register(userData);
      
      if (response.success && response.data) {
        // 회원가입 성공 후 자동 로그인은 하지 않음
        // 사용자가 직접 로그인하도록 유도
      } else {
        throw new Error(response.error || "회원가입에 실패했습니다.");
      }
    } catch (error) {
      console.error("Registration failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    console.log('AuthContext: Logging out...');
    setUser(null);
    setToken(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    }
    apiClient.logout();
  }, []);

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    isLoading,
    isAuthenticated: !!user && !!token,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export default AuthContext;