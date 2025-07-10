"""
기본 부하 테스트 시나리오 - XAI Community API
파일 업로드 제외한 핵심 기능 테스트
"""

import json
import random
from locust import HttpUser, task, between
from locust.exception import RescheduleTask


class XAICommunityUser(HttpUser):
    """XAI Community 사용자 행동 시뮬레이션"""
    
    # 사용자 행동 간격 (1~3초)
    wait_time = between(1, 3)
    
    # 기본 설정
    BASE_URL = "http://localhost:8000"
    
    def on_start(self):
        """테스트 시작 시 초기화"""
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.test_posts = []
        
        # 테스트용 사용자 데이터
        self.test_user = {
            "email": f"test_{random.randint(1000, 9999)}@example.com",
            "password": "testpassword123",
            "handle": f"testuser_{random.randint(1000, 9999)}",
            "display_name": f"Test User {random.randint(1000, 9999)}"
        }
        
        # 로그인 시도
        self.login_user()
    
    def login_user(self):
        """사용자 로그인"""
        # 먼저 회원가입 시도
        with self.client.post("/api/auth/register", json=self.test_user, catch_response=True) as response:
            if response.status_code == 201:
                print(f"✅ 회원가입 성공: {self.test_user['email']}")
            elif response.status_code == 400:
                print(f"ℹ️  기존 사용자 사용: {self.test_user['email']}")
            else:
                print(f"❌ 회원가입 실패: {response.status_code}")
        
        # 로그인
        login_data = {
            "username": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        with self.client.post("/api/auth/login", data=login_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.user_id = data["user"]["id"]
                print(f"✅ 로그인 성공: {self.test_user['email']}")
            else:
                print(f"❌ 로그인 실패: {response.status_code}")
                raise RescheduleTask()
    
    def get_auth_headers(self):
        """인증 헤더 반환"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(3)
    def view_posts_list(self):
        """게시글 목록 조회 (가장 빈번한 액션)"""
        params = {
            "page": random.randint(1, 3),
            "page_size": 20,
            "sort_by": random.choice(["created_at", "likes", "views"])
        }
        
        with self.client.get("/api/posts", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                # 테스트용 게시글 ID 수집
                if "items" in data and data["items"]:
                    self.test_posts = [post["id"] for post in data["items"][:5]]
                response.success()
            else:
                response.failure(f"게시글 목록 조회 실패: {response.status_code}")
    
    @task(2)
    def view_post_detail(self):
        """게시글 상세 조회"""
        if not self.test_posts:
            # 게시글이 없으면 목록 조회 먼저
            self.view_posts_list()
            return
        
        post_id = random.choice(self.test_posts)
        with self.client.get(f"/api/posts/{post_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"게시글 상세 조회 실패: {response.status_code}")
    
    @task(1)
    def search_posts(self):
        """게시글 검색"""
        search_queries = ["부동산", "AI", "서비스", "정보", "팁"]
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
    
    @task(1)
    def create_post(self):
        """게시글 작성"""
        if not self.access_token:
            return
        
        post_data = {
            "title": f"테스트 게시글 {random.randint(1000, 9999)}",
            "content": f"테스트 내용입니다. {random.randint(1000, 9999)}",
            "category": random.choice(["일반", "질문", "정보", "팁"]),
            "tags": [f"tag{i}" for i in range(random.randint(1, 3))],
            "metadata": {
                "type": "general",
                "service_type": "community"
            }
        }
        
        with self.client.post("/api/posts", 
                            json=post_data, 
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 201:
                data = response.json()
                self.test_posts.append(data["id"])
                response.success()
            else:
                response.failure(f"게시글 작성 실패: {response.status_code}")
    
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
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"댓글 조회 실패: {response.status_code}")
    
    @task(1)
    def create_comment(self):
        """댓글 작성"""
        if not self.access_token or not self.test_posts:
            return
        
        post_id = random.choice(self.test_posts)
        comment_data = {
            "content": f"테스트 댓글입니다. {random.randint(1000, 9999)}",
            "parent_id": None
        }
        
        with self.client.post(f"/api/comments/{post_id}/comments",
                            json=comment_data,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"댓글 작성 실패: {response.status_code}")
    
    @task(1)
    def like_post(self):
        """게시글 좋아요"""
        if not self.access_token or not self.test_posts:
            return
        
        post_id = random.choice(self.test_posts)
        
        with self.client.post(f"/api/posts/{post_id}/like",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"게시글 좋아요 실패: {response.status_code}")
    
    @task(1)
    def bookmark_post(self):
        """게시글 북마크"""
        if not self.access_token or not self.test_posts:
            return
        
        post_id = random.choice(self.test_posts)
        
        with self.client.post(f"/api/posts/{post_id}/bookmark",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"게시글 북마크 실패: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """헬스 체크"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"헬스 체크 실패: {response.status_code}")


class ReadOnlyUser(HttpUser):
    """읽기 전용 사용자 (로그인 없이 조회만)"""
    
    wait_time = between(1, 2)
    weight = 3  # 읽기 전용 사용자가 더 많음
    
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
                data = response.json()
                if "items" in data and data["items"]:
                    self.test_posts = [post["id"] for post in data["items"][:3]]
                response.success()
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
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"댓글 조회 실패: {response.status_code}")