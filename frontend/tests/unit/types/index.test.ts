/**
 * 타입 정의 테스트
 * TDD Red 단계: 백엔드 호환성을 위한 타입 검증
 */

import type { 
  CreatePostRequest, 
  PostMetadata, 
  ServiceType, 
  Post,
  User 
} from '~/types';

describe('Type Definitions - Backend Compatibility', () => {
  describe('ServiceType', () => {
    test('should only allow residential_community value', () => {
      // Arrange & Act
      const validService: ServiceType = "residential_community";
      
      // Assert: 타입 컴파일 시점에서 검증됨
      expect(validService).toBe("residential_community");
      
      // 다음은 컴파일 에러가 발생해야 함 (TypeScript 타입 체크)
      // const invalidService: ServiceType = "community"; // 이전 값, 사용 불가
      // const anotherInvalid: ServiceType = "shopping"; // 이전 값, 사용 불가
    });
  });

  describe('PostMetadata', () => {
    test('should have required type and category fields', () => {
      // Arrange
      const validMetadata: PostMetadata = {
        type: "board",
        category: "입주정보"
      };
      
      // Assert
      expect(validMetadata.type).toBe("board");
      expect(validMetadata.category).toBe("입주정보");
    });

    test('should allow optional fields', () => {
      // Arrange
      const metadataWithOptionals: PostMetadata = {
        type: "board",
        category: "생활정보",
        tags: ["생활", "팁"],
        summary: "요약 내용",
        thumbnail: "https://example.com/thumb.jpg",
        attachments: ["file1.jpg", "file2.pdf"]
      };
      
      // Assert
      expect(metadataWithOptionals.tags).toEqual(["생활", "팁"]);
      expect(metadataWithOptionals.summary).toBe("요약 내용");
      expect(metadataWithOptionals.thumbnail).toBe("https://example.com/thumb.jpg");
      expect(metadataWithOptionals.attachments).toEqual(["file1.jpg", "file2.pdf"]);
    });

    test('should validate category values', () => {
      // Arrange: 유효한 카테고리 값들
      const validCategories = ["입주정보", "생활정보", "이야기"];
      
      validCategories.forEach(category => {
        const metadata: PostMetadata = {
          type: "board",
          category: category
        };
        
        // Assert
        expect(metadata.category).toBe(category);
      });
    });
  });

  describe('CreatePostRequest', () => {
    test('should match backend API structure exactly', () => {
      // Arrange: 백엔드 API가 기대하는 정확한 구조
      const createPostRequest: CreatePostRequest = {
        title: "테스트 게시글",
        content: "게시글 내용입니다.",
        service: "residential_community",
        metadata: {
          type: "board",
          category: "입주정보",
          tags: ["테스트", "입주"]
        }
      };
      
      // Assert: 모든 필수 필드가 있는지 확인
      expect(createPostRequest).toHaveProperty('title');
      expect(createPostRequest).toHaveProperty('content');
      expect(createPostRequest).toHaveProperty('service');
      expect(createPostRequest).toHaveProperty('metadata');
      
      // metadata 구조 확인
      expect(createPostRequest.metadata).toHaveProperty('type');
      expect(createPostRequest.metadata).toHaveProperty('category');
      
      // 타입 검증
      expect(typeof createPostRequest.title).toBe('string');
      expect(typeof createPostRequest.content).toBe('string');
      expect(createPostRequest.service).toBe('residential_community');
      expect(createPostRequest.metadata.type).toBe('board');
    });

    test('should not allow old service type values', () => {
      // Note: 이 테스트는 타입 시스템을 통해 컴파일 타임에 검증됨
      // 다음과 같은 코드는 TypeScript 에러가 발생해야 함:
      
      /*
      const invalidRequest: CreatePostRequest = {
        title: "테스트",
        content: "내용",
        service: "community", // 이전 값, 컴파일 에러 발생해야 함
        metadata: {
          type: "board",
          category: "입주정보"
        }
      };
      */
      
      // 실제로는 유효한 값만 허용됨을 확인
      const validRequest: CreatePostRequest = {
        title: "테스트",
        content: "내용",
        service: "residential_community", // 유일하게 허용되는 값
        metadata: {
          type: "board",
          category: "입주정보"
        }
      };
      
      expect(validRequest.service).toBe("residential_community");
    });
  });

  describe('Post Response Types', () => {
    test('should have string ID instead of number', () => {
      // Arrange: 백엔드가 반환하는 Post 구조
      const post: Post = {
        id: "507f1f77bcf86cd799439011", // MongoDB ObjectId 형식
        title: "테스트 게시글",
        content: "내용",
        slug: "test-slug",
        service: "residential_community",
        created_at: "2025-06-30T10:00:00Z",
        updated_at: "2025-06-30T10:00:00Z"
      };
      
      // Assert: ID가 string 타입인지 확인
      expect(typeof post.id).toBe('string');
      expect(post.id).toMatch(/^[a-f\d]{24}$/i); // MongoDB ObjectId 패턴
    });
  });

  describe('User Type Updates', () => {
    test('should use user_handle field consistently', () => {
      // Arrange: 백엔드와 일치하는 User 구조
      const user: User = {
        id: "507f1f77bcf86cd799439011",
        email: "test@example.com",
        user_handle: "test_user", // 백엔드에서 사용하는 필드명
        created_at: "2025-06-30T10:00:00Z",
        updated_at: "2025-06-30T10:00:00Z"
      };
      
      // Assert
      expect(user).toHaveProperty('user_handle');
      expect(typeof user.user_handle).toBe('string');
      expect(user.user_handle).toBe('test_user');
    });
  });
});

// Note: 이 테스트들은 현재 타입 정의가 수정되지 않았으므로 실패할 것입니다.
// TDD Red 단계: 타입 정의를 백엔드 호환으로 수정해야 합니다.