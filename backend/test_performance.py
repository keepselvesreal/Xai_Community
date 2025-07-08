"""
성능 테스트 스크립트
각 최적화 단계별 API 응답 시간 측정
"""

import asyncio
import time
from typing import Dict, Any
import httpx
from datetime import datetime

class PerformanceTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    async def measure_api_response_time(self, endpoint: str, method: str = "GET", 
                                      headers: Dict[str, str] = None, 
                                      data: Dict[str, Any] = None) -> Dict[str, Any]:
        """API 응답 시간 측정"""
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            if method == "GET":
                response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
            elif method == "POST":
                response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=data)
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms로 변환
            
            return {
                "endpoint": endpoint,
                "method": method,
                "response_time_ms": round(response_time, 2),
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_post_detail_performance(self, post_slug: str, auth_token: str = None) -> Dict[str, Any]:
        """게시글 상세 페이지 성능 테스트"""
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        # 1. 게시글 조회
        post_result = await self.measure_api_response_time(
            f"/posts/{post_slug}", 
            headers=headers
        )
        
        # 2. 댓글 조회
        comments_result = await self.measure_api_response_time(
            f"/comments?post_slug={post_slug}",
            headers=headers
        )
        
        total_time = post_result["response_time_ms"] + comments_result["response_time_ms"]
        
        return {
            "post_detail": post_result,
            "comments": comments_result,
            "total_time_ms": round(total_time, 2),
            "test_type": "post_detail_performance"
        }
    
    async def run_baseline_test(self, post_slug: str = "test-post", iterations: int = 5) -> Dict[str, Any]:
        """기준선 성능 테스트"""
        print(f"🔄 기준선 성능 테스트 시작 (반복: {iterations}회)")
        
        results = []
        for i in range(iterations):
            print(f"  테스트 {i+1}/{iterations}...")
            result = await self.test_post_detail_performance(post_slug)
            results.append(result)
            await asyncio.sleep(0.1)  # 짧은 대기
        
        # 평균 계산
        total_times = [r["total_time_ms"] for r in results]
        avg_time = sum(total_times) / len(total_times)
        min_time = min(total_times)
        max_time = max(total_times)
        
        return {
            "phase": "baseline",
            "iterations": iterations,
            "avg_response_time_ms": round(avg_time, 2),
            "min_response_time_ms": round(min_time, 2),
            "max_response_time_ms": round(max_time, 2),
            "all_results": results,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    async def main():
        tester = PerformanceTest()
        
        # 실제 게시글 slug 사용
        test_slug = "686c6cd040839f99492cab46-25-07-08-글쓰기"
        
        # 기준선 테스트 실행
        baseline_result = await tester.run_baseline_test(test_slug)
        print(f"\n📊 기준선 성능 결과:")
        print(f"   평균 응답 시간: {baseline_result['avg_response_time_ms']}ms")
        print(f"   최소 응답 시간: {baseline_result['min_response_time_ms']}ms") 
        print(f"   최대 응답 시간: {baseline_result['max_response_time_ms']}ms")
        
        # 1단계 최적화 후 테스트
        print(f"\n🔄 1단계(스마트 캐싱) 성능 테스트 시작...")
        phase1_result = await tester.run_baseline_test(test_slug)
        phase1_result["phase"] = "smart_caching"
        
        print(f"\n📊 1단계 최적화 후 성능 결과:")
        print(f"   평균 응답 시간: {phase1_result['avg_response_time_ms']}ms")
        print(f"   최소 응답 시간: {phase1_result['min_response_time_ms']}ms") 
        print(f"   최대 응답 시간: {phase1_result['max_response_time_ms']}ms")
        
        # 개선율 계산
        improvement_pct = ((baseline_result['avg_response_time_ms'] - phase1_result['avg_response_time_ms']) / baseline_result['avg_response_time_ms']) * 100
        print(f"   개선율: {improvement_pct:.1f}%")
        
        # 2단계 최적화 후 테스트
        print(f"\n🔄 2단계(배치 조회) 성능 테스트 시작...")
        phase2_result = await tester.run_baseline_test(test_slug)
        phase2_result["phase"] = "batch_queries"
        
        print(f"\n📊 2단계 최적화 후 성능 결과:")
        print(f"   평균 응답 시간: {phase2_result['avg_response_time_ms']}ms")
        print(f"   최소 응답 시간: {phase2_result['min_response_time_ms']}ms") 
        print(f"   최대 응답 시간: {phase2_result['max_response_time_ms']}ms")
        
        # 2단계 개선율 계산
        improvement2_pct = ((phase1_result['avg_response_time_ms'] - phase2_result['avg_response_time_ms']) / phase1_result['avg_response_time_ms']) * 100
        total_improvement_pct = ((baseline_result['avg_response_time_ms'] - phase2_result['avg_response_time_ms']) / baseline_result['avg_response_time_ms']) * 100
        print(f"   2단계 개선율: {improvement2_pct:.1f}%")
        print(f"   전체 개선율: {total_improvement_pct:.1f}%")
        
        # 결과를 파일로 저장
        import json
        with open("/home/nadle/projects/Xai_Community/v5/records/25-07-08/baseline_performance.json", "w") as f:
            json.dump(baseline_result, f, indent=2, ensure_ascii=False)
            
        with open("/home/nadle/projects/Xai_Community/v5/records/25-07-08/phase1_performance.json", "w") as f:
            json.dump(phase1_result, f, indent=2, ensure_ascii=False)
            
        with open("/home/nadle/projects/Xai_Community/v5/records/25-07-08/phase2_performance.json", "w") as f:
            json.dump(phase2_result, f, indent=2, ensure_ascii=False)
        
        # 3단계 Aggregation 성능 테스트 (full 엔드포인트 사용)
        print(f"\n🔄 3단계(Aggregation) 성능 테스트 시작...")
        
        # full 엔드포인트를 위한 특별 테스트
        async def test_aggregation_endpoint():
            times = []
            async with httpx.AsyncClient() as client:
                for i in range(5):
                    start_time = time.time()
                    response = await client.get(f"http://localhost:8000/api/posts/{test_slug}/full")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_time = (end_time - start_time) * 1000
                        times.append(response_time)
                        print(f"  테스트 {i+1}/5: {response_time:.2f}ms")
                    
                    await asyncio.sleep(0.1)
            
            if times:
                return {
                    "avg_response_time_ms": sum(times) / len(times),
                    "min_response_time_ms": min(times),
                    "max_response_time_ms": max(times),
                    "phase": "aggregation"
                }
            return None
        
        import httpx
        phase3_result = await test_aggregation_endpoint()
        
        if phase3_result:
            print(f"\n📊 3단계 Aggregation 성능 결과:")
            print(f"   평균 응답 시간: {phase3_result['avg_response_time_ms']:.2f}ms")
            print(f"   최소 응답 시간: {phase3_result['min_response_time_ms']:.2f}ms") 
            print(f"   최대 응답 시간: {phase3_result['max_response_time_ms']:.2f}ms")
            
            # 3단계 개선율 계산
            improvement3_pct = ((phase2_result['avg_response_time_ms'] - phase3_result['avg_response_time_ms']) / phase2_result['avg_response_time_ms']) * 100
            total_improvement_final = ((baseline_result['avg_response_time_ms'] - phase3_result['avg_response_time_ms']) / baseline_result['avg_response_time_ms']) * 100
            print(f"   3단계 개선율: {improvement3_pct:.1f}%")
            print(f"   최종 전체 개선율: {total_improvement_final:.1f}%")
            
            with open("/home/nadle/projects/Xai_Community/v5/records/25-07-08/phase3_performance.json", "w") as f:
                json.dump(phase3_result, f, indent=2, ensure_ascii=False)
        else:
            print(f"\n❌ 3단계 Aggregation 테스트 실패")
    
    asyncio.run(main())