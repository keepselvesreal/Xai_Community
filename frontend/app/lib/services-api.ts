/**
 * 서비스 관련 API 함수들 (TDD REFACTOR 단계)
 * 
 * 이 모듈은 서비스(업체) 관련 API 호출을 담당합니다.
 * 기존 Posts API를 래핑하여 서비스 전용 인터페이스를 제공합니다.
 */

import type { 
  Post, 
  CreatePostRequest, 
  ApiResponse, 
  PaginatedResponse, 
  PostFilters 
} from "~/types";
import type { ServicePost, ServiceCategory } from "~/types/service-types";
import { 
  parseServicePost, 
  serializeServicePost, 
  convertServicePostToMockService,
  mapServiceCategoryToEnglish 
} from "~/types/service-types";
import { apiClient } from "./api";

// 서비스 필터 타입
export interface ServiceFilters {
  /** 서비스 카테고리 */
  category?: ServiceCategory;
  /** 검색 키워드 */
  search?: string;
  /** 페이지 번호 (1부터 시작) */
  page?: number;
  /** 페이지 크기 (기본값: 20) */
  size?: number;
  /** 정렬 기준 */
  sortBy?: 'created_at' | 'rating' | 'name';
}

// 서비스 생성 요청 타입  
export interface CreateServiceRequest {
  /** 서비스 게시글 데이터 */
  servicePost: ServicePost;
  /** 서비스 카테고리 */
  category: ServiceCategory;
}

// 서비스 응답 타입 (Post에서 ServicePost로 변환된 데이터)
export interface ServiceResponse extends Omit<Post, 'content'> {
  /** 파싱된 서비스 데이터 */
  serviceData: ServicePost;
  /** 원본 content */
  originalContent: string;
}

// 기본 필터 값
const DEFAULT_FILTERS: Required<Omit<ServiceFilters, 'category' | 'search'>> = {
  page: 1,
  size: 20,
  sortBy: 'created_at'
};

/**
 * Post 객체를 ServiceResponse로 변환
 * @param post Post 객체
 * @returns ServiceResponse 객체 또는 null (파싱 실패 시)
 */
function convertPostToServiceResponse(post: Post): ServiceResponse | null {
  try {
    const serviceData = parseServicePost(post.content);
    return {
      ...post,
      serviceData,
      originalContent: post.content
    };
  } catch (error) {
    console.warn('Failed to parse service post:', error);
    return null;
  }
}

/**
 * 필터를 PostFilters로 변환
 * @param filters ServiceFilters
 * @returns PostFilters
 */
function convertFiltersToPostFilters(filters: ServiceFilters): PostFilters {
  const mergedFilters = { ...DEFAULT_FILTERS, ...filters };
  
  const postFilters: PostFilters = {
    service: 'residential_community',
    type: 'moving services', // 서비스 타입 고정
    page: mergedFilters.page,
    size: mergedFilters.size,
    sortBy: mergedFilters.sortBy,
    search: mergedFilters.search
  };

  // 카테고리 필터가 있는 경우 metadata.category로 필터링
  if (mergedFilters.category) {
    postFilters.category = mergedFilters.category;
  }

  return postFilters;
}

/**
 * 서비스 목록 조회
 * @param filters 필터 조건
 * @returns 서비스 목록
 */
export async function fetchServices(filters: ServiceFilters = {}): Promise<ApiResponse<PaginatedResponse<Post>>> {
  try {
    const postFilters = convertFiltersToPostFilters(filters);
    const response = await apiClient.getPosts(postFilters);
    
    // 성공 시 추가 처리나 검증 로직을 여기에 추가할 수 있음
    if (response.success && response.data) {
      console.log(`Successfully fetched ${response.data.items.length} services`);
    }
    
    return response;
  } catch (error) {
    console.error('Failed to fetch services:', error);
    throw error;
  }
}

/**
 * 카테고리별 서비스 조회
 * @param category 서비스 카테고리
 * @param filters 추가 필터 조건
 * @returns 해당 카테고리 서비스 목록
 */
