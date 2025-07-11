"""
3단계: MongoDB Aggregation Pipeline 테스트
JOIN 쿼리로 한 번에 모든 데이터 조회 테스트
"""

import asyncio
from typing import Dict, Any


class TestAggregation:
    """Aggregation Pipeline 기능 테스트"""
    
    async def test_post_with_author_aggregation(self):
        """게시글 + 작성자 정보 Aggregation 테스트"""
        from nadle_backend.services.posts_service import PostsService
        
        posts_service = PostsService()
        
        # Given: 게시글 slug
        post_slug = "686c6cd040839f99492cab46-25-07-08-글쓰기"
        
        # When: Aggregation으로 게시글과 작성자 정보 한 번에 조회
        post_with_author = await posts_service.get_post_with_author_aggregated(post_slug)
        
        # Then: 게시글과 작성자 정보가 함께 반환되어야 함
        assert post_with_author is not None
        assert "title" in post_with_author
        assert "author" in post_with_author
        assert "user_handle" in post_with_author["author"]
        
        print(f"✅ Aggregation으로 게시글 + 작성자 정보 한 번에 조회 완료")
    
    async def test_post_with_comments_aggregation(self):
        """게시글 + 댓글 + 작성자 정보 Aggregation 테스트"""
        from nadle_backend.services.posts_service import PostsService
        
        posts_service = PostsService()
        
        # Given: 댓글이 있는 게시글 slug
        post_slug = "6867ba276ec8a1b04c9c1171-하이마트-철산점"
        
        # When: Aggregation으로 모든 정보 한 번에 조회
        full_data = await posts_service.get_post_with_comments_aggregated(post_slug)
        
        # Then: 게시글, 댓글, 작성자 정보가 모두 포함되어야 함
        assert full_data is not None
        assert "title" in full_data
        assert "author" in full_data
        assert "comments" in full_data
        
        for comment in full_data["comments"]:
            assert "content" in comment
            assert "author" in comment
            
        print(f"✅ Aggregation으로 게시글 + 댓글 + 작성자 정보 모두 한 번에 조회 완료")
    
    async def test_aggregation_performance_comparison(self):
        """Aggregation vs 기존 방식 성능 비교"""
        from nadle_backend.services.posts_service import PostsService
        import time
        
        posts_service = PostsService()
        post_slug = "686c6cd040839f99492cab46-25-07-08-글쓰기"
        
        # 기존 방식 (개별 조회)
        start_time = time.time()
        post = await posts_service.get_post(post_slug)
        author = await posts_service.get_author_info_cached(str(post.author_id))
        separate_time = (time.time() - start_time) * 1000
        
        # Aggregation 방식
        start_time = time.time()
        aggregated_data = await posts_service.get_post_with_author_aggregated(post_slug)
        aggregation_time = (time.time() - start_time) * 1000
        
        print(f"📊 성능 비교:")
        print(f"   개별 조회: {separate_time:.2f}ms")
        print(f"   Aggregation: {aggregation_time:.2f}ms")
        print(f"   개선율: {((separate_time - aggregation_time) / separate_time * 100):.1f}%")


if __name__ == "__main__":
    async def run_tests():
        test = TestAggregation()
        
        print("🧪 Aggregation Pipeline 테스트 시작...")
        
        try:
            print("  1. 게시글 + 작성자 정보 Aggregation 테스트...")
            await test.test_post_with_author_aggregation()
            
            print("  2. 게시글 + 댓글 + 작성자 정보 Aggregation 테스트...")
            await test.test_post_with_comments_aggregation()
            
            print("  3. Aggregation 성능 비교 테스트...")
            await test.test_aggregation_performance_comparison()
            
            print("\n🎉 모든 Aggregation 테스트 통과!")
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())