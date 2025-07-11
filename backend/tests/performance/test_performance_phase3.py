"""
3단계 성능 테스트: Aggregation vs 기존 방식 비교
"""

import asyncio
import time
from typing import Dict, Any
import httpx


class PerformanceTestPhase3:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def measure_endpoint_response_time(self, endpoint: str, iterations: int = 5) -> Dict[str, Any]:
        """엔드포인트 응답 시간 측정"""
        times = []
        
        async with httpx.AsyncClient() as client:
            for i in range(iterations):
                start_time = time.time()
                
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_time = (end_time - start_time) * 1000
                        times.append(response_time)
                        print(f"  테스트 {i+1}/{iterations}: {response_time:.2f}ms")
                    else:
                        print(f"  테스트 {i+1}/{iterations}: 실패 (HTTP {response.status_code})")
                        
                except Exception as e:
                    print(f"  테스트 {i+1}/{iterations}: 오류 - {e}")
                    
                await asyncio.sleep(0.1)
        
        if times:
            return {
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "successful_tests": len(times),
                "total_tests": iterations
            }
        else:
            return {
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0,
                "successful_tests": 0,
                "total_tests": iterations
            }
    
    async def compare_approaches(self, post_slug: str) -> Dict[str, Any]:
        """기존 방식 vs Aggregation 방식 성능 비교"""
        
        print("🚀 3단계 성능 비교 테스트 시작...")
        
        # 1. 기존 방식 (개별 API 호출)
        print(f"\n📊 기존 방식 테스트:")
        print(f"   - 게시글 조회: /api/posts/{post_slug}")
        print(f"   - 댓글 조회: /api/posts/{post_slug}/comments")
        
        existing_post_result = await self.measure_endpoint_response_time(f"/api/posts/{post_slug}")
        existing_comments_result = await self.measure_endpoint_response_time(f"/api/posts/{post_slug}/comments")
        
        existing_total_time = existing_post_result["avg_time"] + existing_comments_result["avg_time"]
        
        print(f"\n   결과:")
        print(f"   - 게시글 조회: {existing_post_result['avg_time']:.2f}ms")
        print(f"   - 댓글 조회: {existing_comments_result['avg_time']:.2f}ms")
        print(f"   - 총 시간: {existing_total_time:.2f}ms")
        
        # 2. Aggregation 방식
        print(f"\n📊 Aggregation 방식 테스트:")
        print(f"   - 통합 조회: /api/posts/{post_slug}/full")
        
        aggregation_result = await self.measure_endpoint_response_time(f"/api/posts/{post_slug}/full")
        
        print(f"\n   결과:")
        print(f"   - 통합 조회: {aggregation_result['avg_time']:.2f}ms")
        
        # 3. 성능 비교
        if aggregation_result["successful_tests"] > 0 and existing_total_time > 0:
            improvement = ((existing_total_time - aggregation_result["avg_time"]) / existing_total_time) * 100
            
            print(f"\n🎯 성능 비교 결과:")
            print(f"   기존 방식: {existing_total_time:.2f}ms")
            print(f"   Aggregation: {aggregation_result['avg_time']:.2f}ms")
            print(f"   성능 개선: {improvement:.1f}%")
            
            return {
                "existing_total_time": existing_total_time,
                "aggregation_time": aggregation_result["avg_time"],
                "improvement_percentage": improvement,
                "aggregation_successful": True
            }
        else:
            print(f"\n❌ Aggregation 방식 실패 - 기존 방식만 측정됨")
            return {
                "existing_total_time": existing_total_time,
                "aggregation_time": 0,
                "improvement_percentage": 0,
                "aggregation_successful": False
            }


if __name__ == "__main__":
    async def main():
        tester = PerformanceTestPhase3()
        
        # 댓글이 있는 게시글로 테스트
        test_slug = "6867ba276ec8a1b04c9c1171-하이마트-철산점"
        
        result = await tester.compare_approaches(test_slug)
        
        # 결과 저장
        import json
        with open("/home/nadle/projects/Xai_Community/v5/records/25-07-08/phase3_comparison.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 결과가 records/25-07-08/phase3_comparison.json에 저장되었습니다")
    
    asyncio.run(main())