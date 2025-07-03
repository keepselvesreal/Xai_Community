#!/usr/bin/env python3
"""
API를 통한 테스트 서비스 생성 스크립트
"""

import json
import requests

def create_test_service_via_api():
    # 서비스 데이터
    service_data = {
        "company": {
            "name": "테스트 청소업체",
            "contact": "010-1234-5678",
            "availableHours": "09:00-18:00",
            "description": "아파트 전문 청소 서비스를 제공합니다."
        },
        "services": [
            {
                "name": "일반 청소",
                "price": 50000,
                "description": "기본적인 집안 청소 서비스"
            },
            {
                "name": "입주 청소",
                "price": 80000,
                "specialPrice": 70000,
                "description": "새 입주시 전체 청소 서비스"
            }
        ]
    }
    
    # 게시글 생성 요청
    post_data = {
        "title": "테스트 청소업체",
        "content": json.dumps(service_data, ensure_ascii=False, indent=2),
        "service": "residential_community",
        "metadata": {
            "type": "moving services",
            "category": "청소",
            "tags": ["청소", "업체", "서비스"],
            "visibility": "public"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/posts",
            json=post_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            if result.get("success") and result.get("data"):
                slug = result["data"].get("slug")
                print(f"✅ Service created: {slug}")
                print(f"🔗 Frontend URL: http://localhost:5173/moving-services-post/{slug}")
                print(f"🔗 API URL: http://localhost:8000/api/posts/services/{slug}")
                return slug
        
        return None
        
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

if __name__ == "__main__":
    create_test_service_via_api()