#!/usr/bin/env python3
"""
게시판 상세 페이지 성능 비교 테스트
MongoDB Atlas 환경에서 실제 데이터를 이용한 성능 측정

비교 대상:
1. 기존 방식: 개별 API 호출 (GET /api/posts/{slug} + GET /api/posts/{slug}/comments)
2. Full 엔드포인트: GET /api/posts/{slug}/full (Aggregation)
3. Aggregated 엔드포인트: GET /api/posts/{slug}/aggregated (게시글 + 작성자만)
"""

import asyncio
import aiohttp
import time
import statistics
import json
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TestResult:
    method_name: str
    times: List[float]
    avg_time: float
    median_time: float
    min_time: float
    max_time: float
    std_dev: float
    success_rate: float


class PerformanceComparison:
    def __init__(self, base_url: str = "http://localhost:8000", iterations: int = 10):
        self.base_url = base_url
        self.iterations = iterations
        self.test_slug = None
        self.results = {}
    
    async def setup_test_data(self):
        """테스트용 게시글 준비"""
        async with aiohttp.ClientSession() as session:
            try:
                # 기존 게시글 목록 조회
                async with session.get(f"{self.base_url}/api/posts?page=1&page_size=1") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('items'):
                            self.test_slug = data['items'][0]['slug']
                            print(f"✅ 테스트 대상 게시글: {self.test_slug}")
                            return True
                
                print("⚠️ 기존 게시글이 없어서 테스트 데이터를 생성합니다...")
                
                # 테스트 게시글 생성 (인증 토큰 필요할 수 있음)
                test_post = {
                    "title": "성능 테스트용 게시글",
                    "content": "이 게시글은 성능 비교 테스트를 위해 생성되었습니다. " * 100,  # 긴 내용
                    "service": "board",
                    "metadata": {
                        "type": "board",
                        "category": "테스트",
                        "tags": ["성능테스트", "벤치마크"]
                    }
                }
                
                return False
                
            except Exception as e:
                print(f"❌ 테스트 데이터 준비 실패: {e}")
                # 실제 존재하는 게시글 slug 사용
                self.test_slug = "25-07-08-glsseugi"
                print(f"🔧 실제 게시글 slug 사용: {self.test_slug}")
                return True
    
    async def measure_time(self, session: aiohttp.ClientSession, method_func) -> float:
        """API 호출 시간 측정"""
        start_time = time.perf_counter()
        try:
            await method_func(session)
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000  # 밀리초 변환
        except Exception as e:
            print(f"⚠️ API 호출 실패: {e}")
            return float('inf')  # 실패한 경우 무한대 반환
    
    async def test_separate_apis(self, session: aiohttp.ClientSession):
        """방식 1: 개별 API 호출"""
        # 병렬로 게시글과 댓글 조회
        post_task = session.get(f"{self.base_url}/api/posts/{self.test_slug}")
        comments_task = session.get(f"{self.base_url}/api/posts/{self.test_slug}/comments")
        
        post_response, comments_response = await asyncio.gather(post_task, comments_task)
        
        if post_response.status != 200 or comments_response.status != 200:
            raise Exception(f"API 호출 실패: {post_response.status}, {comments_response.status}")
        
        # 응답 데이터 읽기
        await post_response.json()
        await comments_response.json()
    
    async def test_full_endpoint(self, session: aiohttp.ClientSession):
        """방식 2: Full Aggregation 엔드포인트"""
        async with session.get(f"{self.base_url}/api/posts/{self.test_slug}/full") as response:
            if response.status != 200:
                raise Exception(f"Full API 호출 실패: {response.status}")
            await response.json()
    
    async def test_aggregated_endpoint(self, session: aiohttp.ClientSession):
        """방식 3: Aggregated 엔드포인트 (게시글 + 작성자만)"""
        async with session.get(f"{self.base_url}/api/posts/{self.test_slug}/aggregated") as response:
            if response.status != 200:
                raise Exception(f"Aggregated API 호출 실패: {response.status}")
            await response.json()
    
    async def run_performance_test(self, method_name: str, method_func) -> TestResult:
        """특정 방식의 성능 테스트 실행"""
        print(f"\n🔄 {method_name} 테스트 시작...")
        
        times = []
        success_count = 0
        
        async with aiohttp.ClientSession() as session:
            for i in range(self.iterations):
                try:
                    elapsed_time = await self.measure_time(session, method_func)
                    if elapsed_time != float('inf'):
                        times.append(elapsed_time)
                        success_count += 1
                        print(f"  테스트 {i+1}: {elapsed_time:.2f}ms")
                    else:
                        print(f"  테스트 {i+1}: 실패")
                except Exception as e:
                    print(f"  테스트 {i+1}: 오류 - {e}")
                
                # 서버 부하 방지를 위한 간격
                await asyncio.sleep(0.1)
        
        if not times:
            print(f"❌ {method_name}: 모든 테스트 실패")
            return TestResult(
                method_name=method_name,
                times=[],
                avg_time=0,
                median_time=0,
                min_time=0,
                max_time=0,
                std_dev=0,
                success_rate=0
            )
        
        return TestResult(
            method_name=method_name,
            times=times,
            avg_time=statistics.mean(times),
            median_time=statistics.median(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0,
            success_rate=(success_count / self.iterations) * 100
        )
    
    def print_results(self, results: List[TestResult]):
        """결과 출력"""
        print("\n" + "="*80)
        print("📊 게시판 상세 페이지 성능 비교 결과")
        print("="*80)
        
        print(f"🔧 테스트 환경: {self.base_url}")
        print(f"📋 테스트 게시글: {self.test_slug}")
        print(f"🔄 반복 횟수: {self.iterations}")
        print()
        
        for result in results:
            print(f"🔹 {result.method_name}")
            print(f"   평균: {result.avg_time:.2f}ms")
            print(f"   중간값: {result.median_time:.2f}ms")
            print(f"   최소: {result.min_time:.2f}ms")
            print(f"   최대: {result.max_time:.2f}ms")
            print(f"   표준편차: {result.std_dev:.2f}ms")
            print(f"   성공률: {result.success_rate:.1f}%")
            print()
        
        # 성능 비교
        if len(results) >= 2:
            print("📈 성능 비교 분석")
            print("-"*50)
            
            baseline = results[0]  # 개별 API 호출을 기준으로
            
            for i, result in enumerate(results[1:], 1):
                if baseline.avg_time > 0 and result.avg_time > 0:
                    improvement = ((baseline.avg_time - result.avg_time) / baseline.avg_time) * 100
                    print(f"{result.method_name}: {improvement:+.1f}% ({'개선' if improvement > 0 else '저하'})")
            
            print()
            
            # 추천 사항
            best_result = min(results, key=lambda x: x.avg_time if x.avg_time > 0 else float('inf'))
            print("🎯 추천 사항")
            print("-"*50)
            print(f"✅ 가장 빠른 방식: {best_result.method_name} ({best_result.avg_time:.2f}ms)")
            
            if "Full" in best_result.method_name:
                print("   → 게시글과 댓글을 모두 표시하는 상세 페이지에 적합")
            elif "Aggregated" in best_result.method_name:
                print("   → 게시글 내용 우선 표시 후 댓글 지연 로딩 방식에 적합")
            else:
                print("   → 기존 방식의 네트워크 병렬성이 여전히 효과적")
    
    def save_results_to_file(self, results: List[TestResult], filename: str = "performance_results.json"):
        """결과를 JSON 파일로 저장"""
        data = {
            "test_config": {
                "base_url": self.base_url,
                "test_slug": self.test_slug,
                "iterations": self.iterations,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "results": [
                {
                    "method_name": r.method_name,
                    "avg_time": r.avg_time,
                    "median_time": r.median_time,
                    "min_time": r.min_time,
                    "max_time": r.max_time,
                    "std_dev": r.std_dev,
                    "success_rate": r.success_rate,
                    "raw_times": r.times
                }
                for r in results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 결과 저장됨: {filename}")
    
    async def run_all_tests(self):
        """전체 테스트 실행"""
        print("🚀 게시판 상세 페이지 성능 비교 테스트 시작")
        
        # 테스트 데이터 준비
        await self.setup_test_data()
        
        if not self.test_slug:
            print("❌ 테스트할 게시글이 없습니다. 먼저 게시글을 생성해주세요.")
            return
        
        # 각 방식별 성능 테스트
        test_methods = [
            ("개별 API 호출 (기존 방식)", self.test_separate_apis),
            ("Full Aggregation 엔드포인트", self.test_full_endpoint),
            ("Aggregated 엔드포인트 (게시글+작성자)", self.test_aggregated_endpoint),
        ]
        
        results = []
        for method_name, method_func in test_methods:
            try:
                result = await self.run_performance_test(method_name, method_func)
                results.append(result)
            except Exception as e:
                print(f"❌ {method_name} 테스트 실패: {e}")
        
        # 결과 출력 및 저장
        if results:
            self.print_results(results)
            self.save_results_to_file(results)
        else:
            print("❌ 모든 테스트가 실패했습니다.")


async def main():
    """메인 실행 함수"""
    # 설정 조정 가능
    tester = PerformanceComparison(
        base_url="http://localhost:8000",
        iterations=15  # 더 정확한 측정을 위해 15회 반복
    )
    
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())