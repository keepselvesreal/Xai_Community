#!/usr/bin/env python3
"""
완전 통합 Aggregation vs 기존 Full 엔드포인트 성능 비교 테스트
MongoDB Atlas 환경에서 실제 데이터를 이용한 성능 측정

비교 대상:
1. 기존 Full 엔드포인트: GET /api/posts/{slug}/full (Aggregation + 배치 조회 혼용)
2. 완전 통합 Aggregation: GET /api/posts/{slug}/complete (단일 쿼리로 모든 데이터 조회)
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


class CompleteAggregationComparison:
    def __init__(self, base_url: str = "http://localhost:8000", iterations: int = 20):
        self.base_url = base_url
        self.iterations = iterations
        self.test_slug = "6867b9d96ec8a1b04c9c116b-정수1"  # 프론트엔드에서 확인된 실제 게시글
        self.results = {}
    
    async def delay(ms: int):
        """지연 함수"""
        await asyncio.sleep(ms / 1000)
    
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
    
    async def test_existing_full_endpoint(self, session: aiohttp.ClientSession):
        """방식 1: 기존 Full 엔드포인트 (Aggregation + 배치 조회 혼용)"""
        # URL 인코딩 처리
        import urllib.parse
        encoded_slug = urllib.parse.quote(self.test_slug, safe='')
        
        async with session.get(f"{self.base_url}/api/posts/{encoded_slug}/full") as response:
            if response.status != 200:
                raise Exception(f"기존 Full API 호출 실패: {response.status}")
            data = await response.json()
            
            # 데이터 완성도 확인
            if not data.get('data', {}).get('id'):
                raise Exception("게시글 데이터 없음")
    
    async def test_complete_aggregation_endpoint(self, session: aiohttp.ClientSession):
        """방식 2: 완전 통합 Aggregation 엔드포인트"""
        # URL 인코딩 처리
        import urllib.parse
        encoded_slug = urllib.parse.quote(self.test_slug, safe='')
        
        async with session.get(f"{self.base_url}/api/posts/{encoded_slug}/complete") as response:
            if response.status != 200:
                # 디버깅을 위해 응답 내용도 출력
                text = await response.text()
                raise Exception(f"완전 통합 API 호출 실패: {response.status}, 응답: {text[:100]}")
            data = await response.json()
            
            # 데이터 완성도 확인
            if not data.get('data', {}).get('id'):
                raise Exception("게시글 데이터 없음")
    
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
        print("📊 완전 통합 Aggregation vs 기존 Full 엔드포인트 성능 비교 결과")
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
            
            full_result = results[0]  # 기존 Full 엔드포인트를 기준으로
            complete_result = results[1]  # 완전 통합 Aggregation
            
            if full_result.avg_time > 0 and complete_result.avg_time > 0:
                improvement = ((full_result.avg_time - complete_result.avg_time) / full_result.avg_time) * 100
                print(f"완전 통합 Aggregation: {improvement:+.1f}% ({'개선' if improvement > 0 else '저하'})")
                
                print()
                print("📊 상세 비교")
                print(f"• 응답시간 차이: {abs(full_result.avg_time - complete_result.avg_time):.2f}ms")
                print(f"• 안정성 비교 (표준편차): {full_result.std_dev:.1f}ms vs {complete_result.std_dev:.1f}ms")
                print(f"• 최악의 경우: {full_result.max_time:.1f}ms vs {complete_result.max_time:.1f}ms")
            
            print()
            
            # 추천 사항
            best_result = min(results, key=lambda x: x.avg_time if x.avg_time > 0 else float('inf'))
            print("🎯 추천 사항")
            print("-"*50)
            print(f"✅ 더 빠른 방식: {best_result.method_name} ({best_result.avg_time:.2f}ms)")
            
            if "완전 통합" in best_result.method_name:
                print("   → 단일 쿼리로 모든 데이터를 한 번에 조회하는 것이 더 효율적")
                print("   → MongoDB Aggregation 파이프라인의 최적화 효과")
                print("   → 네트워크 오버헤드 최소화")
            else:
                print("   → 기존 방식의 부분 최적화와 캐싱이 여전히 효과적")
                print("   → 복잡한 Aggregation의 오버헤드가 클 수 있음")
    
    def analyze_query_complexity(self, results: List[TestResult]):
        """쿼리 복잡도 분석"""
        print("\n🔍 쿼리 복잡도 분석")
        print("-"*50)
        
        print("기존 Full 엔드포인트:")
        print("  1. 게시글 조회 (Aggregation)")
        print("  2. 댓글 목록 조회 (개별 쿼리)")
        print("  3. 댓글 작성자들 배치 조회 (다중 쿼리)")
        print("  4. 사용자 반응 조회 (캐시된)")
        print("  총 쿼리 수: 3-5개")
        
        print("\n완전 통합 Aggregation 엔드포인트:")
        print("  1. 모든 데이터 한 번에 조회 (단일 복합 Aggregation)")
        print("     - 게시글 + 작성자")
        print("     - 댓글 + 댓글 작성자")
        print("     - 사용자 반응")
        print("  총 쿼리 수: 1개")
        
        full_result = results[0] if results else None
        complete_result = results[1] if len(results) > 1 else None
        
        if full_result and complete_result:
            print(f"\n📊 효율성 지표:")
            print(f"• 쿼리 수 감소: 3-5개 → 1개 ({((4-1)/4)*100:.0f}% 감소)")
            print(f"• 네트워크 라운드트립: 3-5회 → 1회")
            print(f"• 응답시간: {full_result.avg_time:.1f}ms → {complete_result.avg_time:.1f}ms")
    
    def save_results_to_file(self, results: List[TestResult], filename: str = "complete_aggregation_results.json"):
        """결과를 JSON 파일로 저장"""
        data = {
            "test_config": {
                "base_url": self.base_url,
                "test_slug": self.test_slug,
                "iterations": self.iterations,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_type": "완전 통합 Aggregation vs 기존 Full 엔드포인트"
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
        print("🚀 완전 통합 Aggregation vs 기존 Full 엔드포인트 성능 비교 테스트 시작")
        print(f"📋 테스트 대상: {self.test_slug}")
        
        # 각 방식별 성능 테스트
        test_methods = [
            ("기존 Full 엔드포인트 (Aggregation + 배치 조회)", self.test_existing_full_endpoint),
            ("완전 통합 Aggregation 엔드포인트", self.test_complete_aggregation_endpoint),
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
            self.analyze_query_complexity(results)
            self.save_results_to_file(results)
        else:
            print("❌ 모든 테스트가 실패했습니다.")


async def main():
    """메인 실행 함수"""
    # 설정 조정 가능
    tester = CompleteAggregationComparison(
        base_url="http://localhost:8000",
        iterations=20  # 더 정확한 측정을 위해 20회 반복
    )
    
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())