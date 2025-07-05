interface CacheData<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class CacheManager {
  private static readonly DEFAULT_TTL = 5 * 60 * 1000; // 5분

  /**
   * 데이터를 localStorage에 캐시합니다
   * @param key 캐시 키
   * @param data 저장할 데이터
   * @param ttl TTL (밀리초, 기본값: 5분)
   */
  static saveToCache<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    try {
      const cacheData: CacheData<T> = {
        data,
        timestamp: Date.now(),
        ttl
      };

      localStorage.setItem(key, JSON.stringify(cacheData));
    } catch (error) {
      console.warn('Failed to save to cache:', error);
    }
  }

  /**
   * localStorage에서 캐시된 데이터를 가져옵니다
   * @param key 캐시 키
   * @returns 캐시된 데이터 또는 null (만료/없음)
   */
  static getFromCache<T>(key: string): T | null {
    try {
      const cached = localStorage.getItem(key);
      if (!cached) return null;

      const cacheData: CacheData<T> = JSON.parse(cached);
      
      // 캐시 만료 검사
      if (Date.now() - cacheData.timestamp > cacheData.ttl) {
        localStorage.removeItem(key);
        return null;
      }

      return cacheData.data;
    } catch (error) {
      console.warn('Failed to get from cache:', error);
      return null;
    }
  }

  /**
   * 특정 키의 캐시를 제거합니다
   * @param key 캐시 키
   */
  static clearCache(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Failed to clear cache:', error);
    }
  }

  /**
   * 캐시가 유효한지 확인합니다 (만료되지 않았는지)
   * @param key 캐시 키
   * @returns 캐시 유효성 여부
   */
  static isCacheValid(key: string): boolean {
    try {
      const cached = localStorage.getItem(key);
      if (!cached) return false;

      const cacheData: CacheData<any> = JSON.parse(cached);
      return Date.now() - cacheData.timestamp <= cacheData.ttl;
    } catch (error) {
      return false;
    }
  }

  /**
   * 모든 캐시를 제거합니다
   */
  static clearAllCache(): void {
    try {
      localStorage.clear();
    } catch (error) {
      console.warn('Failed to clear all cache:', error);
    }
  }

  /**
   * 페이지별 캐시를 안전하게 제거합니다
   */
  static clearPageCaches(): void {
    try {
      Object.values(CACHE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });
      
      // 기타 캐시 키 패턴도 제거
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.includes('-cache')) {
          localStorage.removeItem(key);
          i--; // 인덱스 조정
        }
      }
    } catch (error) {
      console.warn('Failed to clear page caches:', error);
    }
  }
}

// 캐시 키 상수들
export const CACHE_KEYS = {
  INFO_POSTS: 'info-posts-cache',
  SERVICES_POSTS: 'services-posts-cache',
  TIPS_POSTS: 'tips-posts-cache',
  BOARD_POSTS: 'board-posts-cache',
  RECENT_POSTS: 'recent-posts-cache',
  USER_PROFILE: 'user-profile-cache',
} as const;