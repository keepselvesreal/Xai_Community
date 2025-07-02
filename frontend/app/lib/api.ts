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
} from "~/types";
import { validateJWTFormat, decodeJWTPayload, isTokenExpired } from './jwt-utils';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.your-domain.com' 
  : 'http://localhost:8000';

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
      let token = localStorage.getItem('authToken');
      let refreshToken = localStorage.getItem('refreshToken');
      
      // JSON.stringify로 저장된 경우 파싱
      if (token && (token.startsWith('"') && token.endsWith('"'))) {
        try {
          token = JSON.parse(token);
          if (token) {
            localStorage.setItem('authToken', token); // 정리된 토큰 재저장
            console.log('ApiClient: Cleaned JSON stringified token');
          }
        } catch (e) {
          console.error('ApiClient: Failed to parse token:', e);
        }
      }
      
      // Bearer 접두사가 잘못 저장된 경우 제거
      if (token && token.startsWith('Bearer ')) {
        token = token.substring(7);
        localStorage.setItem('authToken', token);
        console.log('ApiClient: Cleaned Bearer prefix from stored token');
      }
      
      this.token = token;
      this.refreshToken = refreshToken;
      console.log('ApiClient: Tokens loaded from localStorage:', 
        this.token ? `access: ${this.token.substring(0, 10)}...` : 'access: null',
        this.refreshToken ? `refresh: ${this.refreshToken.substring(0, 10)}...` : 'refresh: null'
      );
      
      // 토큰이 있으면 자동 갱신 타이머 시작
      if (this.token && this.refreshToken) {
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
      localStorage.setItem('authToken', cleanToken);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      console.log('ApiClient: Tokens saved to localStorage:', 
        cleanToken ? `access: ${cleanToken.substring(0, 10)}...` : 'access: null',
        refreshToken ? `refresh: ${refreshToken.substring(0, 10)}...` : 'refresh: unchanged'
      );
    }
  }

  private removeTokens(): void {
    this.token = null;
    this.refreshToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');
    }
    this.stopTokenRefreshTimer();
  }

  private startTokenRefreshTimer(): void {
    if (typeof window === 'undefined') return;
    
    // 기존 타이머 정리
    this.stopTokenRefreshTimer();
    
    // 5분마다 토큰 상태 확인
    this.tokenCheckInterval = window.setInterval(() => {
      this.checkAndRefreshToken();
    }, 5 * 60 * 1000); // 5분
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
      // 토큰이 10분 이내에 만료되는지 확인
      if (this.isTokenExpired(this.token) || this.isTokenExpiringSoon(this.token, 10 * 60)) {
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
      
      // 디버깅용 로그
      console.log('ApiClient: Setting Authorization header with token:', `Bearer ${cleanToken.substring(0, 10)}...`);
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
    try {
      console.log('ApiClient: Attempting to refresh access token...');
      
      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (!response.ok) {
        console.error('ApiClient: Token refresh failed:', response.status, response.statusText);
        // 리프레시 토큰이 만료되었거나 무효함 - 로그아웃 처리
        this.removeTokens();
        return false;
      }

      const data = await response.json();
      console.log('ApiClient: Token refresh successful');
      
      // 새로운 access token 저장 (refresh token은 그대로 유지)
      this.saveTokens(data.access_token);
      
      // 토큰 갱신 후 타이머 재시작
      this.startTokenRefreshTimer();
      
      return true;
    } catch (error) {
      console.error('ApiClient: Token refresh error:', error);
      this.removeTokens();
      return false;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    return this.makeRequestWithRetry<T>(endpoint, options, false);
  }

  private async makeRequestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry: boolean = false
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    // 토큰이 없고 refresh token이 있다면 먼저 토큰 갱신 시도
    if (!this.token && this.refreshToken && !isRetry) {
      console.log('ApiClient: No access token but refresh token exists, attempting refresh...');
      const refreshSuccess = await this.refreshAccessToken();
      if (!refreshSuccess) {
        console.log('ApiClient: Token refresh failed before request');
        this.notifyTokenExpired();
        return {
          success: false,
          error: 'Authorization header is required',
          timestamp: new Date().toISOString(),
        };
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
        
        // FastAPI validation errors 처리
        if (response.status === 422 && data.detail) {
          const errorMessages = Array.isArray(data.detail) 
            ? data.detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join(', ')
            : data.detail;
          throw new Error(`Validation Error: ${errorMessages}`);
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
    return this.request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    console.log('ApiClient: getCurrentUser called');
    const result = await this.request<User>('/api/auth/profile');
    console.log('ApiClient: getCurrentUser result:', result);
    return result;
  }

  logout(): void {
    console.log('ApiClient: Logout called');
    this.removeTokens();
    console.log('ApiClient: Tokens removed');
  }

  // 테스트를 위한 public 메서드들 (원래는 private이지만 테스트 접근을 위해 public으로 노출)
  public saveTokenPublic(token: string, refreshToken?: string): void {
    return this.saveTokens(token, refreshToken);
  }

  public getHeadersPublic(): Record<string, string> {
    return this.getHeaders();
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

    return this.request<PaginatedResponse<Post>>(endpoint);
  }

  async getPost(slug: string): Promise<ApiResponse<Post>> {
    return this.request<Post>(`/api/posts/${slug}`);
  }

  async createPost(postData: CreatePostRequest): Promise<ApiResponse<Post>> {
    return this.request<Post>('/api/posts', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
  }

  async updatePost(slug: string, postData: Partial<CreatePostRequest>): Promise<ApiResponse<Post>> {
    return this.request<Post>(`/api/posts/${slug}`, {
      method: 'PUT',
      body: JSON.stringify(postData),
    });
  }

  async deletePost(slug: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/api/posts/${slug}`, {
      method: 'DELETE',
    });
  }

  // 댓글 관련 API
  async getComments(postSlug: string, page: number = 1): Promise<ApiResponse<CommentListResponse>> {
    return this.request<CommentListResponse>(`/api/posts/${postSlug}/comments?page=${page}`);
  }

  async createComment(postSlug: string, commentData: CreateCommentRequest): Promise<ApiResponse<Comment>> {
    return this.request<Comment>(`/api/posts/${postSlug}/comments`, {
      method: 'POST',
      body: JSON.stringify(commentData),
    });
  }

  async updateComment(postSlug: string, commentId: string, content: string): Promise<ApiResponse<Comment>> {
    console.log('API updateComment 호출:', { postSlug, commentId, content });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}`;
    console.log('편집 요청 URL:', endpoint);
    
    return this.request<Comment>(endpoint, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteComment(postSlug: string, commentId: string): Promise<ApiResponse<void>> {
    console.log('API deleteComment 호출:', { postSlug, commentId });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}`;
    console.log('삭제 요청 URL:', endpoint);
    
    return this.request<void>(endpoint, {
      method: 'DELETE',
    });
  }

  // 답글 작성 API
  async createReply(postSlug: string, commentId: string, content: string): Promise<ApiResponse<Comment>> {
    return this.request<Comment>(`/api/posts/${postSlug}/comments/${commentId}/replies`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // 댓글 좋아요/싫어요 API
  async likeComment(postSlug: string, commentId: string): Promise<ApiResponse<any>> {
    console.log('API likeComment 호출:', { postSlug, commentId });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}/like`;
    console.log('좋아요 요청 URL:', endpoint);
    
    return this.request<any>(endpoint, {
      method: 'POST',
    });
  }

  async dislikeComment(postSlug: string, commentId: string): Promise<ApiResponse<any>> {
    console.log('API dislikeComment 호출:', { postSlug, commentId });
    const endpoint = `/api/posts/${postSlug}/comments/${commentId}/dislike`;
    console.log('싫어요 요청 URL:', endpoint);
    
    return this.request<any>(endpoint, {
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
      return this.request<any>(`/api/posts/${targetId}/${reactionType}`, {
        method: 'POST',
      });
    } else {
      // 댓글 반응은 일반 reactions 엔드포인트 사용 (구현 예정)
      return this.request<any>(`/api/reactions`, {
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
    return this.request<Reaction[]>(`/api/reactions?target_id=${targetId}&target_type=${targetType}`);
  }

  // 게시글 반응 개별 메서드들 (더 명확한 API)
  async likePost(slug: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/posts/${slug}/like`, {
      method: 'POST',
    });
  }

  async dislikePost(slug: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/posts/${slug}/dislike`, {
      method: 'POST',
    });
  }

  async bookmarkPost(slug: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/posts/${slug}/bookmark`, {
      method: 'POST',
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
}

export const apiClient = new ApiClient();
export default apiClient;