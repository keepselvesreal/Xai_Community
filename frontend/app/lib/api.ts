import type {
  User,
  AuthToken,
  LoginRequest,
  RegisterRequest,
  Post,
  CreatePostRequest,
  Comment,
  CreateCommentRequest,
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

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.loadToken();
  }

  private loadToken(): void {
    if (typeof window !== 'undefined') {
      let token = localStorage.getItem('authToken');
      
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
      console.log('ApiClient: Token loaded from localStorage:', this.token ? `${this.token.substring(0, 10)}...` : 'null');
    }
  }

  private saveToken(token: string): void {
    // Bearer 접두사 제거 (토큰만 저장)
    const cleanToken = token.startsWith('Bearer ') ? token.substring(7) : token;
    
    this.token = cleanToken;
    if (typeof window !== 'undefined') {
      localStorage.setItem('authToken', cleanToken);
      console.log('ApiClient: Token saved to localStorage:', cleanToken ? `${cleanToken.substring(0, 10)}...` : 'null');
    }
  }

  private removeToken(): void {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
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

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      console.log('ApiClient: Making request to:', url);
      const response = await fetch(url, config);
      console.log('ApiClient: Response received:', response.status, response.statusText);
      
      const data = await response.json();
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

      this.saveToken(data.access_token);
      
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
    this.removeToken();
  }

  // 테스트를 위한 public 메서드들 (원래는 private이지만 테스트 접근을 위해 public으로 노출)
  public saveTokenPublic(token: string): void {
    return this.saveToken(token);
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
  async getComments(postSlug: string, page: number = 1): Promise<ApiResponse<PaginatedResponse<Comment>>> {
    return this.request<PaginatedResponse<Comment>>(`/posts/${postSlug}/comments?page=${page}`);
  }

  async createComment(postSlug: string, commentData: CreateCommentRequest): Promise<ApiResponse<Comment>> {
    return this.request<Comment>(`/posts/${postSlug}/comments`, {
      method: 'POST',
      body: JSON.stringify(commentData),
    });
  }

  async updateComment(commentId: number, content: string): Promise<ApiResponse<Comment>> {
    return this.request<Comment>(`/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteComment(commentId: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/comments/${commentId}`, {
      method: 'DELETE',
    });
  }

  // 반응 관련 API
  async toggleReaction(
    targetId: number,
    targetType: 'post' | 'comment',
    reactionType: ReactionType
  ): Promise<ApiResponse<Reaction | null>> {
    return this.request<Reaction | null>(`/reactions`, {
      method: 'POST',
      body: JSON.stringify({
        target_id: targetId,
        target_type: targetType,
        reaction_type: reactionType,
      }),
    });
  }

  async getUserReactions(targetId: number, targetType: 'post' | 'comment'): Promise<ApiResponse<Reaction[]>> {
    return this.request<Reaction[]>(`/reactions?target_id=${targetId}&target_type=${targetType}`);
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