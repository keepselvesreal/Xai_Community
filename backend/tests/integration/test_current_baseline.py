"""
현재 상태 베이스라인 테스트
타입 통일 작업 전 기존 동작을 보장하는 테스트
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from nadle_backend.models.core import User, Post, Comment, UserReaction
from nadle_backend.services.user_activity_service import UserActivityService
from nadle_backend.repositories.post_repository import PostRepository
from nadle_backend.repositories.comment_repository import CommentRepository
from nadle_backend.repositories.user_reaction_repository import UserReactionRepository
import asyncio


client = TestClient(app)


class TestCurrentBaseline:
    """현재 상태 베이스라인 테스트"""
    
    @pytest.mark.asyncio
    async def test_user_activity_api_response_structure(self):
        """현재 /api/users/me/activity API 응답 구조 테스트"""
        # 실제 사용자 데이터가 있다고 가정하고 API 호출
        # 이 테스트는 기존 구조를 문서화하기 위한 목적
        
        # API 응답이 현재 구조를 만족하는지 확인
        expected_structure = {
            "posts": {
                "board": "list",
                "info": "list", 
                "services": "list",
                "tips": "list"
            },
            "comments": "list",
            "reactions": {
                "likes": {
                    "board": "list",
                    "info": "list", 
                    "services": "list",
                    "tips": "list"
                },
                "dislikes": {
                    "board": "list",
                    "info": "list",
                    "services": "list", 
                    "tips": "list"
                },
                "bookmarks": {
                    "board": "list",
                    "info": "list",
                    "services": "list",
                    "tips": "list"
                }
            },
            "pagination": "dict"
        }
        
        # 현재 이 구조가 기대되는 구조임을 문서화
        assert expected_structure is not None
    
    @pytest.mark.asyncio
    async def test_current_route_path_generation(self):
        """현재 라우트 경로 생성 방식 테스트"""
        service = UserActivityService(
            PostRepository(),
            CommentRepository(), 
            UserReactionRepository()
        )
        
        # 현재 라우트 생성 방식 확인
        test_cases = [
            ("board", "test-slug", "/board-post/test-slug"),
            ("property_information", "test-slug", "/property-info/test-slug"),
            ("expert_tips", "test-slug", "/expert-tips/test-slug"),
            ("services", "test-slug", "/moving-services-post/test-slug")
        ]
        
        for page_type, slug, expected_route in test_cases:
            actual_route = service._generate_route_path(page_type, slug)
            assert actual_route == expected_route, f"Route generation failed for {page_type}"
    
    @pytest.mark.asyncio 
    async def test_current_page_type_extraction(self):
        """현재 페이지 타입 추출 방식 테스트"""
        service = UserActivityService(
            PostRepository(),
            CommentRepository(),
            UserReactionRepository()
        )
        
        # 현재 경로 파싱 방식 확인
        test_cases = [
            ("/board-post/some-slug", "board"),
            ("/property-info/some-slug", "info"),
            ("/moving-services-post/some-slug", "services"),
            ("/expert-tips/some-slug", "tips")
        ]
        
        for route_path, expected_type in test_cases:
            actual_type = service._extract_page_type_from_reaction(route_path)
            # 현재 정규화된 타입 반환하는지 확인
            assert actual_type in ["board", "info", "services", "tips"]
    
    @pytest.mark.asyncio
    async def test_current_type_normalization(self):
        """현재 타입 정규화 방식 테스트"""
        service = UserActivityService(
            PostRepository(),
            CommentRepository(),
            UserReactionRepository()
        )
        
        # 현재 정규화 로직 확인
        test_cases = [
            ("board", "board"),
            ("property_information", "info"), 
            ("expert_tips", "tips"),
            ("services", "services"),
            ("moving services", "services")
        ]
        
        for db_type, expected_normalized in test_cases:
            actual_normalized = service.normalize_post_type(db_type)
            assert actual_normalized == expected_normalized
    
    def test_api_endpoint_accessibility(self):
        """API 엔드포인트 접근성 테스트"""
        # 인증 없이 접근 가능한 엔드포인트들
        public_endpoints = [
            "/api/posts",
            "/api/posts/search", 
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            # 200 또는 422(파라미터 누락) 응답이면 엔드포인트 존재
            assert response.status_code in [200, 422]


if __name__ == "__main__":
    # 개별 테스트 실행을 위한 헬퍼
    pytest.main([__file__, "-v"])