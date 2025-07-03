#!/usr/bin/env python3
"""입주 업체 서비스 API의 문의/후기 통계 테스트"""

import asyncio
import httpx
from datetime import datetime
import json

BASE_URL = "http://localhost:8001"

async def test_service_stats():
    """서비스 통계 API 테스트"""
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. 입주 업체 서비스 목록 조회
            print("🔍 입주 업체 서비스 목록 조회 중...")
            response = await client.get(
                f"{BASE_URL}/api/posts/",
                params={
                    "metadata_type": "moving services",
                    "page": 1,
                    "page_size": 10
                }
            )
            
            if response.status_code != 200:
                print(f"❌ API 호출 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return
            
            data = response.json()
            print(f"✅ 총 {data.get('total', 0)}개의 서비스 발견")
            
            # 2. 각 서비스의 통계 확인
            items = data.get('items', [])
            if not items:
                print("⚠️ 서비스가 없습니다. 테스트 데이터를 먼저 생성해주세요.")
                return
            
            print("\n📊 서비스별 통계:")
            print("=" * 80)
            
            for idx, item in enumerate(items[:5], 1):  # 최대 5개만 표시
                title = item.get('title', 'Unknown')
                stats = item.get('stats', {})
                service_stats = item.get('service_stats', None)
                
                print(f"\n{idx}. {title}")
                print(f"   - 기본 통계:")
                print(f"     • 조회수: {stats.get('view_count', 0)}")
                print(f"     • 댓글수: {stats.get('comment_count', 0)}")
                print(f"     • 북마크: {stats.get('bookmark_count', 0)}")
                
                if service_stats:
                    print(f"   - 🚀 서비스 통계 (확장):")
                    print(f"     • 조회수: {service_stats.get('views', 0)}")
                    print(f"     • 관심수: {service_stats.get('bookmarks', 0)}")
                    print(f"     • 문의수: {service_stats.get('inquiries', 0)} ⭐")
                    print(f"     • 후기수: {service_stats.get('reviews', 0)} ⭐")
                else:
                    print(f"   - ❌ service_stats 없음 (문의/후기 구분 불가)")
            
            print("\n" + "=" * 80)
            
            # 3. 통계 요약
            services_with_stats = sum(1 for item in items if item.get('service_stats'))
            print(f"\n📈 통계 요약:")
            print(f"   - 전체 서비스: {len(items)}개")
            print(f"   - service_stats 포함: {services_with_stats}개")
            print(f"   - service_stats 미포함: {len(items) - services_with_stats}개")
            
            if services_with_stats == len(items):
                print("\n✅ 모든 서비스가 문의/후기 통계를 포함하고 있습니다!")
            elif services_with_stats > 0:
                print("\n⚠️ 일부 서비스만 문의/후기 통계를 포함하고 있습니다.")
            else:
                print("\n❌ 어떤 서비스도 문의/후기 통계를 포함하지 않습니다.")
                print("   백엔드 서버를 재시작했는지 확인해주세요.")
                
        except httpx.ConnectError:
            print("❌ 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.")
            print(f"   URL: {BASE_URL}")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("🚀 입주 업체 서비스 통계 API 테스트")
    print("=" * 80)
    asyncio.run(test_service_stats())