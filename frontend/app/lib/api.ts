import type {
  User,
  AuthToken,
  LoginRequest,
  RegisterRequest,
  Post,
  CreatePostRequest,
  Comment,
  CreateCommentRequest,
  CommentListResponse,
  Reaction,
  ReactionType,
  ApiResponse,
  PaginatedResponse,
  PostFilters,
  ApiTestRequest,
  ApiTestResponse,
  UserActivityResponse,
  EmailVerificationRequest,
  EmailVerificationResponse,
  EmailVerificationCodeRequest,
  EmailVerificationCodeResponse,
  AlertRule,
  AlertStatistics,
  AlertHistory,
  CreateAlertRuleRequest,
  UpdateAlertRuleRequest,
} from "~/types";
import { validateJWTFormat, decodeJWTPayload, isTokenExpired } from './jwt-utils';
import { 
  STORAGE_KEYS, 
  SESSION_CONFIG, 
  SESSION_EXPIRY_REASONS,
  SESSION_MESSAGES
} from './constants';

// 환경별 API URL 설정
function getApiBaseUrl(): string {
  // staging, production 환경에서는 Vercel 사이트 환경변수 사용
  // 개발환경에서는 .env.development 파일의 환경변수 사용
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // 개발환경 fallback
  return 'http://localhost:8000';
}

const API_BASE_URL = getApiBaseUrl();

// ✅ 환경변수 디버깅
const nodeEnv = import.meta.env.VITE_NODE_ENV || 'development';
const isProduction = nodeEnv === 'production';

console.log('✅ VITE_NODE_ENV:', nodeEnv);
console.log('✅ PROD:', isProduction);

