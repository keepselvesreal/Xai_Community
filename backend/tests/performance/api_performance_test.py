#!/usr/bin/env python3
"""
게시판 상세 페이지 API 성능 측정 스크립트
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, List, Any
from statistics import mean, median, stdev
import sys

# API 베이스 URL (로컬 서버 기준)
BASE_URL = "http://localhost:8000"

# 테스트할 게시글 슬러그 (board 타입 게시글)
TEST_SLUG = "686c6cd040839f99492cab46-25-07-08-글쓰기"

# 테스트할 API 엔드포인트들
API_ENDPOINTS = {
    "게시글 상세": f"{BASE_URL}/api/posts/{TEST_SLUG}",
    "게시글 댓글": f"{BASE_URL}/api/posts/{TEST_SLUG}/comments", 
    "게시글 통계": f"{BASE_URL}/api/posts/{TEST_SLUG}/stats",
    "게시글 Full (Aggregated)": f"{BASE_URL}/api/posts/{TEST_SLUG}/full",
    "게시글 Aggregated": f"{BASE_URL}/api/posts/{TEST_SLUG}/aggregated",
    "게시글 Complete": f"{BASE_URL}/api/posts/{TEST_SLUG}/complete"
}

# 테스트 반복 횟수
TEST_ITERATIONS = 20

async def measure_api_response_time(session: aiohttp.ClientSession, url: str, name: str) -> Dict[str, Any]:
    """단일 API 호출 시간 측정"""
    times = []
    errors = []
    
    print(f"\n📊 {name} API 테스트 시작...")
    
    for i in range(TEST_ITERATIONS):
        try:
            start_time = time.time()
            async with session.get(url) as response:
                await response.read()  # 응답 본문까지 완전히 읽기
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # ms로 변환
                times.append(response_time)
                
                print(f"  {i+1:2d}. {response_time:6.2f}ms - Status: {response.status}")
                
                if response.status != 200:
                    errors.append(f"Status {response.status}")
                    
        except Exception as e:
            errors.append(str(e))
            print(f"  {i+1:2d}. ERROR: {str(e)}")
            
        # 서버 부하 방지를 위한 짧은 대기
        await asyncio.sleep(0.1)
    
    if not times:
        return {
            "name": name,
            "url": url,
            "success": False,
            "error": "All requests failed",
            "errors": errors
        }
    
    # 통계 계산
    avg_time = mean(times)
    median_time = median(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = stdev(times) if len(times) > 1 else 0
    
    return {
        "name": name,
        "url": url,
        "success": True,
        "times": times,
        "avg_time": avg_time,
        "median_time": median_time,
        "min_time": min_time,
        "max_time": max_time,
        "std_dev": std_dev,
        "success_rate": (len(times) / TEST_ITERATIONS) * 100,
        "total_requests": TEST_ITERATIONS,
        "successful_requests": len(times),
        "errors": errors
    }

async def test_combined_api_calls():
    """기존 방식: 게시글 상세 + 댓글을 별도로 호출하는 시간 측정"""
    print(f"\n🔄 기존 방식 (게시글 + 댓글 별도 호출) 테스트...")
    
    times = []
    errors = []
    
    async with aiohttp.ClientSession() as session:
        for i in range(TEST_ITERATIONS):
            try:
                start_time = time.time()
                
                # 게시글 상세와 댓글을 병렬로 호출
                tasks = [
                    session.get(f"{BASE_URL}/api/posts/{TEST_SLUG}"),
                    session.get(f"{BASE_URL}/api/posts/{TEST_SLUG}/comments")
                ]
                
                responses = await asyncio.gather(*tasks)
                
                # 응답 본문 읽기
                await asyncio.gather(*[resp.read() for resp in responses])
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                times.append(response_time)
                
                print(f"  {i+1:2d}. {response_time:6.2f}ms - Status: {[r.status for r in responses]}")
                
                # 응답 닫기
                for resp in responses:
                    resp.close()
                    
            except Exception as e:
                errors.append(str(e))
                print(f"  {i+1:2d}. ERROR: {str(e)}")
                
            await asyncio.sleep(0.1)
    
    if not times:
        return {
            "name": "기존 방식 (게시글 + 댓글)",
            "success": False,
            "error": "All requests failed",
            "errors": errors
        }
    
    return {
        "name": "기존 방식 (게시글 + 댓글)",
        "success": True,
        "times": times,
        "avg_time": mean(times),
        "median_time": median(times),
        "min_time": min(times),
        "max_time": max(times),
        "std_dev": stdev(times) if len(times) > 1 else 0,
        "success_rate": (len(times) / TEST_ITERATIONS) * 100,
        "total_requests": TEST_ITERATIONS,
        "successful_requests": len(times),
        "errors": errors
    }

async def main():
    """메인 테스트 실행"""
    print("🚀 게시판 상세 페이지 API 성능 측정 시작")
    print(f"📍 테스트 대상: {TEST_SLUG}")
    print(f"🔄 반복 횟수: {TEST_ITERATIONS}회")
    print(f"🌐 서버 URL: {BASE_URL}")
    print("=" * 60)
    
    # 서버 연결 확인
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as resp:
                if resp.status == 200:
                    print("✅ 서버 연결 확인됨")
                else:
                    print(f"❌ 서버 연결 실패: {resp.status}")
                    return
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return
    
    results = []
    
    # 각 API 엔드포인트별 테스트
    async with aiohttp.ClientSession() as session:
        for name, url in API_ENDPOINTS.items():
            result = await measure_api_response_time(session, url, name)
            results.append(result)
            
            # 결과 출력
            if result["success"]:
                print(f"✅ {name}: {result['avg_time']:.2f}ms (평균)")
            else:
                print(f"❌ {name}: 실패 - {result.get('error', 'Unknown error')}")
    
    # 기존 방식 (게시글 + 댓글 별도 호출) 테스트
    combined_result = await test_combined_api_calls()
    results.append(combined_result)
    
    # 결과 출력
    if combined_result["success"]:
        print(f"✅ {combined_result['name']}: {combined_result['avg_time']:.2f}ms (평균)")
    else:
        print(f"❌ {combined_result['name']}: 실패")
    
    print("\n" + "=" * 60)
    print("📊 성능 측정 결과 요약")
    print("=" * 60)
    
    # 성공한 테스트들만 정렬하여 표시
    successful_results = [r for r in results if r["success"]]
    successful_results.sort(key=lambda x: x["avg_time"])
    
    if successful_results:
        print(f"{'순위':<4} {'API 이름':<25} {'평균(ms)':<10} {'중간값(ms)':<12} {'최소(ms)':<10} {'최대(ms)':<10} {'표준편차':<10}")
        print("-" * 85)
        
        for i, result in enumerate(successful_results, 1):
            print(f"{i:<4} {result['name']:<25} {result['avg_time']:<10.2f} {result['median_time']:<12.2f} {result['min_time']:<10.2f} {result['max_time']:<10.2f} {result['std_dev']:<10.2f}")
    
    # 성능 개선 분석
    if len(successful_results) > 1:
        fastest = successful_results[0]
        baseline = None
        
        # 기존 방식을 기준선으로 설정
        for result in successful_results:
            if "기존 방식" in result["name"]:
                baseline = result
                break
        
        if baseline:
            print(f"\n🎯 성능 개선 분석 (기준: {baseline['name']})")
            print("-" * 60)
            for result in successful_results:
                if result != baseline:
                    improvement = ((baseline["avg_time"] - result["avg_time"]) / baseline["avg_time"]) * 100
                    if improvement > 0:
                        print(f"✅ {result['name']}: {improvement:.1f}% 개선 ({result['avg_time']:.2f}ms)")
                    else:
                        print(f"❌ {result['name']}: {abs(improvement):.1f}% 느림 ({result['avg_time']:.2f}ms)")
    
    # 결과를 JSON 파일로 저장
    output_file = "/home/nadle/projects/Xai_Community/v5/backend/performance_results_detailed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 상세 결과가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())