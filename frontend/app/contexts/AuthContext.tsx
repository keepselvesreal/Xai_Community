import { createContext, useContext, useEffect, useState, useCallback } from "react";
import apiClient from "~/lib/api";
import { getLocalStorage, setLocalStorage, removeLocalStorage } from "~/lib/utils";
import { 
  STORAGE_KEYS, 
  SESSION_EXPIRY_REASONS, 
  SESSION_MESSAGES 
} from "~/lib/constants";
import type { AuthContextType, User, LoginRequest, RegisterRequest } from "~/types";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false); // 비차단형: 기본값을 false로
  const [renderKey, setRenderKey] = useState(0); // 강제 리렌더링을 위한 키
  const [showSessionWarning, setShowSessionWarning] = useState(false); // 세션 경고 표시
  const [sessionExpiryReason, setSessionExpiryReason] = useState<string | null>(null); // 만료 사유

  // 비차단형 인증 상태 확인 - UI를 차단하지 않고 백그라운드에서 처리
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('AuthContext: Initializing auth (non-blocking)...');
      
      // 직접 localStorage 사용하여 JSON.parse 회피
      const savedToken = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN) : null;
      const savedRefreshToken = typeof window !== 'undefined' ? localStorage.getItem('refreshToken') : null;
      console.log('AuthContext: Saved tokens:', savedToken ? 'access found' : 'access not found', savedRefreshToken ? 'refresh found' : 'refresh not found');
      
      // 토큰이 있으면 바로 상태에 설정 (UI 즉시 업데이트)
      if (savedToken) {
        setToken(savedToken);
        setRefreshToken(savedRefreshToken);
        
        // 백그라운드에서 사용자 정보 검증
        try {
          console.log('AuthContext: Fetching current user in background...');
          const response = await apiClient.getCurrentUser();
          console.log('AuthContext: getCurrentUser response:', response);
          
          if (response.success && response.data) {
            console.log('AuthContext: User loaded successfully:', response.data);
            // id 필드 보장 (백엔드에서 _id로 올 수 있음)
            const userData = {
              ...response.data,
              id: response.data.id || response.data._id
            };
            setUser(userData);
          } else {
            console.log('AuthContext: Failed to get user - response not successful:', response);
            // 토큰이 유효하지 않은 경우 - 상태 정리
            setUser(null);
            setToken(null);
            setRefreshToken(null);
            if (typeof window !== 'undefined') {
              localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
              localStorage.removeItem('refreshToken');
            }
            apiClient.logout();
          }
        } catch (error) {
          console.error("AuthContext: Failed to get current user - exception caught:", error);
          // 예외 발생 시 - 상태 정리
          setUser(null);
          setToken(null);
          setRefreshToken(null);
          if (typeof window !== 'undefined') {
            localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
            localStorage.removeItem('refreshToken');
          }
          apiClient.logout();
        }
      }
      
      console.log('AuthContext: Non-blocking initialization complete');
    };

    initializeAuth();
  }, []);

  // 브라우저 네비게이션 이벤트 처리 (뒤로가기 등)
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      console.log('AuthContext: PopState event detected, ensuring context stability');
      // 뒤로가기 등의 네비게이션 시 강제 리렌더링으로 context 안정성 확보
      setRenderKey(prev => prev + 1);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('popstate', handlePopState);
      return () => {
        window.removeEventListener('popstate', handlePopState);
      };
    }
  }, []);

  // 세션 및 토큰 관련 이벤트 리스너
  useEffect(() => {
    const handleTokenExpired = () => {
      console.log('AuthContext: Token expired event received, logging out...');
      setSessionExpiryReason(SESSION_EXPIRY_REASONS.TOKEN_INVALID);
      performLogout();
    };

    const handleSessionExpired = (event: CustomEvent) => {
      const reason = event.detail?.reason || SESSION_EXPIRY_REASONS.TOKEN_INVALID;
      console.log('AuthContext: Session expired event received, reason:', reason);
      setSessionExpiryReason(reason);
      performLogout();
    };

    const handleSessionWarning = () => {
      console.log('AuthContext: Session warning event received');
      setShowSessionWarning(true);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('tokenExpired', handleTokenExpired);
      window.addEventListener('sessionExpired', handleSessionExpired as EventListener);
      window.addEventListener('sessionWarning', handleSessionWarning);
      
      return () => {
        window.removeEventListener('tokenExpired', handleTokenExpired);
        window.removeEventListener('sessionExpired', handleSessionExpired as EventListener);
        window.removeEventListener('sessionWarning', handleSessionWarning);
      };
    }
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      console.log('AuthContext: Attempting login...');
      const response = await apiClient.login(credentials);
      
      if (response.success && response.data) {
        const { access_token, refresh_token } = response.data;
        console.log('AuthContext: Login successful, tokens:', access_token ? 'access received' : 'access missing', refresh_token ? 'refresh received' : 'refresh missing');
        
        // 토큰 저장 (직접 localStorage 사용하여 JSON.stringify 회피)
        setToken(access_token);
        setRefreshToken(refresh_token);
        if (typeof window !== 'undefined') {
          localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, access_token);
          if (refresh_token) {
            localStorage.setItem('refreshToken', refresh_token);
          }
        }
        
        // 로그인 후 즉시 사용자 정보 로드
        console.log('AuthContext: Loading user info after login...');
        try {
          const userResponse = await apiClient.getCurrentUser();
          if (userResponse.success && userResponse.data) {
            console.log('AuthContext: User info loaded:', userResponse.data);
            // id 필드 보장 (백엔드에서 _id로 올 수 있음)
            const userData = {
              ...userResponse.data,
              id: userResponse.data.id || userResponse.data._id
            };
            setUser(userData);
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

  const performLogout = useCallback(() => {
    console.log('AuthContext: Performing logout...');
    
    // 세션 만료 사유를 로그아웃 전에 localStorage에 저장 (알림용)
    if (typeof window !== 'undefined' && sessionExpiryReason) {
      localStorage.setItem('logoutReason', sessionExpiryReason);
    }
    
    // 상태 즉시 업데이트
    setUser(null);
    setToken(null);
    setRefreshToken(null);
    setIsLoading(false);
    setRenderKey(prev => prev + 1); // 강제 리렌더링
    
    // localStorage 정리 (로그아웃 사유는 제외)
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.LOGIN_TIME);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_COUNT);
      console.log('AuthContext: All tokens and session data removed from localStorage');
    }
    
    // API 클라이언트 로그아웃
    apiClient.logout();
    
    console.log('AuthContext: Logout complete');
    
    // 로그아웃 후 홈페이지로 리디렉션
    if (typeof window !== 'undefined') {
      setTimeout(() => {
        window.location.href = '/';
      }, 100); // 상태 업데이트가 완료된 후 리디렉션
    }
  }, [sessionExpiryReason]);

  const logout = useCallback(() => {
    console.log('AuthContext: Manual logout requested');
    setSessionExpiryReason(SESSION_EXPIRY_REASONS.MANUAL_LOGOUT);
    performLogout();
  }, [performLogout]);

  // 세션 관련 기능들
  const extendSession = useCallback(() => {
    console.log('AuthContext: Extending session requested');
    setShowSessionWarning(false);
    return apiClient.extendSession();
  }, []);

  const getSessionInfo = useCallback(() => {
    return apiClient.getSessionInfo();
  }, []);

  const dismissSessionWarning = useCallback(() => {
    setShowSessionWarning(false);
  }, []);

  const getSessionExpiryMessage = useCallback(() => {
    switch (sessionExpiryReason) {
      case SESSION_EXPIRY_REASONS.TIME_LIMIT:
        return SESSION_MESSAGES.EXPIRED_TIME_LIMIT;
      case SESSION_EXPIRY_REASONS.REFRESH_LIMIT:
        return SESSION_MESSAGES.EXPIRED_REFRESH_LIMIT;
      case SESSION_EXPIRY_REASONS.TOKEN_INVALID:
        return SESSION_MESSAGES.EXPIRED_TOKEN_INVALID;
      default:
        return SESSION_MESSAGES.EXPIRED_TOKEN_INVALID;
    }
  }, [sessionExpiryReason]);

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    isLoading,
    isAuthenticated: !!user && !!token,
    // 세션 관리 기능들
    showSessionWarning,
    sessionExpiryReason,
    extendSession,
    getSessionInfo,
    dismissSessionWarning,
    getSessionExpiryMessage,
  };
  
  console.log('AuthContext: Current state - user:', !!user, 'token:', !!token, 'isAuthenticated:', !!user && !!token, 'renderKey:', renderKey);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    // 에러 발생 전에 디버깅 정보 출력
    console.error('useAuth: AuthContext is undefined');
    console.error('useAuth: Current location:', typeof window !== 'undefined' ? window.location.href : 'server');
    console.error('useAuth: Stack trace:', new Error().stack);
    
    // 브라우저 환경에서 뒤로가기 등으로 인한 일시적 오류인 경우 fallback 제공
    if (typeof window !== 'undefined') {
      console.warn('useAuth: Providing fallback context due to navigation issue');
      return {
        user: null,
        token: null,
        login: async () => { throw new Error('Auth not available'); },
        register: async () => { throw new Error('Auth not available'); },
        logout: () => { console.warn('Logout called but auth not available'); },
        isLoading: false,
        isAuthenticated: false,
      };
    }
    
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export default AuthContext;