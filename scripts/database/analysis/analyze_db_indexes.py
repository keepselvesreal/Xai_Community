#!/usr/bin/env python3
"""
MongoDB 인덱스 분석 및 최적화 도구 - Phase 3
"""

import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import sys
import os

# 프로젝트 루트의 backend 디렉토리를 Python 경로에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../..'))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

from nadle_backend.config import settings

# 테스트할 게시글 슬러그 (board 타입)
TEST_SLUG = "686c6cd040839f99492cab46-25-07-08-글쓰기"

class MongoIndexAnalyzer:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """MongoDB 연결"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.database_name]
            # 연결 테스트
            await self.client.admin.command('ping')
            print("✅ MongoDB 연결 성공")
            return True
        except Exception as e:
            print(f"❌ MongoDB 연결 실패: {e}")
            return False
    
    async def close(self):
        """연결 종료"""
        if self.client:
            self.client.close()
    
    async def analyze_current_indexes(self):
        """현재 인덱스 분석"""
        print("\n" + "="*60)
        print("📋 현재 인덱스 구성 분석")
        print("="*60)
        
        collections = ["posts", "comments", "user_reactions", "users"]
        index_info = {}
        
        for collection_name in collections:
            try:
                collection = self.db[collection_name]
                indexes = await collection.list_indexes().to_list(length=None)
                
                print(f"\n📊 {collection_name} 컬렉션:")
                print("-" * 40)
                
                index_info[collection_name] = []
                for idx in indexes:
                    name = idx['name']
                    keys = idx['key']
                    
                    # 키 정보를 문자열로 변환
                    key_str = ", ".join([f"{k}:{v}" for k, v in keys.items()])
                    print(f"  - {name}: {key_str}")
                    
                    index_info[collection_name].append({
                        "name": name,
                        "keys": keys,
                        "key_string": key_str
                    })
                    
            except Exception as e:
                print(f"  ❌ 오류: {e}")
                index_info[collection_name] = []
        
        return index_info
    
    async def analyze_query_performance(self):
        """쿼리 실행 계획 분석"""
        print("\n" + "="*60)
        print("🔍 쿼리 실행 계획 분석")
        print("="*60)
        
        posts_collection = self.db["posts"]
        
        # 1. 게시글 slug로 조회 (게시글 상세 API)
        print(f"\n1️⃣ 게시글 slug 조회: {TEST_SLUG}")
        print("-" * 50)
        
        try:
            explain_result = await posts_collection.find({"slug": TEST_SLUG}).explain()
            execution_stats = explain_result.get("executionStats", {})
            
            print(f"  📊 실행 통계:")
            print(f"    - 실행 시간: {execution_stats.get('executionTimeMillis', 'N/A')}ms")
            print(f"    - 문서 검토: {execution_stats.get('totalDocsExamined', 'N/A')}개")
            print(f"    - 인덱스 키 검토: {execution_stats.get('totalKeysExamined', 'N/A')}개")
            print(f"    - 반환 문서: {execution_stats.get('totalDocsReturned', 'N/A')}개")
            print(f"    - 인덱스 사용: {execution_stats.get('indexName', 'N/A')}")
            
            # 승리한 플랜 정보
            winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
            stage = winning_plan.get("stage", "N/A")
            print(f"    - 실행 방식: {stage}")
            
        except Exception as e:
            print(f"  ❌ 쿼리 분석 실패: {e}")
        
        # 2. 게시글과 댓글 조회 시뮬레이션
        print(f"\n2️⃣ 댓글 조회 (parent_id 기준)")
        print("-" * 50)
        
        try:
            # 먼저 게시글 ID 가져오기
            post = await posts_collection.find_one({"slug": TEST_SLUG})
            if post:
                post_id = str(post["_id"])
                comments_collection = self.db["comments"]
                
                explain_result = await comments_collection.find({
                    "parent_id": post_id,
                    "status": "active"
                }).explain()
                
                execution_stats = explain_result.get("executionStats", {})
                print(f"  📊 댓글 조회 통계:")
                print(f"    - 실행 시간: {execution_stats.get('executionTimeMillis', 'N/A')}ms")
                print(f"    - 문서 검토: {execution_stats.get('totalDocsExamined', 'N/A')}개")
                print(f"    - 인덱스 키 검토: {execution_stats.get('totalKeysExamined', 'N/A')}개")
                print(f"    - 반환 문서: {execution_stats.get('totalDocsReturned', 'N/A')}개")
                
                winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
                stage = winning_plan.get("stage", "N/A")
                print(f"    - 실행 방식: {stage}")
                
                # 사용된 인덱스 확인
                if "indexName" in execution_stats:
                    print(f"    - 사용 인덱스: {execution_stats['indexName']}")
                
            else:
                print(f"  ❌ 테스트 게시글을 찾을 수 없습니다: {TEST_SLUG}")
                
        except Exception as e:
            print(f"  ❌ 댓글 쿼리 분석 실패: {e}")
    
    async def suggest_index_optimizations(self):
        """인덱스 최적화 제안"""
        print("\n" + "="*60)
        print("💡 인덱스 최적화 제안")
        print("="*60)
        
        suggestions = [
            {
                "collection": "posts",
                "reason": "게시글 상세 조회 최적화",
                "index": [("slug", ASCENDING), ("status", ASCENDING)],
                "index_name": "slug_status_idx",
                "description": "slug와 status를 함께 조회하는 복합 인덱스"
            },
            {
                "collection": "comments", 
                "reason": "댓글 조회 최적화",
                "index": [("parent_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)],
                "index_name": "parent_status_created_idx",
                "description": "parent_id, status, created_at 복합 인덱스로 정렬된 댓글 조회 최적화"
            },
            {
                "collection": "user_reactions",
                "reason": "사용자 반응 조회 최적화", 
                "index": [("target_type", ASCENDING), ("target_id", ASCENDING), ("user_id", ASCENDING)],
                "index_name": "target_user_idx",
                "description": "특정 게시글/댓글의 사용자 반응 조회 최적화"
            }
        ]
        
        print("\n🎯 권장 인덱스 생성:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['collection']} 컬렉션")
            print(f"   목적: {suggestion['reason']}")
            print(f"   인덱스: {suggestion['index']}")
            print(f"   이름: {suggestion['index_name']}")
            print(f"   설명: {suggestion['description']}")
        
        return suggestions
    
    async def create_optimized_indexes(self, suggestions):
        """최적화된 인덱스 생성"""
        print("\n" + "="*60)
        print("🔧 최적화 인덱스 생성")
        print("="*60)
        
        results = []
        
        for suggestion in suggestions:
            collection_name = suggestion["collection"]
            index_spec = suggestion["index"]
            index_name = suggestion["index_name"]
            
            try:
                collection = self.db[collection_name]
                
                # 인덱스가 이미 존재하는지 확인
                existing_indexes = await collection.list_indexes().to_list(length=None)
                index_exists = any(idx['name'] == index_name for idx in existing_indexes)
                
                if index_exists:
                    print(f"  ✅ {collection_name}.{index_name}: 이미 존재함")
                    results.append({
                        "collection": collection_name,
                        "index_name": index_name,
                        "status": "already_exists"
                    })
                else:
                    # 인덱스 생성
                    await collection.create_index(index_spec, name=index_name)
                    print(f"  ✅ {collection_name}.{index_name}: 생성 완료")
                    results.append({
                        "collection": collection_name,
                        "index_name": index_name,
                        "status": "created"
                    })
                    
            except Exception as e:
                print(f"  ❌ {collection_name}.{index_name}: 생성 실패 - {e}")
                results.append({
                    "collection": collection_name,
                    "index_name": index_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    async def run_full_analysis(self):
        """전체 분석 실행"""
        print("🚀 Phase 3: MongoDB 인덱스 최적화 분석 시작")
        print(f"📅 분석 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not await self.connect():
            return None
            
        try:
            # 1. 현재 인덱스 분석
            current_indexes = await self.analyze_current_indexes()
            
            # 2. 쿼리 성능 분석 (최적화 전)
            await self.analyze_query_performance()
            
            # 3. 최적화 제안
            suggestions = await self.suggest_index_optimizations()
            
            # 4. 인덱스 생성
            creation_results = await self.create_optimized_indexes(suggestions)
            
            # 5. 최적화 후 성능 분석
            print("\n" + "="*60)
            print("🔄 최적화 후 성능 재분석")
            print("="*60)
            await self.analyze_query_performance()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "current_indexes": current_indexes,
                "suggestions": suggestions,
                "creation_results": creation_results
            }
            
        finally:
            await self.close()

async def main():
    """메인 실행 함수"""
    analyzer = MongoIndexAnalyzer()
    results = await analyzer.run_full_analysis()
    
    if results:
        # 결과 저장
        output_file = "/home/nadle/projects/Xai_Community/v5/backend/mongodb_index_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 분석 결과가 {output_file}에 저장되었습니다.")
        
        # 다음 단계 안내
        print("\n" + "="*60)
        print("📋 다음 단계")
        print("="*60)
        print("1. ✅ 인덱스 분석 및 최적화 완료")
        print("2. 🔄 성능 측정으로 개선 효과 확인 필요")
        print("3. 📊 성능 추적 보고서 업데이트 예정")

if __name__ == "__main__":
    asyncio.run(main())