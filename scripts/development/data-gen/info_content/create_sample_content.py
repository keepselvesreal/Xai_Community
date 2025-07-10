"""
샘플 정보 콘텐츠 생성 스크립트

각 콘텐츠 타입별로 샘플 데이터를 생성하여 정보 페이지에 표시할 수 있습니다.
관리자가 실행하여 테스트용 콘텐츠를 생성하는 스크립트입니다.
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from scripts.info_content.content_types import ContentType, InfoCategory
from scripts.info_content.base_creator import ContentGenerator
from scripts.info_content.creators.ai_creator import AIContentCreator
from scripts.info_content.creators.interactive_creator import InteractiveChartCreator
from nadle_backend.models.core import Post, User, Comment
from nadle_backend.database.connection import Database


async def create_sample_contents():
    """모든 타입의 샘플 콘텐츠 생성"""
    
    # 관리자 사용자 ID (실제 환경에서는 실제 관리자 ID 사용)
    admin_user_id = "admin_user_001"
    
    print("🚀 정보 페이지 샘플 콘텐츠 생성을 시작합니다...")
    
    # 데이터베이스 연결 및 초기화
    db = Database()
    try:
        await db.connect()
        await db.init_beanie_models([Post, User, Comment])
        print("✅ 데이터베이스 연결 완료")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return
    
    try:
        # 콘텐츠 생성기 초기화
        generator = ContentGenerator(admin_user_id)
        
        # AI 콘텐츠 생성기 등록
        ai_creator = AIContentCreator(admin_user_id)
        generator.register_creator(ContentType.AI_ARTICLE, ai_creator)
        
        # 인터렉티브 차트 생성기 등록
        chart_creator = InteractiveChartCreator(admin_user_id)
        generator.register_creator(ContentType.INTERACTIVE_CHART, chart_creator)
        
        # 각 카테고리별로 AI 콘텐츠 생성
        ai_contents = []
        for category in InfoCategory:
            print(f"\n📝 {category.value} 카테고리 AI 콘텐츠 생성 중...")
            content_id = await ai_creator.create_and_save(category=category)
            ai_contents.append(content_id)
            print(f"✅ AI 콘텐츠 생성 완료: {content_id}")
        
        # 각 카테고리별로 인터렉티브 차트 생성
        chart_contents = []
        chart_types = ["line", "bar", "pie", "doughnut"]
        
        for i, category in enumerate(InfoCategory):
            chart_type = chart_types[i % len(chart_types)]
            print(f"\n📊 {category.value} 카테고리 {chart_type} 차트 생성 중...")
            content_id = await chart_creator.create_and_save(
                category=category,
                chart_type=chart_type
            )
            chart_contents.append(content_id)
            print(f"✅ 인터렉티브 차트 생성 완료: {content_id}")
        
        # 결과 요약
        print(f"\n🎉 샘플 콘텐츠 생성 완료!")
        print(f"📝 AI 생성 글: {len(ai_contents)}개")
        print(f"📊 인터렉티브 차트: {len(chart_contents)}개")
        print(f"📋 총 생성된 콘텐츠: {len(ai_contents) + len(chart_contents)}개")
        
        print(f"\n📂 생성된 콘텐츠 ID 목록:")
        print(f"AI 콘텐츠: {', '.join(ai_contents)}")
        print(f"차트 콘텐츠: {', '.join(chart_contents)}")
        
        # 정리
        await generator.cleanup()
        
        print(f"\n✨ 모든 작업이 완료되었습니다!")
        print(f"🌐 프론트엔드에서 /info 페이지를 확인해보세요.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 데이터베이스 연결 정리
        await db.disconnect()
        print("🔗 데이터베이스 연결 종료")
    

async def create_single_content(content_type: str, category: str = None):
    """단일 콘텐츠 생성"""
    
    admin_user_id = "admin_user_001"
    
    # 데이터베이스 연결 및 초기화
    db = Database()
    try:
        await db.connect()
        await db.init_beanie_models([Post, User, Comment])
        print("✅ 데이터베이스 연결 완료")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return
    
    try:
        # 콘텐츠 타입 검증
        if content_type not in [ct.value for ct in ContentType]:
            print(f"❌ 지원하지 않는 콘텐츠 타입: {content_type}")
            print(f"지원하는 타입: {[ct.value for ct in ContentType]}")
            return
        
        # 카테고리 검증
        category_enum = InfoCategory.MARKET_ANALYSIS  # 기본값
        if category:
            try:
                category_enum = InfoCategory(category)
            except ValueError:
                print(f"❌ 지원하지 않는 카테고리: {category}")
                print(f"지원하는 카테고리: {[cat.value for cat in InfoCategory]}")
                return
        
        print(f"🚀 {content_type} 타입의 {category_enum.value} 카테고리 콘텐츠 생성 중...")
        
        if content_type == ContentType.AI_ARTICLE.value:
            creator = AIContentCreator(admin_user_id)
            content_id = await creator.create_and_save(category=category_enum)
        elif content_type == ContentType.INTERACTIVE_CHART.value:
            creator = InteractiveChartCreator(admin_user_id)
            content_id = await creator.create_and_save(category=category_enum)
        else:
            print(f"❌ 아직 구현되지 않은 콘텐츠 타입: {content_type}")
            return
        
        print(f"✅ 콘텐츠 생성 완료: {content_id}")
        await creator.cleanup()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 데이터베이스 연결 정리
        await db.disconnect()
        print("🔗 데이터베이스 연결 종료")


def print_usage():
    """사용법 출력"""
    print("📖 사용법:")
    print("python create_sample_content.py [all|타입] [카테고리]")
    print("")
    print("예시:")
    print("python create_sample_content.py all                    # 모든 샘플 콘텐츠 생성")
    print("python create_sample_content.py ai_article            # AI 글만 생성")
    print("python create_sample_content.py interactive_chart     # 인터렉티브 차트만 생성")
    print("python create_sample_content.py ai_article market_analysis  # 특정 카테고리의 AI 글 생성")
    print("")
    print("📋 지원하는 콘텐츠 타입:")
    for ct in ContentType:
        print(f"  - {ct.value}")
    print("")
    print("📂 지원하는 카테고리:")
    for cat in InfoCategory:
        print(f"  - {cat.value}")


async def main():
    """메인 함수"""
    
    if len(sys.argv) == 1 or sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "all":
        await create_sample_contents()
    else:
        category = sys.argv[2] if len(sys.argv) > 2 else None
        await create_single_content(command, category)


if __name__ == "__main__":
    asyncio.run(main())