export async function fetchServicesByCategory(
  category: ServiceCategory, 
  filters: Omit<ServiceFilters, 'category'> = {}
): Promise<ApiResponse<PaginatedResponse<Post>>> {
  return fetchServices({ ...filters, category });
}

/**
 * 새로운 서비스 생성
 * @param serviceData 서비스 데이터
 * @returns 생성된 서비스 게시글
 * @throws Error 유효하지 않은 서비스 데이터인 경우
 */
export async function createService(serviceData: CreateServiceRequest): Promise<ApiResponse<Post>> {
  try {
    // 서비스 데이터 검증
    if (!serviceData.servicePost.company.name.trim()) {
      throw new Error('업체명은 필수입니다');
    }
    
    if (serviceData.servicePost.services.length === 0) {
      throw new Error('최소 하나의 서비스가 필요합니다');
    }

    const postData: CreatePostRequest = {
      title: serviceData.servicePost.company.name,
      content: serializeServicePost(serviceData.servicePost),
      service: 'residential_community',
      metadata: {
        type: 'moving services',
        category: serviceData.category,
        tags: [serviceData.category, '업체', '서비스'],
        visibility: 'public'
      }
    };

    const response = await apiClient.createPost(postData);
    
    if (response.success) {
      console.log(`Successfully created service: ${serviceData.servicePost.company.name}`);
    }
    
    return response;
  } catch (error) {
    console.error('Failed to create service:', error);
    throw error;
  }
}

/**
 * 서비스 검색
 * @param query 검색 쿼리
 * @param filters 추가 필터 조건
 * @returns 검색된 서비스 목록
 */
export async function searchServices(
  query: string, 
  filters: Omit<ServiceFilters, 'search'> = {}
): Promise<ApiResponse<PaginatedResponse<Post>>> {
  if (!query.trim()) {
    console.warn('Empty search query provided');
    return fetchServices(filters);
  }
  
  return fetchServices({ ...filters, search: query.trim() });
}

/**
 * 특정 서비스 조회
 * @param id 서비스 ID (slug)
 * @returns 서비스 상세 정보
 */
export async function getServiceById(id: string): Promise<ApiResponse<Post>> {
  if (!id.trim()) {
    throw new Error('Service ID is required');
  }
  
  try {
    const response = await apiClient.getPost(id.trim());
    
    if (response.success && response.data) {
      // 서비스 데이터 검증
      try {
        parseServicePost(response.data.content);
        console.log(`Successfully fetched service: ${id}`);
      } catch (parseError) {
        console.warn(`Service ${id} has invalid content format:`, parseError);
      }
    }
    
    return response;
  } catch (error) {
    console.error(`Failed to get service ${id}:`, error);
    throw error;
  }
}

/**
 * 서비스 데이터를 ServiceResponse 배열로 변환
 * @param posts Post 배열
 * @returns ServiceResponse 배열 (파싱 가능한 것들만)
 */
export function convertPostsToServiceResponses(posts: Post[]): ServiceResponse[] {
  return posts
    .map(convertPostToServiceResponse)
    .filter((service): service is ServiceResponse => service !== null);
}

/**
 * 서비스 통계 조회
 * @param filters 필터 조건
 * @returns 서비스 통계 정보
 */
export async function getServiceStats(filters: ServiceFilters = {}): Promise<{
  totalServices: number;
  servicesByCategory: Record<ServiceCategory, number>;
}> {
  try {
    const response = await fetchServices({ ...filters, size: 1000 }); // 전체 조회
    
    if (!response.success || !response.data) {
      throw new Error('Failed to fetch service stats');
    }
    
    const serviceResponses = convertPostsToServiceResponses(response.data.items);
    const servicesByCategory: Record<ServiceCategory, number> = {
      '이사': 0,
      '청소': 0,
      '에어컨': 0
    };
    
    serviceResponses.forEach(service => {
      if (service.metadata.category && service.metadata.category in servicesByCategory) {
        servicesByCategory[service.metadata.category as ServiceCategory]++;
      }
    });
    
    return {
      totalServices: serviceResponses.length,
      servicesByCategory
    };
  } catch (error) {
    console.error('Failed to get service stats:', error);
    throw error;
  }
}