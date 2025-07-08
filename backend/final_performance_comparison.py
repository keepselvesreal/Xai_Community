#!/usr/bin/env python3
"""
최종 성능 비교 테스트 - 기존 full vs 완전 통합 Aggregation
"""

import asyncio
import aiohttp
import time
import urllib.parse
import statistics

async def run_performance_test():
    """최종 성능 비교 테스트"""
    
    # 테스트 설정
    base_url = "http://localhost:8000"
    test_slug = "6867b9d96ec8a1b04c9c116b-정수1"
    encoded_slug = urllib.parse.quote(test_slug, safe='-')
    test_rounds = 10  # 10회 테스트
    
    print(f"🚀 최종 성능 비교 테스트")
    print(f"📝 테스트 대상: {test_slug}")
    print(f"🔁 테스트 횟수: {test_rounds}회")
    print(f"=" * 50)
    
    full_times = []
    complete_times = []
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        for round_num in range(1, test_rounds + 1):
            print(f"\n🔄 Round {round_num}/{test_rounds}")
            
            # 1. 기존 full 엔드포인트 테스트
            try:
                full_url = f"{base_url}/api/posts/{encoded_slug}/full"
                start_time = time.time()
                async with session.get(full_url) as response:
                    end_time = time.time()
                    if response.status == 200:
                        full_time = (end_time - start_time) * 1000
                        full_times.append(full_time)
                        print(f"   Full: {full_time:.2f}ms")
                    else:
                        print(f"   Full: 실패 ({response.status})")
            except Exception as e:
                print(f"   Full: 오류 - {e}")
            
            # 잠깐 대기
            await asyncio.sleep(0.1)
            
            # 2. 완전 통합 엔드포인트 테스트
            try:
                complete_url = f"{base_url}/api/posts/{encoded_slug}/complete"
                start_time = time.time()
                async with session.get(complete_url) as response:
                    end_time = time.time()
                    if response.status == 200:
                        complete_time = (end_time - start_time) * 1000
                        complete_times.append(complete_time)
                        print(f"   Complete: {complete_time:.2f}ms")
                    else:
                        print(f"   Complete: 실패 ({response.status})")
            except Exception as e:
                print(f"   Complete: 오류 - {e}")
            
            # 라운드 간 대기
            await asyncio.sleep(0.2)
    
    # 통계 분석
    if full_times and complete_times:
        print(f"\n" + "=" * 60)
        print(f"📊 최종 성능 비교 결과")
        print(f"=" * 60)
        
        # 기존 full 엔드포인트 통계
        full_avg = statistics.mean(full_times)
        full_min = min(full_times)
        full_max = max(full_times)
        full_median = statistics.median(full_times)
        full_stdev = statistics.stdev(full_times) if len(full_times) > 1 else 0
        
        print(f"\n🔹 기존 Full 엔드포인트 ({len(full_times)}회 측정):")
        print(f"   평균: {full_avg:.2f}ms")
        print(f"   최소: {full_min:.2f}ms")
        print(f"   최대: {full_max:.2f}ms")
        print(f"   중앙값: {full_median:.2f}ms")
        print(f"   표준편차: {full_stdev:.2f}ms")
        
        # 완전 통합 엔드포인트 통계
        complete_avg = statistics.mean(complete_times)
        complete_min = min(complete_times)
        complete_max = max(complete_times)
        complete_median = statistics.median(complete_times)
        complete_stdev = statistics.stdev(complete_times) if len(complete_times) > 1 else 0
        
        print(f"\n🚀 완전 통합 엔드포인트 ({len(complete_times)}회 측정):")
        print(f"   평균: {complete_avg:.2f}ms")
        print(f"   최소: {complete_min:.2f}ms")
        print(f"   최대: {complete_max:.2f}ms")
        print(f"   중앙값: {complete_median:.2f}ms")
        print(f"   표준편차: {complete_stdev:.2f}ms")
        
        # 성능 개선 분석
        avg_improvement = ((full_avg - complete_avg) / full_avg) * 100
        median_improvement = ((full_median - complete_median) / full_median) * 100
        best_improvement = ((full_min - complete_min) / full_min) * 100
        
        print(f"\n📈 성능 개선 분석:")
        print(f"   평균 응답시간 개선: {avg_improvement:+.1f}%")
        print(f"   중앙값 개선: {median_improvement:+.1f}%")
        print(f"   최고 성능 개선: {best_improvement:+.1f}%")
        print(f"   절대 시간 단축: {full_avg - complete_avg:.2f}ms")
        
        # 결론
        print(f"\n🎯 결론:")
        if avg_improvement > 0:
            print(f"   완전 통합 Aggregation이 평균 {avg_improvement:.1f}% 더 빠름")
            print(f"   MongoDB 단일 쿼리의 효과가 입증됨")
        else:
            print(f"   성능 차이가 미미하거나 기존 방식이 더 빠름")
        
        return {
            "full_avg": full_avg,
            "complete_avg": complete_avg,
            "improvement_percent": avg_improvement,
            "full_times": full_times,
            "complete_times": complete_times
        }
    else:
        print(f"\n❌ 테스트 실패: 충분한 데이터가 수집되지 않음")
        return None


if __name__ == "__main__":
    asyncio.run(run_performance_test())