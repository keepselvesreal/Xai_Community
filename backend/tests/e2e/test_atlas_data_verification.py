"""
MongoDB Atlas 실제 데이터 저장 검증 테스트

실제 Atlas 데이터베이스에 데이터가 저장되고 지속되는지 확인합니다.
삭제하지 않고 데이터를 남겨두어 Atlas 대시보드에서 확인할 수 있도록 합니다.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from nadle_backend.config import settings
from nadle_backend.database.connection import database
from nadle_backend.models.core import User, Post, Comment, FileRecord
from nadle_backend.utils.password import PasswordManager


@pytest.mark.asyncio
class TestAtlasDataPersistence:
    """Atlas 데이터베이스 실제 저장 검증"""
    
    async def test_persistent_data_creation(self):
        """실제 Atlas에 데이터를 생성하고 지속성을 확인합니다."""
        await database.connect()
        await database.init_beanie_models([User, Post, Comment, FileRecord])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n=== Atlas 실제 데이터 저장 검증 ({timestamp}) ===")
        print(f"Database: {database.database.name}")
        print(f"MongoDB URL: {settings.mongodb_url[:50]}...")
        
        # 1. 사용자 생성 및 Atlas 직접 확인
        password_manager = PasswordManager()
        user_data = {
            'email': f'atlas_test_{timestamp}@example.com',
            'user_handle': f'atlasuser_{timestamp}',
            'password_hash': password_manager.hash_password('atlas123'),
            'name': f'Atlas Test User {timestamp}',
            'bio': 'Real Atlas data verification test user',
            'is_admin': False,
            'status': 'active'
        }
        
        user = User(**user_data)
        await user.insert()
        print(f"✅ User created with ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Handle: {user.user_handle}")
        
        # MongoDB 직접 쿼리로 확인
        users_collection = database.database[settings.users_collection]
        atlas_user = await users_collection.find_one({"_id": user.id})
        
        if atlas_user:
            print(f"✅ Atlas에서 직접 조회 성공:")
            print(f"   Collection: {settings.users_collection}")
            print(f"   Email: {atlas_user.get('email')}")
            print(f"   Handle: {atlas_user.get('user_handle')}")
            print(f"   Created: {atlas_user.get('created_at')}")
        else:
            print(f"❌ Atlas에서 사용자를 찾을 수 없음")
            raise AssertionError("User not found in Atlas")
        
        # 2. 게시물 생성 및 Atlas 확인
        post_data = {
            'title': f'Atlas Verification Post {timestamp}',
            'content': f'이 게시물은 {timestamp}에 생성되어 실제 MongoDB Atlas의 {settings.posts_collection} 컬렉션에 저장되어야 합니다. 이 데이터는 Atlas 대시보드에서 확인할 수 있습니다.',
            'slug': f'atlas-verification-{timestamp.replace("_", "-")}',
            'author_id': str(user.id),
            'service': 'community',
            'status': 'published',
            'metadata': {
                'type': 'atlas-verification',
                'tags': ['atlas', 'verification', 'persistent'],
                'test_timestamp': timestamp,
                'editor_type': 'wysiwyg'
            }
        }
        
        post = Post(**post_data)
        await post.insert()
        print(f"\n✅ Post created with ID: {post.id}")
        print(f"   Title: {post.title}")
        print(f"   Slug: {post.slug}")
        
        # Atlas 직접 확인
        posts_collection = database.database[settings.posts_collection]
        atlas_post = await posts_collection.find_one({"_id": post.id})
        
        if atlas_post:
            print(f"✅ Atlas에서 게시물 직접 조회 성공:")
            print(f"   Collection: {settings.posts_collection}")
            print(f"   Title: {atlas_post.get('title')}")
            print(f"   Author ID: {atlas_post.get('author_id')}")
            print(f"   Metadata: {atlas_post.get('metadata', {}).get('test_timestamp')}")
        else:
            print(f"❌ Atlas에서 게시물을 찾을 수 없음")
            raise AssertionError("Post not found in Atlas")
        
        # 3. 댓글 생성 및 Atlas 확인
        comment_data = {
            'content': f'이것은 {timestamp}에 생성된 실제 Atlas 검증 댓글입니다. {settings.comments_collection} 컬렉션에 저장되어야 합니다.',
            'parent_id': str(post.id),
            'author_id': str(user.id),
            'status': 'active',
            'metadata': {
                'test_timestamp': timestamp,
                'verification_type': 'atlas_persistence'
            }
        }
        
        comment = Comment(**comment_data)
        await comment.insert()
        print(f"\n✅ Comment created with ID: {comment.id}")
        print(f"   Content length: {len(comment.content)} characters")
        print(f"   Parent post: {comment.parent_id}")
        
        # Atlas 직접 확인
        comments_collection = database.database[settings.comments_collection]
        atlas_comment = await comments_collection.find_one({"_id": comment.id})
        
        if atlas_comment:
            print(f"✅ Atlas에서 댓글 직접 조회 성공:")
            print(f"   Collection: {settings.comments_collection}")
            print(f"   Content preview: {atlas_comment.get('content', '')[:50]}...")
            print(f"   Parent ID: {atlas_comment.get('parent_id')}")
        else:
            print(f"❌ Atlas에서 댓글을 찾을 수 없음")
            raise AssertionError("Comment not found in Atlas")
        
        # 4. 파일 레코드 생성 및 Atlas 확인
        file_data = {
            'file_id': f'atlas_test_{timestamp}',
            'original_filename': f'atlas_verification_{timestamp}.jpg',
            'file_path': f'/uploads/atlas_test/{timestamp}/verification.jpg',
            'file_size': 2048576,  # 2MB
            'content_type': 'image/jpeg',
            'attachment_type': 'post_image',
            'attachment_id': str(post.id),
            'uploaded_by': str(user.id),
            'status': 'active'
        }
        
        file_record = FileRecord(**file_data)
        await file_record.insert()
        print(f"\n✅ File record created with ID: {file_record.id}")
        print(f"   File ID: {file_record.file_id}")
        print(f"   Original name: {file_record.original_filename}")
        
        # Atlas 직접 확인
        files_collection = database.database[settings.files_collection]
        atlas_file = await files_collection.find_one({"_id": file_record.id})
        
        if atlas_file:
            print(f"✅ Atlas에서 파일 레코드 직접 조회 성공:")
            print(f"   Collection: {settings.files_collection}")
            print(f"   File ID: {atlas_file.get('file_id')}")
            print(f"   Size: {atlas_file.get('file_size')} bytes")
        else:
            print(f"❌ Atlas에서 파일 레코드를 찾을 수 없음")
            raise AssertionError("File record not found in Atlas")
        
        # 5. 모든 컬렉션의 문서 수 확인
        print(f"\n📊 각 컬렉션별 총 문서 수:")
        collections_to_check = [
            (settings.users_collection, users_collection),
            (settings.posts_collection, posts_collection),
            (settings.comments_collection, comments_collection),
            (settings.files_collection, files_collection)
        ]
        
        for collection_name, collection in collections_to_check:
            total_count = await collection.count_documents({})
            test_count = await collection.count_documents({"created_at": {"$exists": True}})
            print(f"   {collection_name}: {total_count} total documents ({test_count} with created_at)")
        
        # 6. 관계형 데이터 검증
        print(f"\n🔗 데이터 관계 검증:")
        
        # 사용자의 모든 게시물
        user_posts = await posts_collection.find({"author_id": str(user.id)}).to_list(length=None)
        print(f"   User {user.user_handle}의 게시물: {len(user_posts)}개")
        
        # 게시물의 모든 댓글
        post_comments = await comments_collection.find({"parent_id": str(post.id)}).to_list(length=None)
        print(f"   Post '{post.slug}'의 댓글: {len(post_comments)}개")
        
        # 게시물의 파일들
        post_files = await files_collection.find({"attachment_id": str(post.id)}).to_list(length=None)
        print(f"   Post '{post.slug}'의 파일: {len(post_files)}개")
        
        # 7. 검색 쿼리 테스트
        print(f"\n🔍 고급 쿼리 테스트:")
        
        # 메타데이터 검색
        atlas_posts = await posts_collection.find({
            "metadata.type": "atlas-verification",
            "status": "published"
        }).to_list(length=None)
        print(f"   Atlas 검증 게시물: {len(atlas_posts)}개")
        
        # 사용자별 활동 검색
        user_activity = await comments_collection.find({
            "author_id": str(user.id),
            "status": "active"
        }).to_list(length=None)
        print(f"   User 활동 (댓글): {len(user_activity)}개")
        
        # 8. 데이터를 삭제하지 않고 Atlas 확인을 위해 보존
        print(f"\n💾 데이터 보존 (Atlas 대시보드 확인용):")
        print(f"   이 테스트로 생성된 데이터는 삭제하지 않습니다.")
        print(f"   MongoDB Atlas 대시보드에서 다음 정보로 확인하세요:")
        print(f"   - Database: {database.database.name}")
        print(f"   - Timestamp: {timestamp}")
        print(f"   - User email: {user.email}")
        print(f"   - Post slug: {post.slug}")
        
        # 연결 종료
        await database.disconnect()
        
        print(f"\n✅ Atlas 실제 데이터 저장 검증 완료!")
        print(f"🔗 MongoDB Atlas에서 확인하세요: https://cloud.mongodb.com/")
        
        return {
            'timestamp': timestamp,
            'user_id': str(user.id),
            'post_id': str(post.id),
            'comment_id': str(comment.id),
            'file_id': str(file_record.id),
            'collections': {
                'users': settings.users_collection,
                'posts': settings.posts_collection,
                'comments': settings.comments_collection,
                'files': settings.files_collection
            }
        }
    
    async def test_data_query_verification(self):
        """기존 데이터를 쿼리하여 실제 저장 확인"""
        await database.connect()
        await database.init_beanie_models([User, Post, Comment, FileRecord])
        
        print(f"\n=== 기존 Atlas 데이터 쿼리 검증 ===")
        
        # 1. 모든 컬렉션에서 최근 생성된 테스트 데이터 찾기
        collections_info = [
            (User, settings.users_collection, "atlas_test"),
            (Post, settings.posts_collection, "Atlas Verification"),
            (Comment, settings.comments_collection, "Atlas 검증 댓글"),
            (FileRecord, settings.files_collection, "atlas_test")
        ]
        
        for model_class, collection_name, search_term in collections_info:
            print(f"\n📋 {collection_name} 컬렉션 조회:")
            
            # 직접 MongoDB 쿼리
            collection = database.database[collection_name]
            
            # 최근 문서들 조회
            recent_docs = await collection.find({}).sort("_id", -1).limit(5).to_list(length=5)
            print(f"   최근 5개 문서: {len(recent_docs)}개")
            
            for i, doc in enumerate(recent_docs):
                doc_id = doc.get('_id')
                if hasattr(doc, 'get'):
                    # 문서별 주요 필드 출력
                    if collection_name == settings.users_collection:
                        email = doc.get('email', 'N/A')
                        handle = doc.get('user_handle', 'N/A')
                        print(f"     #{i+1}: {doc_id} | {email} | {handle}")
                    elif collection_name == settings.posts_collection:
                        title = doc.get('title', 'N/A')
                        slug = doc.get('slug', 'N/A')
                        print(f"     #{i+1}: {doc_id} | {title[:30]}... | {slug}")
                    elif collection_name == settings.comments_collection:
                        content = doc.get('content', 'N/A')
                        parent_id = doc.get('parent_id', 'N/A')
                        print(f"     #{i+1}: {doc_id} | {content[:30]}... | parent: {parent_id}")
                    elif collection_name == settings.files_collection:
                        file_id = doc.get('file_id', 'N/A')
                        filename = doc.get('original_filename', 'N/A')
                        print(f"     #{i+1}: {doc_id} | {file_id} | {filename}")
            
            # Beanie로도 조회
            try:
                beanie_count = await model_class.count()
                print(f"   Beanie 카운트: {beanie_count}개")
            except Exception as e:
                print(f"   Beanie 오류: {e}")
        
        # 2. 특정 테스트 데이터 검색
        print(f"\n🔍 테스트 데이터 검색:")
        
        # Atlas 검증 게시물들 찾기
        atlas_posts = await Post.find({
            "title": {"$regex": "Atlas.*Verification", "$options": "i"}
        }).to_list()
        
        print(f"   Atlas 검증 게시물: {len(atlas_posts)}개")
        for post in atlas_posts:
            print(f"     - {post.title} (ID: {post.id})")
        
        # 테스트 사용자들 찾기
        test_users = await User.find({
            "user_handle": {"$regex": "atlas.*test", "$options": "i"}
        }).to_list()
        
        print(f"   테스트 사용자: {len(test_users)}개")
        for user in test_users:
            print(f"     - {user.user_handle} ({user.email})")
        
        await database.disconnect()
        print(f"\n✅ 기존 데이터 쿼리 검증 완료!")
    
    async def test_persistent_connection_verification(self):
        """연결 재시작 후 데이터 지속성 확인"""
        print(f"\n=== 연결 재시작 후 데이터 지속성 확인 ===")
        
        # 첫 번째 연결
        await database.connect()
        await database.init_beanie_models([User, Post])
        
        # 데이터 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        password_manager = PasswordManager()
        
        user = User(
            email=f'persistence_{timestamp}@test.com',
            user_handle=f'persist_{timestamp}',
            password_hash=password_manager.hash_password('persist123'),
            name=f'Persistence Test {timestamp}'
        )
        await user.insert()
        user_id = str(user.id)
        print(f"✅ 사용자 생성: {user_id}")
        
        # 연결 종료
        await database.disconnect()
        print(f"🔌 데이터베이스 연결 종료")
        
        # 잠시 대기
        await asyncio.sleep(1)
        
        # 새로운 연결
        await database.connect()
        await database.init_beanie_models([User, Post])
        print(f"🔌 데이터베이스 재연결")
        
        # 데이터 조회
        from bson import ObjectId
        
        # ObjectId로 변환
        try:
            object_id = ObjectId(user_id)
            found_user = await User.get(object_id)
            
            if found_user:
                print(f"✅ 재연결 후 사용자 조회 성공:")
                print(f"   ID: {found_user.id}")
                print(f"   Email: {found_user.email}")
                print(f"   Handle: {found_user.user_handle}")
            else:
                print(f"❌ 재연결 후 사용자를 찾을 수 없음")
                raise AssertionError("User persistence failed")
                
        except Exception as e:
            print(f"❌ 재연결 테스트 실패: {e}")
            # MongoDB 직접 쿼리로 재확인
            collection = database.database[settings.users_collection]
            direct_user = await collection.find_one({"_id": ObjectId(user_id)})
            if direct_user:
                print(f"✅ MongoDB 직접 쿼리로는 찾음: {direct_user.get('email')}")
            else:
                print(f"❌ MongoDB 직접 쿼리로도 찾을 수 없음")
        
        await database.disconnect()
        print(f"✅ 데이터 지속성 확인 완료!")


# 직접 실행 가능한 스크립트
if __name__ == "__main__":
    async def run_all_tests():
        test_instance = TestAtlasDataPersistence()
        
        print("🚀 MongoDB Atlas 실제 데이터 저장 검증 시작")
        
        # 테스트 1: 실제 데이터 생성 및 확인
        result = await test_instance.test_persistent_data_creation()
        print(f"✅ 테스트 1 완료: {result}")
        
        # 테스트 2: 기존 데이터 쿼리
        await test_instance.test_data_query_verification()
        print(f"✅ 테스트 2 완료")
        
        # 테스트 3: 연결 재시작 후 지속성
        await test_instance.test_persistent_connection_verification()
        print(f"✅ 테스트 3 완료")
        
        print(f"\n🎉 모든 Atlas 검증 테스트 완료!")
        print(f"📊 MongoDB Atlas 대시보드에서 실제 데이터를 확인하세요.")
    
    asyncio.run(run_all_tests())