"""
2단계: 배치 조회 테스트
댓글 목록 조회 시 작성자 정보 배치 처리 테스트
"""

import asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock


class TestBatchQueries:
    """배치 조회 기능 테스트"""
    
    async def test_batch_author_lookup(self):
        """작성자 정보 배치 조회 테스트"""
        from nadle_backend.services.posts_service import PostsService
        
        posts_service = PostsService()
        
        # Given: 여러 작성자 ID 목록
        author_ids = [
            "6867b9246ec8a1b04c9c1165",
            "6867b9cb6ec8a1b04c9c116a", 
            "6867640707ebf8a214bc5c23"
        ]
        
        # When: 배치로 작성자 정보 조회
        authors_info = await posts_service.get_authors_info_batch(author_ids)
        
        # Then: 모든 작성자 정보가 반환되어야 함
        assert isinstance(authors_info, dict)
        assert len(authors_info) <= len(author_ids)  # 존재하지 않는 사용자는 제외될 수 있음
        
        for author_id, author_info in authors_info.items():
            assert "user_handle" in author_info
            assert "display_name" in author_info
            
        print(f"✅ 배치 조회로 {len(authors_info)}명의 작성자 정보 조회 완료")
    
    async def test_batch_user_reactions_lookup(self):
        """사용자 반응 배치 조회 테스트"""
        from nadle_backend.services.posts_service import PostsService
        
        posts_service = PostsService()
        
        # Given: 사용자 ID와 여러 게시글 ID 목록
        user_id = "6867b9246ec8a1b04c9c1165"
        post_ids = [
            "686c6cd040839f99492cab46",
            "6867c90d6ec8a1b04c9c1185",
            "6867c8cf6ec8a1b04c9c1183"
        ]
        
        # When: 배치로 사용자 반응 조회
        reactions = await posts_service.get_user_reactions_batch(user_id, post_ids)
        
        # Then: 모든 게시글에 대한 반응 정보가 반환되어야 함
        assert isinstance(reactions, dict)
        assert len(reactions) == len(post_ids)
        
        for post_id, reaction in reactions.items():
            assert "liked" in reaction
            assert "disliked" in reaction 
            assert "bookmarked" in reaction
            
        print(f"✅ 배치 조회로 {len(reactions)}개 게시글의 사용자 반응 조회 완료")
    
    async def test_comments_with_batch_authors(self):
        """댓글 조회 시 작성자 정보 배치 처리 테스트"""
        from nadle_backend.services.posts_service import PostsService
        
        posts_service = PostsService()
        
        # Given: 게시글 slug
        post_slug = "6867ba276ec8a1b04c9c1171-하이마트-철산점"
        
        # When: 댓글 목록을 배치 조회로 조회
        comments_with_authors = await posts_service.get_comments_with_batch_authors(post_slug)
        
        # Then: 댓글과 작성자 정보가 함께 반환되어야 함
        assert isinstance(comments_with_authors, list)
        
        for comment in comments_with_authors:
            if comment.get("author"):  # 작성자 정보가 있는 경우
                assert "user_handle" in comment["author"]
                assert "display_name" in comment["author"]
                
        print(f"✅ 배치 조회로 {len(comments_with_authors)}개 댓글의 작성자 정보 처리 완료")


if __name__ == "__main__":
    async def run_tests():
        test = TestBatchQueries()
        
        print("🧪 배치 조회 테스트 시작...")
        
        try:
            print("  1. 작성자 정보 배치 조회 테스트...")
            await test.test_batch_author_lookup()
            
            print("  2. 사용자 반응 배치 조회 테스트...")
            await test.test_batch_user_reactions_lookup()
            
            print("  3. 댓글 배치 조회 테스트...")
            await test.test_comments_with_batch_authors()
            
            print("\n🎉 모든 배치 조회 테스트 통과!")
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(run_tests())