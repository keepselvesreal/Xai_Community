#!/usr/bin/env python3
"""
캐시 히트율 측정 도구 - Phase 2 성능 분석용
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, List, Any
from statistics import mean, median, stdev
import re

# API 베이스 URL
BASE_URL = "http://localhost:8000"

# 테스트할 게시글 슬러그 (board 타입)
TEST_SLUG = "686c6cd040839f99492cab46-25-07-08-글쓰기"

# 테스트 반복 횟수
TEST_ITERATIONS = 30

class CacheHitRateMonitor:
    def __init__(self):
        self.cache_stats = {
            "post_detail": {"hits": 0, "misses": 0, "requests": 0},
            "comments_batch": {"hits": 0, "misses": 0, "requests": 0},
            "author_info": {"hits": 0, "misses": 0, "requests": 0},
            "user_reaction": {"hits": 0, "misses": 0, "requests": 0}
        }
        self.response_times = []
        
    def parse_cache_logs(self, response_text: str):
        """응답 로그에서 캐시 히트/미스 정보 파싱"""
        # 게시글 캐시
        if "📦 Redis 캐시 적중" in response_text:
            self.cache_stats["post_detail"]["hits"] += 1
        elif "캐시 미스" in response_text and "게시글" in response_text:
            self.cache_stats["post_detail"]["misses"] += 1
            
        # 댓글 캐시
        if "📦 댓글 캐시 적중" in response_text:
            self.cache_stats["comments_batch"]["hits"] += 1
        elif "🔍 댓글 캐시 미스" in response_text:
            self.cache_stats["comments_batch"]["misses"] += 1
            
        # 작성자 정보 캐시
        author_hits = len(re.findall(r"📦 작성자 정보 캐시 적중", response_text))
        author_misses = len(re.findall(r"💾 작성자 정보 캐시 저장", response_text))
        self.cache_stats["author_info"]["hits"] += author_hits
        self.cache_stats["author_info"]["misses"] += author_misses
        
        # 사용자 반응 캐시
        reaction_hits = len(re.findall(r"📦 사용자 반응 캐시 적중", response_text))
        reaction_misses = len(re.findall(r"💾 사용자 반응 캐시 저장", response_text))
        self.cache_stats["user_reaction"]["hits"] += reaction_hits
        self.cache_stats["user_reaction"]["misses"] += reaction_misses
    
    async def test_cache_performance(self):
        """캐시 성능 테스트 실행"""
        print("🚀 Phase 2 캐시 성능 측정 시작")
        print(f"📍 테스트 대상: {TEST_SLUG}")
        print(f"🔄 반복 횟수: {TEST_ITERATIONS}회")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            for i in range(TEST_ITERATIONS):
                try:
                    start_time = time.time()
                    
                    # 병렬 호출 (실제 프론트엔드 패턴)
                    tasks = [
                        session.get(f"{BASE_URL}/api/posts/{TEST_SLUG}"),
                        session.get(f"{BASE_URL}/api/posts/{TEST_SLUG}/comments")
                    ]
                    
                    responses = await asyncio.gather(*tasks)
                    
                    # 응답 텍스트 읽기
                    response_texts = []
                    for resp in responses:
                        text = await resp.text()
                        response_texts.append(text)
                        resp.close()
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000
                    self.response_times.append(response_time)
                    
                    # 캐시 로그 파싱
                    for text in response_texts:
                        self.parse_cache_logs(text)
                    
                    # 요청 수 업데이트
                    for cache_type in self.cache_stats:
                        self.cache_stats[cache_type]["requests"] += 1
                    
                    print(f"  {i+1:2d}. {response_time:6.2f}ms - Status: {[r.status for r in responses]}")
                    
                    # 서버 부하 방지
                    if i < TEST_ITERATIONS - 1:  # 마지막 요청이 아니면
                        await asyncio.sleep(0.2)
                        
                except Exception as e:
                    print(f"  {i+1:2d}. ERROR: {str(e)}")
    
    def calculate_hit_rates(self):
        """캐시 히트율 계산"""
        hit_rates = {}
        for cache_type, stats in self.cache_stats.items():
            total = stats["hits"] + stats["misses"]
            if total > 0:
                hit_rate = (stats["hits"] / total) * 100
                hit_rates[cache_type] = {
                    "hit_rate": hit_rate,
                    "hits": stats["hits"],
                    "misses": stats["misses"],
                    "total": total
                }
            else:
                hit_rates[cache_type] = {
                    "hit_rate": 0,
                    "hits": 0,
                    "misses": 0,
                    "total": 0
                }
        return hit_rates
    
    def print_results(self):
        """결과 출력"""
        print("\n" + "=" * 60)
        print("📊 Phase 2 캐시 히트율 분석 결과")
        print("=" * 60)
        
        # 응답 시간 통계
        if self.response_times:
            avg_time = mean(self.response_times)
            median_time = median(self.response_times)
            min_time = min(self.response_times)
            max_time = max(self.response_times)
            std_dev = stdev(self.response_times) if len(self.response_times) > 1 else 0
            
            print(f"\n🕐 응답 시간 통계:")
            print(f"   평균: {avg_time:.2f}ms")
            print(f"   중간값: {median_time:.2f}ms") 
            print(f"   최소: {min_time:.2f}ms")
            print(f"   최대: {max_time:.2f}ms")
            print(f"   표준편차: {std_dev:.2f}ms")
        
        # 캐시 히트율
        hit_rates = self.calculate_hit_rates()
        print(f"\n📦 캐시 히트율 분석:")
        print(f"{'캐시 유형':<20} {'히트율':<10} {'히트':<8} {'미스':<8} {'총합':<8}")
        print("-" * 60)
        
        for cache_type, stats in hit_rates.items():
            print(f"{cache_type:<20} {stats['hit_rate']:>6.1f}% {stats['hits']:>7} {stats['misses']:>7} {stats['total']:>7}")
        
        # 전체 히트율
        total_hits = sum([stats['hits'] for stats in hit_rates.values()])
        total_misses = sum([stats['misses'] for stats in hit_rates.values()])
        total_requests = total_hits + total_misses
        
        if total_requests > 0:
            overall_hit_rate = (total_hits / total_requests) * 100
            print("-" * 60)
            print(f"{'전체 평균':<20} {overall_hit_rate:>6.1f}% {total_hits:>7} {total_misses:>7} {total_requests:>7}")
        
        return {
            "response_times": {
                "avg": avg_time if self.response_times else 0,
                "median": median_time if self.response_times else 0,
                "min": min_time if self.response_times else 0,
                "max": max_time if self.response_times else 0,
                "std_dev": std_dev if self.response_times else 0
            },
            "cache_hit_rates": hit_rates,
            "overall_hit_rate": overall_hit_rate if total_requests > 0 else 0
        }

async def main():
    """메인 실행 함수"""
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
    
    # 캐시 성능 테스트
    monitor = CacheHitRateMonitor()
    await monitor.test_cache_performance()
    
    # 결과 분석 및 출력
    results = monitor.print_results()
    
    # 결과를 JSON 파일로 저장
    output_file = "/home/nadle/projects/Xai_Community/v5/backend/cache_performance_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 캐시 성능 결과가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())