class ApiClient {
  private baseURL: string;
  private token: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing: boolean = false;
  private refreshPromise: Promise<boolean> | null = null;
  private tokenCheckInterval: number | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.loadTokens();
  }

  private loadTokens(): void {
    if (typeof window !== 'undefined') {
      let token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
      let refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      
      // JSON.stringify로 저장된 경우 파싱
      if (token && (token.startsWith('"') && token.endsWith('"'))) {
        try {
          token = JSON.parse(token);
          if (token) {
            localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token); // 정리된 토큰 재저장
            console.log('ApiClient: Cleaned JSON stringified token');
          }
        } catch (e) {
          console.error('ApiClient: Failed to parse token:', e);
        }
      }
      
      // Bearer 접두사가 잘못 저장된 경우 제거
      if (token && token.startsWith('Bearer ')) {
        token = token.substring(7);
        localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
        console.log('ApiClient: Cleaned Bearer prefix from stored token');
      }
      
      this.token = token;
      this.refreshToken = refreshToken;
      // 프로덕션에서는 토큰 정보 로그 제거
      if (!isProduction) {
        console.log('ApiClient: Tokens loaded from localStorage:', 
          this.token ? `access: ${this.token.substring(0, 10)}...` : 'access: null',
          this.refreshToken ? `refresh: ${this.refreshToken.substring(0, 10)}...` : 'refresh: null'
        );
      }
      
      // 세션 만료 체크
      if (this.token && this.refreshToken) {
        if (this.isSessionExpired()) {
          console.log('ApiClient: Session expired, forcing logout');
          this.handleSessionExpiry(this.getSessionExpiryReason());
          return;
        }
        
        // 토큰이 있고 세션이 유효하면 자동 갱신 타이머 시작
        this.startTokenRefreshTimer();
      }
    }
  }

  private saveTokens(accessToken: string, refreshToken?: string): void {
    // Bearer 접두사 제거 (토큰만 저장)
    const cleanToken = accessToken.startsWith('Bearer ') ? accessToken.substring(7) : accessToken;
    
    this.token = cleanToken;
    if (refreshToken) {
      this.refreshToken = refreshToken;
    }
    
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, cleanToken);
      if (refreshToken) {
        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
      }
      // 프로덕션에서는 토큰 정보 로그 제거
      if (!isProduction) {
        console.log('ApiClient: Tokens saved to localStorage:', 
          cleanToken ? `access: ${cleanToken.substring(0, 10)}...` : 'access: null',
          refreshToken ? `refresh: ${refreshToken.substring(0, 10)}...` : 'refresh: unchanged'
        );
      }
    }
  }

  // 세션 관리 메서드들 (하이브리드 방식)
  private saveLoginTime(): void {
    if (typeof window !== 'undefined') {
      const loginTime = new Date().toISOString();
      localStorage.setItem(STORAGE_KEYS.LOGIN_TIME, loginTime);
      localStorage.setItem(STORAGE_KEYS.REFRESH_COUNT, '0');
      console.log('ApiClient: Login time saved:', loginTime);
    }
  }

  private getLoginTime(): Date | null {
    if (typeof window === 'undefined') return null;
    
    const loginTimeStr = localStorage.getItem(STORAGE_KEYS.LOGIN_TIME);
    return loginTimeStr ? new Date(loginTimeStr) : null;
  }

  private getRefreshCount(): number {
    if (typeof window === 'undefined') return 0;
    
    const count = localStorage.getItem(STORAGE_KEYS.REFRESH_COUNT);
    return count ? parseInt(count, 10) : 0;
  }

  private incrementRefreshCount(): void {
    if (typeof window !== 'undefined') {
      const currentCount = this.getRefreshCount();
      const newCount = currentCount + 1;
      localStorage.setItem(STORAGE_KEYS.REFRESH_COUNT, newCount.toString());
      console.log('ApiClient: Refresh count incremented to:', newCount);
    }
  }

  private isSessionExpired(): boolean {
    const loginTime = this.getLoginTime();
    const refreshCount = this.getRefreshCount();
    
    if (!loginTime) return false;
    
    // 로그인 상태 유지 설정에 따른 동적 세션 정책
    const isRememberMe = typeof window !== 'undefined' && localStorage.getItem('rememberMe') === 'true';
    const maxSessionHours = isRememberMe ? 24 * 7 : SESSION_CONFIG.MAX_SESSION_HOURS; // 7일 vs 1일
    const maxRefreshCount = isRememberMe ? SESSION_CONFIG.MAX_REFRESH_COUNT * 7 : SESSION_CONFIG.MAX_REFRESH_COUNT; // 700회 vs 100회
    
    // 조건 1: 절대 시간 제한
    const elapsed = (Date.now() - loginTime.getTime()) / (1000 * 60 * 60);
    if (elapsed > maxSessionHours) {
      console.log('ApiClient: Session expired due to time limit:', elapsed, 'hours (max:', maxSessionHours, ')');
      return true;
    }
    
    // 조건 2: 갱신 횟수 제한
    if (refreshCount >= maxRefreshCount) {
      console.log('ApiClient: Session expired due to refresh limit:', refreshCount, '(max:', maxRefreshCount, ')');
      return true;
    }
    
    return false;
  }

  private getSessionExpiryReason(): string {
    const loginTime = this.getLoginTime();
    const refreshCount = this.getRefreshCount();
    
    if (!loginTime) return SESSION_EXPIRY_REASONS.TOKEN_INVALID;
    
    // 로그인 상태 유지 설정에 따른 동적 세션 정책
    const isRememberMe = typeof window !== 'undefined' && localStorage.getItem('rememberMe') === 'true';
    const maxSessionHours = isRememberMe ? 24 * 7 : SESSION_CONFIG.MAX_SESSION_HOURS;
    const maxRefreshCount = isRememberMe ? SESSION_CONFIG.MAX_REFRESH_COUNT * 7 : SESSION_CONFIG.MAX_REFRESH_COUNT;
    
    const elapsed = (Date.now() - loginTime.getTime()) / (1000 * 60 * 60);
    if (elapsed > maxSessionHours) {
      return SESSION_EXPIRY_REASONS.TIME_LIMIT;
    }
    
    if (refreshCount >= maxRefreshCount) {
      return SESSION_EXPIRY_REASONS.REFRESH_LIMIT;
    }
    
    return SESSION_EXPIRY_REASONS.TOKEN_INVALID;
  }

  private shouldShowSessionWarning(): boolean {
    const loginTime = this.getLoginTime();
    if (!loginTime) return false;
    
    // 로그인 상태 유지 설정에 따른 동적 경고 시간
    const isRememberMe = typeof window !== 'undefined' && localStorage.getItem('rememberMe') === 'true';
    const maxSessionHours = isRememberMe ? 24 * 7 : SESSION_CONFIG.MAX_SESSION_HOURS;
    
    const elapsed = (Date.now() - loginTime.getTime()) / (1000 * 60);
    const warningThreshold = (maxSessionHours * 60) - SESSION_CONFIG.WARNING_BEFORE_LOGOUT_MINUTES;
    
    return elapsed > warningThreshold;
  }

  private handleSessionExpiry(reason: string): void {
    console.log('ApiClient: Handling session expiry, reason:', reason);
    
    // 토큰 및 세션 데이터 정리
    this.removeTokens();
    
    // 세션 만료 이벤트 발생 (AuthContext에서 처리)
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('sessionExpired', { 
        detail: { reason } 
      }));
    }
  }

  private removeTokens(): void {
    this.token = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.LOGIN_TIME);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_COUNT);
    }
    this.stopTokenRefreshTimer();
  }

  private startTokenRefreshTimer(): void {
    if (typeof window === 'undefined') return;
    
    // 기존 타이머 정리
    this.stopTokenRefreshTimer();
    
    // 설정된 주기마다 토큰 및 세션 상태 확인
    const intervalMinutes = SESSION_CONFIG.SESSION_CHECK_INTERVAL_MINUTES;
    this.tokenCheckInterval = window.setInterval(() => {
      this.checkAndRefreshToken();
    }, intervalMinutes * 60 * 1000);
  }

  private stopTokenRefreshTimer(): void {
    if (this.tokenCheckInterval) {
      clearInterval(this.tokenCheckInterval);
      this.tokenCheckInterval = null;
    }
  }

  private async checkAndRefreshToken(): Promise<void> {
    if (!this.token || !this.refreshToken) {
      return;
    }

    try {
      // 1. 먼저 세션 만료 체크
      if (this.isSessionExpired()) {
        console.log('ApiClient: Session expired during check');
        this.handleSessionExpiry(this.getSessionExpiryReason());
        return;
      }

      // 2. 세션 경고 체크
      if (this.shouldShowSessionWarning()) {
        console.log('ApiClient: Session warning should be shown');
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('sessionWarning'));
        }
      }

      // 3. 토큰 만료 체크 및 갱신
      const thresholdMinutes = SESSION_CONFIG.TOKEN_REFRESH_THRESHOLD_MINUTES;
      if (this.isTokenExpired(this.token) || this.isTokenExpiringSoon(this.token, thresholdMinutes * 60)) {
        console.log('ApiClient: Token is expired or expiring soon, refreshing...');
        await this.refreshAccessToken();
      }
    } catch (error) {
      console.error('ApiClient: Error checking token expiration:', error);
    }
  }

  private isTokenExpiringSoon(token: string, secondsBeforeExpiry: number): boolean {
    try {
      const payload = this.decodeJWTPayload(token);
      const now = Math.floor(Date.now() / 1000);
      const expiresAt = payload.exp;
      
      // 현재 시간 + secondsBeforeExpiry가 만료 시간보다 크거나 같으면 곧 만료됨
      return (now + secondsBeforeExpiry) >= expiresAt;
    } catch (error) {
      console.error('ApiClient: Error checking token expiration:', error);
      return true; // 파싱 실패 시 안전하게 만료된 것으로 처리
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      // 토큰에서 Bearer 접두사 제거 후 다시 추가 (정규화)
      const cleanToken = this.token.replace(/^Bearer\s+/i, '');
      headers['Authorization'] = `Bearer ${cleanToken}`;
      
      // 프로덕션에서는 토큰 정보 로그 제거
      if (!isProduction) {
        console.log('ApiClient: Setting Authorization header with token:', `Bearer ${cleanToken.substring(0, 10)}...`);
      }
    }

    return headers;
  }

  private async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) {
      console.log('ApiClient: No refresh token available');
      return false;
    }

    if (this.isRefreshing) {
      // 이미 토큰 갱신 중이면 기존 프로미스를 기다림
      return this.refreshPromise || Promise.resolve(false);
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();
    
    const result = await this.refreshPromise;
    this.isRefreshing = false;
    this.refreshPromise = null;
    
    return result;
  }

  private async performTokenRefresh(): Promise<boolean> {
    return this.performTokenRefreshWithRetry();
  }

  private async performTokenRefreshWithRetry(attempt: number = 1, maxAttempts: number = 3): Promise<boolean> {
    try {
      console.log(`ApiClient: Attempting to refresh access token... (attempt ${attempt}/${maxAttempts})`);
      
      // 갱신 전 세션 만료 체크
      if (this.isSessionExpired()) {
        console.log('ApiClient: Session expired, cannot refresh token');
        this.handleSessionExpiry(this.getSessionExpiryReason());
        return false;
      }
      
      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (!response.ok) {
        console.error('ApiClient: Token refresh failed:', response.status, response.statusText);
        
        // 재시도 가능한 오류인지 확인
        if (this.isRetryableError(response.status) && attempt < maxAttempts) {
          const delay = Math.pow(2, attempt) * 1000; // 지수 백오프: 2초, 4초, 8초
          console.log(`ApiClient: Retrying token refresh in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.performTokenRefreshWithRetry(attempt + 1, maxAttempts);
        }
        
        // 재시도 불가능하거나 최대 재시도 횟수 초과 - 로그아웃 처리
        this.handleSessionExpiry(SESSION_EXPIRY_REASONS.TOKEN_INVALID);
        return false;
      }

      const data = await response.json();
      console.log('ApiClient: Token refresh successful');
      
      // 갱신 횟수 증가
      this.incrementRefreshCount();
      
      // 새로운 access token 저장 (refresh token은 그대로 유지)
      this.saveTokens(data.access_token);
      
      // 갱신 후 세션 만료 재체크 (갱신 횟수 제한)
      if (this.isSessionExpired()) {
        console.log('ApiClient: Session expired after refresh');
        this.handleSessionExpiry(this.getSessionExpiryReason());
        return false;
      }
      
      // 토큰 갱신 후 타이머 재시작
      this.startTokenRefreshTimer();
      
      return true;
    } catch (error) {
      console.error('ApiClient: Token refresh error:', error);
      
      // 네트워크 오류 등 재시도 가능한 오류인지 확인
      if (this.isRetryableNetworkError(error) && attempt < maxAttempts) {
        const delay = Math.pow(2, attempt) * 1000; // 지수 백오프
        console.log(`ApiClient: Retrying token refresh due to network error in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.performTokenRefreshWithRetry(attempt + 1, maxAttempts);
      }
      
      this.handleSessionExpiry(SESSION_EXPIRY_REASONS.TOKEN_INVALID);
      return false;
    }
  }

  private isRetryableError(status: number): boolean {
    // 일시적인 서버 오류로 재시도 가능한 상태 코드들
    return status === 502 || status === 503 || status === 504 || status === 408;
  }

  private isRetryableNetworkError(error: unknown): boolean {
    // 네트워크 관련 재시도 가능한 오류들
    if (error instanceof Error) {
      const errorMessage = error.message.toLowerCase();
      return errorMessage.includes('network') ||
             errorMessage.includes('fetch') ||
             errorMessage.includes('timeout') ||
             errorMessage.includes('connection');
    }
    return false;
  }

  private parseValidationErrors(validationErrors: any): string {
    // FastAPI 422 에러를 사용자 친화적 메시지로 변환
    if (Array.isArray(validationErrors)) {
      const friendlyMessages: string[] = [];
      
      for (const error of validationErrors) {
        // 백엔드 응답 구조에 맞게 필드 추출 (field 또는 loc)
        const field = error.field || (error.loc?.join('.')) || 'unknown';
        const msg = error.message || error.msg || 'Invalid value';
        
        console.log('Parsing validation error:', { field, msg, error }); // 디버깅용
        
        // 비밀번호 관련 에러 특별 처리 (현재 MVP 정책에 맞춤)
        if (field.includes('password')) {
          if (msg.includes('lowercase')) {
            friendlyMessages.push('비밀번호에 소문자가 포함되어야 합니다.');
          } else if (msg.includes('digit')) {
            friendlyMessages.push('비밀번호에 숫자가 포함되어야 합니다.');
          } else if (msg.includes('min_length') || msg.includes('at least')) {
            friendlyMessages.push('비밀번호는 최소 6자 이상이어야 합니다.');
          } else {
            friendlyMessages.push('비밀번호는 6자 이상, 소문자와 숫자를 포함해야 합니다.');
          }
        }
        // 이메일 관련 에러 처리
        else if (field.includes('email')) {
          if (msg.includes('valid email')) {
            friendlyMessages.push('올바른 이메일 주소를 입력해주세요.');
          } else {
            friendlyMessages.push('이메일 형식이 올바르지 않습니다.');
          }
        }
        // 사용자 핸들 관련 에러 처리 (현재 실제 정책에 맞춤)
        else if (field.includes('user_handle')) {
          if (msg.includes('min_length') || msg.includes('at least 3')) {
            friendlyMessages.push('사용자 아이디는 3자 이상이어야 합니다.');
          } else if (msg.includes('max_length') || msg.includes('at most 30')) {
            friendlyMessages.push('사용자 아이디는 30자 이하여야 합니다.');
          } else if (msg.includes('letters, numbers, and underscores') || msg.includes('alphanumeric')) {
            friendlyMessages.push('사용자 아이디는 영문, 숫자, 언더스코어(_)만 사용 가능합니다.');
          } else {
            friendlyMessages.push('사용자 아이디는 3-30자, 영문/숫자/언더스코어만 사용 가능합니다.');
          }
        }
        // 기타 필드 에러
        else {
          friendlyMessages.push(`${field}: ${this.translateValidationMessage(msg)}`);
        }
      }
      
      return friendlyMessages.length > 0 
        ? friendlyMessages.join(' ') 
        : '입력 정보를 다시 확인해주세요.';
    }
    
    // 단일 에러 메시지인 경우
    return typeof validationErrors === 'string' 
      ? this.translateValidationMessage(validationErrors)
      : '입력 정보를 다시 확인해주세요.';
  }

  private translateValidationMessage(msg: string): string {
    // 영문 에러 메시지를 한국어로 변환
    const translations: Record<string, string> = {
      'Field required': '필수 입력 항목입니다.',
      'String should have at least': '최소 길이를 만족하지 않습니다.',
      'String should have at most': '최대 길이를 초과했습니다.',
      'value is not a valid email address': '올바른 이메일 주소가 아닙니다.',
      'Input should be a valid string': '문자열을 입력해주세요.',
    };
    
    for (const [en, ko] of Object.entries(translations)) {
      if (msg.includes(en)) {
        return ko;
      }
    }
    
    return msg; // 번역되지 않은 메시지는 원문 반환
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    return this.makeRequestWithRetry<T>(endpoint, options, false);
  }

  // Public request method for general use
  async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    options?: {
      params?: Record<string, any>;
      body?: any;
      headers?: Record<string, string>;
    }
  ): Promise<ApiResponse<T>> {
    let finalEndpoint = endpoint;
    
    // Add query parameters if provided
    if (options?.params) {
      const params = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, String(value));
        }
      });
      if (params.toString()) {
        finalEndpoint += `?${params.toString()}`;
      }
    }

    const requestOptions: RequestInit = {
      method,
      ...options?.headers && { headers: { ...this.getHeaders(), ...options.headers } }
    };

    // Add body for non-GET requests
    if (method !== 'GET' && options?.body) {
      requestOptions.body = typeof options.body === 'string' 
        ? options.body 
        : JSON.stringify(options.body);
    }

    return this.makeRequestWithRetry<T>(finalEndpoint, requestOptions, false);
  }

  private async makeRequestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry: boolean = false
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    console.log('🔍 요청 URL 구성:', { baseURL: this.baseURL, endpoint, finalURL: url });
    
    // 토큰이 없고 refresh token이 있다면 먼저 토큰 갱신 시도
    if (!this.token && this.refreshToken && !isRetry) {
      console.log('ApiClient: No access token but refresh token exists, attempting refresh...');
      const refreshSuccess = await this.refreshAccessToken();
      if (!refreshSuccess) {
        console.log('ApiClient: Token refresh failed before request');
        // SSR 환경이거나 공개 API인 경우 토큰 없이 계속 진행
        if (typeof window === 'undefined') {
          console.log('ApiClient: SSR environment - proceeding without token');
        } else {
          this.notifyTokenExpired();
        }
      }
    }
    
    const config: RequestInit = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      console.log('ApiClient: Making request to:', url, isRetry ? '(retry)' : '');
      const response = await fetch(url, config);
      console.log('ApiClient: Response received:', response.status, response.statusText);
      
      // 401 Unauthorized 처리 - 토큰 갱신 시도
      if (response.status === 401 && !isRetry && this.refreshToken) {
        console.log('ApiClient: Received 401, attempting token refresh...');
        const refreshSuccess = await this.refreshAccessToken();
        
        if (refreshSuccess) {
          console.log('ApiClient: Token refreshed successfully, retrying request...');
          // 토큰 갱신 성공 시 요청 재시도
          return this.makeRequestWithRetry<T>(endpoint, options, true);
        } else {
          console.log('ApiClient: Token refresh failed, user needs to login again');
          // 토큰 갱신 실패 시 로그아웃 이벤트 발생
          this.notifyTokenExpired();
        }
      }
      
      // 빈 응답 처리
      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const text = await response.text();
        if (text.trim()) {
          data = JSON.parse(text);
        } else {
          // 빈 JSON 응답 처리
          data = { success: true };
        }
      } else {
        // JSON이 아닌 응답
        data = { success: true };
      }
      console.log('ApiClient: Response data:', data);

      if (!response.ok) {
        // 상세한 오류 정보 로그
        console.error('API Error Details:', {
          url,
          status: response.status,
          statusText: response.statusText,
          data,
          requestBody: config.body
        });
        
        // FastAPI validation errors 처리 - 사용자 친화적 메시지 제공
        if (response.status === 422 && (data.details || data.detail)) {
          const validationErrors = data.details || data.detail;
          const friendlyErrorMessage = this.parseValidationErrors(validationErrors);
          throw new Error(friendlyErrorMessage);
        }
        
        throw new Error(data.message || data.detail || `HTTP error! status: ${response.status}`);
      }

      return {
        success: true,
        data,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('API request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      };
    }
  }

  private notifyTokenExpired(): void {
    // 토큰 만료 이벤트를 발생시켜 AuthContext가 로그아웃 처리하도록 함
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('tokenExpired'));
    }
  }

  // 인증 관련 API
  async login(credentials: LoginRequest): Promise<ApiResponse<AuthToken>> {
    // OAuth2PasswordRequestForm expects form-data with username/password fields
    const formData = new FormData();
    formData.append('username', credentials.email); // Backend expects 'username' field with email value
    formData.append('password', credentials.password);

    const url = `${this.baseURL}/api/auth/login`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData, // Send as form-data, not JSON
      });
      
      const data = await response.json();

      if (!response.ok) {
        console.error('Login API Error Details:', {
          url,
          status: response.status,
          statusText: response.statusText,
          data
        });
        
        if (response.status === 422 && data.detail) {
          const errorMessages = Array.isArray(data.detail) 
            ? data.detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join(', ')
            : data.detail;
          throw new Error(`Validation Error: ${errorMessages}`);
        }
        
        throw new Error(data.message || data.detail || `HTTP error! status: ${response.status}`);
      }

      this.saveTokens(data.access_token, data.refresh_token);
      
      // 로그인 시간 저장 (세션 관리용)
      this.saveLoginTime();
      
      // 로그인 성공 시 토큰 자동 갱신 타이머 시작
      this.startTokenRefreshTimer();
      
      return {
        success: true,
        data,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Login API request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      };
    }
  }

  async register(userData: RegisterRequest): Promise<ApiResponse<User>> {
    return this.makeRequest<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    console.log('ApiClient: getCurrentUser called');
    const result = await this.makeRequest<User>('/api/auth/profile');
    console.log('ApiClient: getCurrentUser result:', result);
    return result;
  }

  async updateUserProfile(profileData: { name?: string; bio?: string; avatar_url?: string; user_handle?: string; email?: string }): Promise<ApiResponse<User>> {
    console.log('ApiClient: updateUserProfile called with data:', profileData);
    const result = await this.makeRequest<User>('/api/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
    console.log('ApiClient: updateUserProfile result:', result);
    return result;
  }

  async changePassword(passwordData: { current_password: string; new_password: string }): Promise<ApiResponse<{ message: string }>> {
    console.log('ApiClient: changePassword called');
    const result = await this.makeRequest<{ message: string }>('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
    console.log('ApiClient: changePassword result:', result);
    return result;
  }

  // 사용자 활동 개수 조회 API (빠른 조회용)
  async getUserActivityCounts(): Promise<{posts: number, comments: number, reactions: number}> {
    console.log('ApiClient: getUserActivityCounts called');
    
    const result = await this.makeRequest<{posts: number, comments: number, reactions: number}>('/api/users/me/activity/counts', {
      method: 'GET',
    });
    
    if (!result.success) {
      throw new Error(`Failed to retrieve user activity counts: ${result.error}`);
    }
    
    return result.data;
  }

  // 사용자 활동 조회 API (진짜 페이지네이션)
  async getUserActivity(page: number = 1, limit: number = 10): Promise<UserActivityResponse> {
    console.log('ApiClient: getUserActivity called with page:', page, 'limit:', limit);
    
    const queryParams = new URLSearchParams();
    queryParams.append('page', page.toString());
    queryParams.append('limit', limit.toString());
    
    const result = await this.makeRequest<UserActivityResponse>(`/api/users/me/activity?${queryParams.toString()}`, {
      method: 'GET',
    });
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to fetch user activity');
    }
    
    console.log('ApiClient: getUserActivity result:', result.data);
    return result.data!;
  }

  logout(): void {
    console.log('ApiClient: Logout called');
    this.removeTokens();
    console.log('ApiClient: Tokens removed');
  }

  // 인증 상태 확인
  isAuthenticated(): boolean {
    return !!this.token && !this.isTokenExpired(this.token);
  }

  // 테스트를 위한 public 메서드들 (원래는 private이지만 테스트 접근을 위해 public으로 노출)
  public saveTokenPublic(token: string, refreshToken?: string): void {
    return this.saveTokens(token, refreshToken);
  }

  public getHeadersPublic(): Record<string, string> {
    return this.getHeaders();
  }

  // 세션 상태 확인을 위한 public 메서드들
  public getSessionInfo() {
    const loginTime = this.getLoginTime();
    const refreshCount = this.getRefreshCount();
    const isExpired = this.isSessionExpired();
    const showWarning = this.shouldShowSessionWarning();
    
    let timeRemaining = 0;
    if (loginTime) {
      const elapsed = (Date.now() - loginTime.getTime()) / (1000 * 60 * 60);
      timeRemaining = Math.max(0, SESSION_CONFIG.MAX_SESSION_HOURS - elapsed);
    }
    
    return {
      loginTime,
      refreshCount,
      maxRefreshCount: SESSION_CONFIG.MAX_REFRESH_COUNT,
      isExpired,
      showWarning,
      timeRemaining: Math.round(timeRemaining * 100) / 100, // 소수점 2자리
      maxSessionHours: SESSION_CONFIG.MAX_SESSION_HOURS
    };
  }

  public extendSession(): boolean {
    // 세션 연장 요청 (리프레시 토큰으로 갱신 시도)
    if (this.isSessionExpired()) {
      console.log('ApiClient: Cannot extend expired session');
      return false;
    }
    
    console.log('ApiClient: Extending session by refreshing token');
    this.refreshAccessToken();
    return true;
  }

  // JWT 검증 메서드들
  public isValidJWTFormat(token: string): boolean {
    return validateJWTFormat(token);
  }

  public decodeJWTPayload(token: string): any {
    return decodeJWTPayload(token);
  }

  public isTokenExpired(token: string): boolean {
    return isTokenExpired(token);
  }

  // 기존 debugAuth 메서드 개선
  debugAuth(): void {
    console.log('=== Auth Debug Info ===');
    console.log('Current token in memory:', this.token ? `${this.token.substring(0, 10)}...` : 'null');
    
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('authToken');
      console.log('Stored token in localStorage:', storedToken ? `${storedToken.substring(0, 10)}...` : 'null');
      
      if (storedToken) {
        try {
          console.log('Token valid format:', this.isValidJWTFormat(storedToken));
          console.log('Token expired:', this.isTokenExpired(storedToken));
          
          const payload = this.decodeJWTPayload(storedToken);
          console.log('Token payload:', payload);
          console.log('Token expires at:', new Date(payload.exp * 1000));
          console.log('Current time:', new Date());
        } catch (e) {
          console.log('Token decode error:', e);
        }
      }
    }
    console.log('=======================');
  }

  // 게시글 관련 API
  async getPosts(filters: PostFilters = {}): Promise<ApiResponse<PaginatedResponse<Post>>> {
    console.log('🚀 getPosts 호출 - filters:', filters);
    
    const queryParams = new URLSearchParams();
    
    if (filters.type) queryParams.append('type', filters.type);
    if (filters.service) queryParams.append('service_type', filters.service);
    if (filters.metadata_type) queryParams.append('metadata_type', filters.metadata_type);
    if (filters.sortBy) queryParams.append('sort_by', filters.sortBy);
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.page) queryParams.append('page', filters.page.toString());
    if (filters.size) queryParams.append('size', filters.size.toString());

    const query = queryParams.toString();
    const endpoint = `/api/posts/${query ? `?${query}` : ''}`;
    
    console.log('📡 API 요청 - endpoint:', endpoint);

    return this.makeRequest<PaginatedResponse<Post>>(endpoint);
  }

  async searchPosts(filters: PostFilters = {}): Promise<ApiResponse<PaginatedResponse<Post>>> {
    const queryParams = new URLSearchParams();
    
    // 검색 쿼리 (백엔드에서 'q' 파라미터 기대)
    if (filters.query) queryParams.append('q', filters.query);
    
    // 기타 필터 파라미터
    if (filters.service) queryParams.append('service', filters.service);
    if (filters.metadata_type) queryParams.append('metadata_type', filters.metadata_type);
    if (filters.category) queryParams.append('category', filters.category);
    if (filters.sortBy) queryParams.append('sortBy', filters.sortBy);
    if (filters.page) queryParams.append('page', filters.page.toString());
    if (filters.size) queryParams.append('size', filters.size.toString());

    const query = queryParams.toString();
    const endpoint = `/api/posts/search${query ? `?${query}` : ''}`;

    return this.makeRequest<PaginatedResponse<Post>>(endpoint);
  }

  async getPost(slug: string): Promise<ApiResponse<Post>> {
    return this.makeRequest<Post>(`/api/posts/${slug}`);
  }


  // 🚀 완전 통합 Aggregation으로 게시글 + 작성자 + 댓글 + 댓글작성자 + 사용자반응을 모두 한 번에 조회
  async getPostComplete(slug: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/posts/${slug}/complete`);
  }

  async createPost(postData: CreatePostRequest): Promise<ApiResponse<Post>> {
    console.log('🚀 createPost 호출 - 전송할 데이터:', JSON.stringify(postData, null, 2));
    return this.makeRequest<Post>('/api/posts/', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
  }

  async updatePost(slug: string, postData: Partial<CreatePostRequest>): Promise<ApiResponse<Post>> {
    console.log('🚀 updatePost 호출 - 전송할 데이터:', JSON.stringify(postData, null, 2));
    return this.makeRequest<Post>(`/api/posts/${slug}`, {
      method: 'PUT',
      body: JSON.stringify(postData),
    });
  }

  async deletePost(slug: string): Promise<ApiResponse<void>> {
    return this.makeRequest<void>(`/api/posts/${slug}`, {
      method: 'DELETE',
    });
  }

  // 댓글 관련 API
  async getComments(postSlug: string, page: number = 1): Promise<ApiResponse<CommentListResponse>> {
    return this.makeRequest<CommentListResponse>(`/api/posts/${postSlug}/comments?page=${page}`);
  }

  // 🚀 2단계: 배치 조회로 댓글과 작성자 정보 함께 조회
  async getCommentsBatch(postSlug: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/posts/${postSlug}/comments`);
  }

  async createComment(postSlug: string, commentData: CreateCommentRequest): Promise<ApiResponse<Comment>> {
    console.log('🚀 댓글 작성 API 호출:', { postSlug, commentData });
    
    const response = await this.makeRequest<Comment>(`/api/posts/${postSlug}/comments`, {
      method: 'POST',
      body: JSON.stringify(commentData),
    });
    
    console.log('🔍 댓글 작성 API 응답:', {
      success: response.success,
      data: response.data,
      error: response.error,
      timestamp: response.timestamp
    });
    
    return response;
  }

  async updateComment(postSlug: string, commentId: string, content: string): Promise<ApiResponse<Comment>> {
    console.log('API updateComment 호출:', { postSlug, commentId, content });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}`;
    console.log('편집 요청 URL:', endpoint);
    
    return this.makeRequest<Comment>(endpoint, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteComment(postSlug: string, commentId: string): Promise<ApiResponse<void>> {
    console.log('API deleteComment 호출:', { postSlug, commentId });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}`;
    console.log('삭제 요청 URL:', endpoint);
    
    return this.makeRequest<void>(endpoint, {
      method: 'DELETE',
    });
  }

  // 답글 작성 API
  async createReply(postSlug: string, commentId: string, content: string): Promise<ApiResponse<Comment>> {
    return this.makeRequest<Comment>(`/api/posts/${postSlug}/comments/${commentId}/replies`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // 댓글 좋아요/싫어요 API
  async likeComment(postSlug: string, commentId: string): Promise<ApiResponse<any>> {
    console.log('API likeComment 호출:', { postSlug, commentId });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}/like`;
    console.log('좋아요 요청 URL:', endpoint);
    
    return this.makeRequest<any>(endpoint, {
      method: 'POST',
    });
  }

  async dislikeComment(postSlug: string, commentId: string): Promise<ApiResponse<any>> {
    console.log('API dislikeComment 호출:', { postSlug, commentId });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}/dislike`;
    console.log('싫어요 요청 URL:', endpoint);
    
    return this.makeRequest<any>(endpoint, {
      method: 'POST',
    });
  }

  // 반응 관련 API (게시글용 - API v3 명세서 기준)
  async toggleReaction(
    targetId: string,
    targetType: 'post' | 'comment',
    reactionType: ReactionType
  ): Promise<ApiResponse<any>> {
    if (targetType === 'post') {
      // 게시글 반응은 slug 기반 개별 엔드포인트 사용
      return this.makeRequest<any>(`/api/posts/${targetId}/${reactionType}`, {
        method: 'POST',
      });
    } else {
      // 댓글 반응은 일반 reactions 엔드포인트 사용 (구현 예정)
      return this.makeRequest<any>(`/api/reactions`, {
        method: 'POST',
        body: JSON.stringify({
          target_id: targetId,
          target_type: targetType,
          reaction_type: reactionType,
        }),
      });
    }
  }

  async getUserReactions(targetId: string, targetType: 'post' | 'comment'): Promise<ApiResponse<Reaction[]>> {
    return this.makeRequest<Reaction[]>(`/api/reactions?target_id=${targetId}&target_type=${targetType}`);
  }

  // 게시글 반응 개별 메서드들 (더 명확한 API)
  async likePost(slug: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/posts/${slug}/like`, {
      method: 'POST',
    });
  }

  async dislikePost(slug: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/posts/${slug}/dislike`, {
      method: 'POST',
    });
  }

  async bookmarkPost(slug: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/posts/${slug}/bookmark`, {
      method: 'POST',
    });
  }

  // 🆕 서비스 게시글 확장 통계 조회
  async getServicePostWithExtendedStats(slug: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/posts/services/${slug}`);
  }

  // 🆕 서비스 게시글 목록 확장 통계 조회
  async getServicePostsWithExtendedStats(
    page: number = 1, 
    size: number = 20, 
    sortBy: string = "created_at"
  ): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
      sort_by: sortBy
    });
    return this.makeRequest<any>(`/api/posts/services?${params.toString()}`);
  }

  // 🆕 서비스 문의/후기 API
  async createServiceInquiry(postSlug: string, inquiryData: CreateCommentRequest): Promise<ApiResponse<Comment>> {
    return this.makeRequest<Comment>(`/api/posts/${postSlug}/comments/inquiry`, {
      method: 'POST',
      body: JSON.stringify(inquiryData),
    });
  }

  async createServiceReview(postSlug: string, reviewData: CreateCommentRequest): Promise<ApiResponse<Comment>> {
    return this.makeRequest<Comment>(`/api/posts/${postSlug}/comments/review`, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  }

  // 이메일 인증 API
  async sendVerificationEmail(request: EmailVerificationRequest): Promise<ApiResponse<EmailVerificationResponse>> {
    return this.makeRequest<EmailVerificationResponse>('/api/auth/send-verification-email', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async verifyEmailCode(request: EmailVerificationCodeRequest): Promise<ApiResponse<EmailVerificationCodeResponse>> {
    return this.makeRequest<EmailVerificationCodeResponse>('/api/auth/verify-email-code', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // API 테스트용 메서드
  async testApiCall(request: ApiTestRequest): Promise<ApiTestResponse> {
    const startTime = Date.now();
    
    try {
      let url = `${this.baseURL}${request.endpoint}`;
      
      // Query parameters 처리
      if (request.queryParams) {
        const queryParams = new URLSearchParams(request.queryParams);
        url += `?${queryParams.toString()}`;
      }

      const response = await fetch(url, {
        method: request.method,
        headers: {
          'Content-Type': 'application/json',
          ...request.headers,
        },
        body: request.body ? JSON.stringify(request.body) : undefined,
      });

      const data = await response.json();
      const duration = Date.now() - startTime;

      return {
        status: response.status,
        data,
        headers: Object.fromEntries(response.headers.entries()),
        duration,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      
      return {
        status: 0,
        data: {
          error: error instanceof Error ? error.message : 'Unknown error',
        },
        headers: {},
        duration,
        timestamp: new Date().toISOString(),
      };
    }
  }

  // 알림 관련 API
  async getAlertRules(): Promise<ApiResponse<{ rules: AlertRule[] }>> {
    return this.makeRequest<{ rules: AlertRule[] }>('/api/alerts/rules');
  }

  async getAvailableMetrics(): Promise<ApiResponse<{ metrics: any[], categories: string[] }>> {
    return this.makeRequest<{ metrics: any[], categories: string[] }>('/api/alerts/metrics');
  }

  async createAlertRule(ruleData: CreateAlertRuleRequest): Promise<ApiResponse<AlertRule>> {
    return this.makeRequest<AlertRule>('/api/alerts/rules', {
      method: 'POST',
      body: JSON.stringify(ruleData),
    });
  }

  async updateAlertRule(ruleId: string, ruleData: UpdateAlertRuleRequest): Promise<ApiResponse<AlertRule>> {
    return this.makeRequest<AlertRule>(`/api/alerts/rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(ruleData),
    });
  }

  async deleteAlertRule(ruleId: string): Promise<ApiResponse<void>> {
    return this.makeRequest<void>(`/api/alerts/rules/${ruleId}`, {
      method: 'DELETE',
    });
  }

  async getAlertStatistics(): Promise<ApiResponse<AlertStatistics>> {
    return this.makeRequest<AlertStatistics>('/api/alerts/statistics');
  }

  async getAlertHistory(
    page: number = 1,
    limit: number = 20,
    ruleId?: string
  ): Promise<ApiResponse<{ alerts: AlertHistory[], total: number }>> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    
    if (ruleId) {
      params.append('rule_id', ruleId);
    }
    
    return this.makeRequest<{ alerts: AlertHistory[], total: number }>(`/api/alerts/history?${params.toString()}`);
  }

  async evaluateAlertRules(): Promise<ApiResponse<{ evaluated: number; triggered: number }>> {
    return this.makeRequest<{ evaluated: number; triggered: number }>('/api/alerts/evaluate', {
      method: 'POST',
    });
  }

  async toggleAlertRule(ruleId: string): Promise<ApiResponse<AlertRule>> {
    return this.makeRequest<AlertRule>(`/api/alerts/rules/${ruleId}/toggle`, {
      method: 'POST',
    });
  }

  async testAlertRule(ruleId: string): Promise<ApiResponse<{ success: boolean; message: string }>> {
    return this.makeRequest<{ success: boolean; message: string }>(`/api/alerts/rules/${ruleId}/test`, {
      method: 'POST',
    });
  }

  async getAlertSystemHealth(): Promise<ApiResponse<any>> {
    return this.makeRequest<any>('/api/alerts/health');
  }

  async testAlertSystem(): Promise<ApiResponse<any>> {
    return this.makeRequest<any>('/api/alerts/test', {
      method: 'POST',
    });
  }

  // 관리자 문의 관리 API
  async getInquiries(
    page: number = 1,
    page_size: number = 20,
    inquiry_type?: string,
    status?: string
  ): Promise<ApiResponse<{
    items: any[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: page_size.toString(),
    });
    
    if (inquiry_type) {
      params.append('inquiry_type', inquiry_type);
    }
    
    if (status) {
      params.append('status', status);
    }
    
    return this.makeRequest<{
      items: any[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/api/admin/inquiries?${params.toString()}`);
  }

  async getInquiryById(inquiryId: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/admin/inquiries/${inquiryId}`);
  }

  async updateInquiryStatus(inquiryId: string, status: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/admin/inquiries/${inquiryId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // 관리자 사용자 권한 관리 API
  async getUserById(userId: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/admin/users/${userId}`);
  }

  async updateUserPermissions(
    userId: string,
    permissions: {
      can_write_moving_services?: boolean;
      can_write_expert_tips?: boolean;
    }
  ): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/admin/users/${userId}/permissions`, {
      method: 'PUT',
      body: JSON.stringify(permissions),
    });
  }

  // 신고 관리 API
  async reportPost(postId: string, content: string): Promise<ApiResponse<{
    id: string;
    target_type: string;
    target_id: string;
    content: string;
    reporter_id: string;
    created_at: string;
    status: string;
  }>> {
    return this.makeRequest<{
      id: string;
      target_type: string;
      target_id: string;
      content: string;
      reporter_id: string;
      created_at: string;
      status: string;
    }>(`/api/reports/post/${postId}`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  async reportComment(commentId: string, content: string): Promise<ApiResponse<{
    id: string;
    target_type: string;
    target_id: string;
    content: string;
    reporter_id: string;
    created_at: string;
    status: string;
  }>> {
    return this.makeRequest<{
      id: string;
      target_type: string;
      target_id: string;
      content: string;
      reporter_id: string;
      created_at: string;
      status: string;
    }>(`/api/reports/comment/${commentId}`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  async getReports(
    page: number = 1,
    page_size: number = 20,
    status?: string,
    target_type?: string
  ): Promise<ApiResponse<{
    items: any[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }>> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: page_size.toString(),
    });
    
    if (status) {
      params.append('status', status);
    }
    
    if (target_type) {
      params.append('target_type', target_type);
    }
    
    return this.makeRequest<{
      items: any[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/api/reports?${params.toString()}`);
  }

  async updateReportStatus(reportId: string, status: string): Promise<ApiResponse<any>> {
    return this.makeRequest<any>(`/api/reports/${reportId}/status?new_status=${status}`, {
      method: 'PUT',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;