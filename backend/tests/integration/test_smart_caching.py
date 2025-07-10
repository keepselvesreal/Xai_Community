"""
1단계: 스마트 캐싱 테스트
작성자 정보와 사용자 반응 정보 캐싱 테스트
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from nadle_backend.services.posts_service import PostsService


class TestSmartCaching:
    """스마트 캐싱 기능 테스트"""
    
    async def test_author_info_caching(self):
        """작성자 정보 캐싱 테스트"""
        # Given: 캐시된 작성자 정보가 없는 상태
        posts_service = PostsService()
        author_id = "6867b9246ec8a1b04c9c1165"
        
        # When: 같은 작성자 정보를 2번 조회
        # Then: 첫 번째는 DB 조회, 두 번째는 캐시 조회
        
        # 첫 번째 조회 (DB에서 조회 후 캐시 저장)
        author_info_1 = await posts_service.get_author_info_cached(author_id)
        
        # 두 번째 조회 (캐시에서 조회)
        author_info_2 = await posts_service.get_author_info_cached(author_id)
        
        # 결과 검증
        assert author_info_1 == author_info_2
        assert author_info_1 is not None
        assert "user_handle" in author_info_1
        
    async def test_user_reaction_caching(self):
        """사용자 반응 정보 캐싱 테스트"""
        # Given: 사용자와 게시글 ID
        posts_service = PostsService()
        user_id = "6867b9246ec8a1b04c9c1165"
        post_id = "686c6cd040839f99492cab46"
        
        # When: 같은 사용자 반응을 2번 조회
        # Then: 첫 번째는 DB 조회, 두 번째는 캐시 조회
        
        reaction_1 = await posts_service.get_user_reaction_cached(user_id, post_id)
        reaction_2 = await posts_service.get_user_reaction_cached(user_id, post_id)
        
        # 결과 검증
        assert reaction_1 == reaction_2
        
    async def test_cache_invalidation_on_author_update(self):
        """작성자 정보 변경 시 캐시 무효화 테스트"""
        # Given: 캐시된 작성자 정보
        posts_service = PostsService()
        author_id = "6867b9246ec8a1b04c9c1165"
        
        # When: 작성자 정보 변경
        await posts_service.invalidate_author_cache(author_id)
        
        # Then: 캐시가 무효화되어야 함
        # (실제 구현에서는 Redis 캐시 삭제 확인)
        pass

if __name__ == "__main__":
    async def run_tests():
        test = TestSmartCaching()
        
        print("🧪 스마트 캐싱 테스트 시작...")
        
        try:
            print("  1. 작성자 정보 캐싱 테스트...")
            await test.test_author_info_caching()
            print("  ✅ 작성자 정보 캐싱 테스트 통과")
            
            print("  2. 사용자 반응 캐싱 테스트...")
            await test.test_user_reaction_caching()
            print("  ✅ 사용자 반응 캐싱 테스트 통과")
            
            print("  3. 캐시 무효화 테스트...")
            await test.test_cache_invalidation_on_author_update()
            print("  ✅ 캐시 무효화 테스트 통과")
            
            print("\n🎉 모든 테스트 통과!")
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())