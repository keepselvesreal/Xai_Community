"""
읽기 전용 부하 테스트 시나리오 - XAI Community API
인증 없이 조회 기능만 테스트
"""

import random
from locust import HttpUser, task, between


class ReadOnlyUser(HttpUser):
    """읽기 전용 사용자 (로그인 없이 조회만)"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """테스트 시작 시 초기화"""
        self.test_posts = []
    
    @task(5)
    def view_posts_list(self):
        """게시글 목록 조회"""
        params = {
            "page": random.randint(1, 5),
            "page_size": 20
        }
        
        with self.client.get("/api/posts", params=params, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "items" in data and data["items"]:
                        # 실제 응답 구조에 맞게 수정
                        if isinstance(data["items"], list) and len(data["items"]) > 0:
                            item = data["items"][0]
                            # 응답 구조 확인을 위한 로깅
                            print(f"📊 게시글 아이템 구조: {list(item.keys()) if isinstance(item, dict) else type(item)}")
                            
                            # id 필드가 있는지 확인
                            if isinstance(item, dict):
                                if "_id" in item:
                                    self.test_posts = [post["_id"] for post in data["items"][:3]]
                                elif "id" in item:
                                    self.test_posts = [post["id"] for post in data["items"][:3]]
                                elif "slug" in item:
                                    self.test_posts = [post["slug"] for post in data["items"][:3]]
                    response.success()
                except Exception as e:
                    print(f"❌ 응답 파싱 오류: {e}")
                    response.failure(f"응답 파싱 실패: {e}")
            else:
                response.failure(f"게시글 목록 조회 실패: {response.status_code}")
    
    @task(3)
    def view_post_detail(self):
        """게시글 상세 조회"""
        if not self.test_posts:
            self.view_posts_list()
            return
        
        post_id = random.choice(self.test_posts)
        with self.client.get(f"/api/posts/{post_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 게시글이 없으면 목록 새로 가져오기
                self.test_posts = []
                response.success()  # 404는 정상적인 상황으로 처리
            else:
                response.failure(f"게시글 상세 조회 실패: {response.status_code}")
    
    @task(2)
    def search_posts(self):
        """게시글 검색"""
        search_queries = ["부동산", "AI", "서비스", "정보", "팁", "이사"]
        query = random.choice(search_queries)
        
        params = {
            "q": query,
            "page": 1,
            "page_size": 10
        }
        
        with self.client.get("/api/posts/search", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"게시글 검색 실패: {response.status_code}")
    
    @task(2)
    def view_comments(self):
        """댓글 조회"""
        if not self.test_posts:
            return
        
        post_id = random.choice(self.test_posts)
        params = {
            "page": 1,
            "page_size": 10
        }
        
        with self.client.get(f"/api/comments/{post_id}/comments", 
                           params=params,
                           catch_response=True) as response:
            if response.status_code in [200, 404]:  # 댓글이 없을 수도 있음
                response.success()
            else:
                response.failure(f"댓글 조회 실패: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """헬스 체크"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"헬스 체크 실패: {response.status_code}")
    
    @task(1)
    def api_docs_check(self):
        """API 문서 접근 체크"""
        with self.client.get("/docs", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API 문서 접근 실패: {response.status_code}")


# 기본 실행을 위한 간단한 사용자 클래스
class SimpleLoadUser(HttpUser):
    """간단한 부하 테스트용 사용자"""
    
    wait_time = between(1, 2)
    
    @task(3)
    def basic_health_check(self):
        """기본 헬스 체크"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"헬스 체크 실패: {response.status_code}")
    
    @task(2)
    def basic_posts_list(self):
        """기본 게시글 목록"""
        params = {"page": 1, "page_size": 10}
        with self.client.get("/api/posts", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"게시글 목록 실패: {response.status_code}")
    
    @task(1)
    def basic_search(self):
        """기본 검색"""
        params = {"q": "테스트", "page": 1, "page_size": 5}
        with self.client.get("/api/posts/search", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"검색 실패: {response.status_code}")