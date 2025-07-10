#!/usr/bin/env python3
"""
완전 통합 Aggregation HTTP API 테스트
"""

import asyncio
import aiohttp
import time
import urllib.parse

async def test_complete_http_api():
    """완전 통합 Aggregation HTTP API 테스트"""
    
    # 테스트할 게시글 정보
    base_url = "http://localhost:8000"
    test_slug = "6867b9d96ec8a1b04c9c116b-정수1"
    
    # URL 인코딩된 slug (한국어 처리)
    encoded_slug = urllib.parse.quote(test_slug, safe='-')
    print(f"🔍 테스트 대상: {test_slug}")
    print(f"🔗 인코딩된 slug: {encoded_slug}")
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        try:
            # 1. 기존 full 엔드포인트 테스트
            print(f"\n📋 1. 기존 full 엔드포인트 테스트:")
            full_url = f"{base_url}/api/posts/{encoded_slug}/full"
            print(f"   URL: {full_url}")
            
            start_time = time.time()
            async with session.get(full_url) as response:
                end_time = time.time()
                full_time = (end_time - start_time) * 1000
                
                print(f"   상태 코드: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 성공! 소요 시간: {full_time:.2f}ms")
                    if data.get("success") and data.get("data"):
                        post_data = data["data"]
                        print(f"   게시글: {post_data.get('title', 'N/A')}")
                        print(f"   작성자: {post_data.get('author', {}).get('user_handle', 'N/A')}")
                        print(f"   댓글 수: {len(post_data.get('comments', []))}")
                else:
                    print(f"   ❌ 실패: {response.status}")
                    error_text = await response.text()
                    print(f"   오류: {error_text}")
                    full_time = 0
        
        except Exception as e:
            print(f"   ❌ full 엔드포인트 실패: {e}")
            full_time = 0
        
        try:
            # 2. 새로운 complete 엔드포인트 테스트
            print(f"\n🚀 2. 새로운 complete 엔드포인트 테스트:")
            complete_url = f"{base_url}/api/posts/{encoded_slug}/complete"
            print(f"   URL: {complete_url}")
            
            start_time = time.time()
            async with session.get(complete_url) as response:
                end_time = time.time()
                complete_time = (end_time - start_time) * 1000
                
                print(f"   상태 코드: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ 성공! 소요 시간: {complete_time:.2f}ms")
                    if data.get("success") and data.get("data"):
                        post_data = data["data"]
                        print(f"   게시글: {post_data.get('title', 'N/A')}")
                        print(f"   작성자: {post_data.get('author', {}).get('user_handle', 'N/A')}")
                        print(f"   댓글 수: {len(post_data.get('comments', []))}")
                        print(f"   사용자 반응: {'user_reaction' in post_data}")
                else:
                    print(f"   ❌ 실패: {response.status}")
                    error_text = await response.text()
                    print(f"   오류: {error_text}")
                    complete_time = 0
        
        except Exception as e:
            print(f"   ❌ complete 엔드포인트 실패: {e}")
            complete_time = 0
        
        # 3. 성능 비교
        if full_time > 0 and complete_time > 0:
            improvement = ((full_time - complete_time) / full_time) * 100
            print(f"\n📊 HTTP API 성능 비교:")
            print(f"   기존 full: {full_time:.2f}ms")
            print(f"   완전 통합: {complete_time:.2f}ms")
            print(f"   성능 개선: {improvement:+.1f}%")
        
        # 4. 추가 디버깅: 엔드포인트 확인
        print(f"\n🔍 4. 엔드포인트 확인:")
        try:
            health_url = f"{base_url}/api/posts/health"
            async with session.get(health_url) as response:
                print(f"   Posts 헬스체크: {response.status}")
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   응답: {health_data}")
        except Exception as e:
            print(f"   헬스체크 실패: {e}")


if __name__ == "__main__":
    asyncio.run(test_complete_http_api())