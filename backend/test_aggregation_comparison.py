"""
정확한 Aggregation 성능 비교 테스트
같은 조건 (게시글 + 작성자 정보)에서 기존 방식 vs Aggregation 비교
"""

import asyncio
import time
import httpx


async def test_performance_comparison():
    test_slug = "686c6cd040839f99492cab46-25-07-08-글쓰기"
    
    print("🚀 Aggregation 정확한 성능 비교 테스트")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # 1. 기존 방식 테스트 (게시글만)
        print("📊 기존 방식 (게시글 + 작성자 정보):")
        existing_times = []
        
        for i in range(5):
            start_time = time.time()
            response = await client.get(f"http://localhost:8000/api/posts/{test_slug}")
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000
                existing_times.append(response_time)
                print(f"  테스트 {i+1}/5: {response_time:.2f}ms")
            
            await asyncio.sleep(0.1)
        
        existing_avg = sum(existing_times) / len(existing_times)
        
        # 2. Aggregation 방식 테스트 (게시글 + 작성자)
        print("\n📊 Aggregation 방식 (게시글 + 작성자 정보):")
        aggregation_times = []
        
        for i in range(5):
            start_time = time.time()
            response = await client.get(f"http://localhost:8000/api/posts/{test_slug}/aggregated")
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = (end_time - start_time) * 1000
                aggregation_times.append(response_time)
                print(f"  테스트 {i+1}/5: {response_time:.2f}ms")
            
            await asyncio.sleep(0.1)
        
        aggregation_avg = sum(aggregation_times) / len(aggregation_times)
        
        # 3. 결과 분석
        print("\n🎯 성능 비교 결과:")
        print(f"   기존 방식 평균: {existing_avg:.2f}ms")
        print(f"   Aggregation 평균: {aggregation_avg:.2f}ms")
        
        if aggregation_avg < existing_avg:
            improvement = ((existing_avg - aggregation_avg) / existing_avg) * 100
            print(f"   성능 개선: {improvement:.1f}% 향상")
        else:
            regression = ((aggregation_avg - existing_avg) / existing_avg) * 100
            print(f"   성능 저하: {regression:.1f}% 느려짐")
        
        # 4. 결과 저장
        result = {
            "test_type": "aggregation_comparison",
            "existing_avg_ms": existing_avg,
            "aggregation_avg_ms": aggregation_avg,
            "existing_times": existing_times,
            "aggregation_times": aggregation_times,
            "improvement_percentage": ((existing_avg - aggregation_avg) / existing_avg) * 100
        }
        
        import json
        with open("/home/nadle/projects/Xai_Community/v5/records/25-07-08/aggregation_comparison.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 결과가 records/25-07-08/aggregation_comparison.json에 저장되었습니다")
        
        return result


if __name__ == "__main__":
    asyncio.run(test_performance_comparison())