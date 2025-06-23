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
      const savedToken = getLocalStorage(STORAGE_KEYS.AUTH_TOKEN, null);
      
      if (savedToken) {
        setToken(savedToken);
        try {
          const response = await apiClient.getCurrentUser();
          if (response.success && response.data) {
            setUser(response.data);
          } else {
            // 토큰이 유효하지 않은 경우
            logout();
          }
        } catch (error) {
          console.error("Failed to get current user:", error);
          logout();
        }
      }
      
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const response = await apiClient.login(credentials);
      
      if (response.success && response.data) {
        const { access_token } = response.data;
        setToken(access_token);
        setLocalStorage(STORAGE_KEYS.AUTH_TOKEN, access_token);
        
        // 사용자 정보 가져오기
        const userResponse = await apiClient.getCurrentUser();
        if (userResponse.success && userResponse.data) {
          setUser(userResponse.data);
        }
      } else {
        throw new Error(response.error || "로그인에 실패했습니다.");
      }
    } catch (error) {
      console.error("Login failed:", error);
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
    setUser(null);
    setToken(null);
    removeLocalStorage(STORAGE_KEYS.AUTH_TOKEN);
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