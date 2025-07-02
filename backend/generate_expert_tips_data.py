#!/usr/bin/env python3
"""
Expert Tips Test Data Generator

This script generates comprehensive test data for expert tips in the backend system.
It creates posts with metadata.type = "expert_tips" and proper data structure
that matches the frontend Tip interface requirements.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Import backend dependencies
from nadle_backend.database.connection import database
from nadle_backend.models.core import User, Post, PostMetadata, UserCreate
from nadle_backend.services.auth_service import AuthService
from nadle_backend.services.posts_service import PostsService
from nadle_backend.utils.password import PasswordManager

# Expert tip categories and their related keywords
EXPERT_CATEGORIES = {
    "인테리어": ["방 꾸미기", "가구 배치", "색상 선택", "조명", "수납", "소품"],
    "생활팁": ["청소", "정리정돈", "절약", "효율성", "생활습관", "건강"],
    "요리": ["레시피", "요리법", "식재료", "주방용품", "건강식", "간편식"],
    "육아": ["아이 돌보기", "교육", "놀이", "건강관리", "소통", "성장"],
    "반려동물": ["반려견", "반려묘", "건강관리", "훈련", "용품", "놀이"],
    "가드닝": ["식물 키우기", "베란다", "화분", "물주기", "흙", "햇빛"],
    "DIY": ["만들기", "수리", "조립", "도구", "재료", "창작"],
    "건강": ["운동", "스트레칭", "영양", "수면", "스트레스", "관리"],
    "재정관리": ["절약", "투자", "가계부", "적금", "보험", "계획"],
    "취미": ["독서", "음악", "영화", "게임", "수집", "체험"]
}

# Expert profiles for generating realistic data
EXPERT_PROFILES = [
    {"name": "김민수", "title": "인테리어 디자이너", "specialties": ["인테리어", "DIY"]},
    {"name": "박영희", "title": "생활컨설턴트", "specialties": ["생활팁", "정리정돈"]},
    {"name": "이준호", "title": "요리연구가", "specialties": ["요리", "건강"]},
    {"name": "최수진", "title": "육아전문가", "specialties": ["육아", "교육"]},
    {"name": "정민아", "title": "반려동물 훈련사", "specialties": ["반려동물", "건강"]},
    {"name": "홍길동", "title": "가드닝 전문가", "specialties": ["가드닝", "생활팁"]},
    {"name": "서지혜", "title": "DIY 크리에이터", "specialties": ["DIY", "인테리어"]},
    {"name": "강태우", "title": "헬스 트레이너", "specialties": ["건강", "운동"]},
    {"name": "윤소영", "title": "재정관리 전문가", "specialties": ["재정관리", "절약"]},
    {"name": "한승우", "title": "취미생활 큐레이터", "specialties": ["취미", "생활팁"]}
]

# Sample expert tip content templates
EXPERT_TIP_TEMPLATES = {
    "인테리어": [
        {
            "title": "작은 방을 넓어 보이게 하는 {tip_detail} 방법",
            "content": "작은 방을 넓어 보이게 하려면 다음과 같은 방법을 사용해보세요:\n\n1. **밝은 색상 활용**: 벽지와 가구를 밝은 색으로 선택하여 공간감을 확대시킵니다.\n2. **거울 배치**: 창문 맞은편에 큰 거울을 설치하여 자연광을 반사시킵니다.\n3. **수직 공간 활용**: 높은 선반과 벽걸이 수납을 이용해 바닥 공간을 확보합니다.\n4. **투명 가구**: 유리나 아크릴 소재의 가구를 사용하여 시각적 부담을 줄입니다.\n\n이러한 방법들을 조합하여 사용하면 좁은 공간도 훨씬 넓고 쾌적하게 느낄 수 있습니다.",
            "keywords": ["공간 확장", "밝은 색상", "거울", "수납"]
        },
        {
            "title": "아파트 현관 {tip_detail} 인테리어 꿀팁",
            "content": "아파트 현관을 더욱 실용적이고 예쁘게 만들어보세요:\n\n**공간 활용 팁:**\n- 현관 벽면에 후크를 설치하여 가방이나 우산을 걸 수 있게 합니다\n- 신발장 위 공간에 작은 화분이나 소품을 배치합니다\n- 전신거울을 설치하여 외출 전 마지막 점검을 할 수 있게 합니다\n\n**분위기 연출:**\n- 따뜻한 색온도의 조명을 사용합니다\n- 계절에 맞는 소품으로 포인트를 줍니다\n- 향초나 디퓨저로 좋은 향을 연출합니다\n\n현관은 집의 첫인상을 결정하는 중요한 공간이니 신경 써서 꾸며보세요!",
            "keywords": ["현관 인테리어", "수납", "조명", "소품"]
        }
    ],
    "생활팁": [
        {
            "title": "전기요금 {tip_detail}% 절약하는 실용적인 방법",
            "content": "전기요금을 크게 절약할 수 있는 실용적인 방법들을 소개합니다:\n\n**가전제품 사용법:**\n1. 에어컨 적정온도 설정 (여름 26-28°C, 겨울 18-20°C)\n2. 냉장고 문 여는 횟수 줄이기\n3. 세탁기 찬물 사용하기\n4. 대기전력 차단 (멀티탭 스위치 활용)\n\n**생활 습관 개선:**\n- LED 전구로 교체하기\n- 자연채광 최대한 활용하기\n- 보온병 사용으로 전기포트 사용 줄이기\n- 시간대별 전기요금 확인하여 고효율 시간 활용\n\n이 방법들을 실천하면 월 전기요금을 20-30% 절약할 수 있습니다!",
            "keywords": ["전기요금", "절약", "가전제품", "생활습관"]
        },
        {
            "title": "옷장 정리의 {tip_detail} 단계별 가이드",
            "content": "옷장을 체계적으로 정리하는 단계별 방법을 알려드립니다:\n\n**1단계: 전체 옷 꺼내기**\n- 옷장의 모든 옷을 꺼내어 침대나 바닥에 펼칩니다\n- 현재 가지고 있는 옷의 양을 정확히 파악합니다\n\n**2단계: 분류하기**\n- 자주 입는 옷 / 가끔 입는 옷 / 안 입는 옷으로 분류\n- 계절별, 용도별로 다시 세분화합니다\n\n**3단계: 선별하기**\n- 1년 이상 입지 않은 옷은 기부 또는 처분\n- 손상된 옷은 수선 여부 결정\n\n**4단계: 배치하기**\n- 자주 입는 옷을 눈에 잘 보이는 곳에 배치\n- 색깔별, 길이별로 정렬하여 보기 좋게 정리\n\n정리 후에는 새 옷 구입 시 신중히 선택하는 습관을 기르세요!",
            "keywords": ["옷장정리", "정리정돈", "수납", "미니멀"]
        }
    ],
    "요리": [
        {
            "title": "초보자도 실패없는 {tip_detail} 요리법",
            "content": "요리 초보자도 쉽게 따라할 수 있는 간단한 요리법을 소개합니다:\n\n**기본 재료 (2인분):**\n- 주재료와 부재료 목록을 상세히 설명\n- 대체 가능한 재료들도 함께 안내\n\n**조리 과정:**\n1. **준비 단계**: 재료 손질과 계량을 먼저 완료\n2. **조리 단계**: 온도와 시간을 정확히 지키며 단계별로 진행\n3. **마무리**: 간 맞추기와 플레이팅 팁\n\n**실패하지 않는 꿀팁:**\n- 중간 불로 천천히 조리하기\n- 간은 조금씩 여러 번 맞추기\n- 조리 도구는 미리 준비해두기\n- 첫 번째는 레시피를 정확히 따라하기\n\n한 번 성공하면 다음부터는 자신만의 변화를 줄 수 있어요!",
            "keywords": ["초보 요리", "레시피", "조리법", "간단"]
        },
        {
            "title": "식재료 {tip_detail} 보관법으로 신선도 2배 늘리기",
            "content": "식재료를 올바르게 보관하여 신선도를 오래 유지하는 방법을 알려드립니다:\n\n**채소류 보관법:**\n- 잎채소: 키친타월로 감싸서 밀폐용기에 보관\n- 뿌리채소: 신문지에 싸서 서늘한 곳에 보관\n- 양파, 마늘: 통풍이 잘 되는 곳에 보관\n\n**과일류 보관법:**\n- 사과, 배: 개별 포장 후 냉장보관\n- 바나나: 실온에서 보관, 익으면 냉장고로\n- 베리류: 씻지 말고 냉장보관, 먹기 직전에 세척\n\n**육류/생선 보관법:**\n- 구매 당일 사용하지 않으면 냉동보관\n- 소분하여 냉동하면 필요한 만큼 해동 가능\n- 해동 후 재냉동은 금지\n\n**특별 팁:**\n- 허브류는 물컵에 꽂아서 보관\n- 생강은 껍질을 벗겨 냉동보관\n- 계란은 뾰족한 부분이 아래로 가게 보관\n\n올바른 보관법으로 식재료 낭비를 줄이고 경제적으로 요리해보세요!",
            "keywords": ["식재료 보관", "신선도", "냉장보관", "절약"]
        }
    ],
    "육아": [
        {
            "title": "아이와 함께하는 {tip_detail} 놀이 아이디어",
            "content": "집에서 아이와 함께 할 수 있는 재미있고 교육적인 놀이를 소개합니다:\n\n**창의력 발달 놀이:**\n- 색종이로 동물 만들기\n- 역할놀이 (의사, 선생님, 요리사 등)\n- 집 안 보물찾기 게임\n- 이야기 만들기 놀이\n\n**신체 발달 놀이:**\n- 거실에서 하는 간단한 체조\n- 베개 던지기 게임\n- 바닥에 테이프로 길 만들어 걷기\n- 춤추기 놀이\n\n**학습 놀이:**\n- 숫자 카드 게임\n- 색깔 분류 놀이\n- 알파벳 찾기 게임\n- 퍼즐 맞추기\n\n**주의사항:**\n- 아이의 연령에 맞는 놀이 선택\n- 안전한 환경에서 놀이하기\n- 아이가 지루해하면 다른 놀이로 전환\n- 적절한 휴식 시간 확보\n\n함께 놀이하는 시간이 아이에게는 최고의 선물이에요!",
            "keywords": ["육아놀이", "창의력", "학습", "집콕"]
        }
    ],
    "반려동물": [
        {
            "title": "반려견 {tip_detail} 훈련 기초 가이드",
            "content": "반려견의 기본 훈련 방법을 단계별로 설명합니다:\n\n**기본 준비사항:**\n- 보상용 간식 준비 (작고 맛있는 것)\n- 조용하고 집중할 수 있는 환경 조성\n- 짧고 일관된 명령어 사용\n- 인내심과 꾸준함이 가장 중요\n\n**기본 명령어 훈련:**\n1. **앉기(Sit)**: 간식을 위로 올리며 '앉아' 명령\n2. **기다리기(Stay)**: 손바닥을 보이며 '기다려' 명령\n3. **이리와(Come)**: 밝은 목소리로 '이리와' 명령\n4. **엎드리기(Down)**: 간식을 바닥으로 내리며 '엎드려' 명령\n\n**훈련 팁:**\n- 하루 5-10분씩 짧게 자주 훈련\n- 성공했을 때 즉시 보상하기\n- 실패해도 절대 화내지 않기\n- 같은 명령어를 가족 모두가 사용하기\n\n**주의사항:**\n- 강아지가 피곤하거나 배고플 때는 훈련 피하기\n- 처벌보다는 무시하는 방법 사용\n- 꾸준히 반복하여 습관화시키기\n\n사랑과 인내로 훈련하면 더욱 행복한 반려생활을 할 수 있어요!",
            "keywords": ["반려견 훈련", "기본 명령", "보상", "인내"]
        }
    ],
    "가드닝": [
        {
            "title": "베란다에서 {tip_detail} 키우기 완벽 가이드",
            "content": "베란다에서 식물을 성공적으로 키우는 방법을 알려드립니다:\n\n**환경 조건 파악:**\n- 햇빛 양: 반양지, 반음지, 양지 구분\n- 통풍 상태: 바람의 강도와 방향\n- 온도 변화: 계절별 온도 차이\n- 습도 조절: 물 주기와 습도 관리\n\n**식물 선택 가이드:**\n- 초보자 추천: 스킨답서스, 산세베리아, 몬스테라\n- 햇빛 많이 필요: 다육식물, 허브류\n- 그늘에서도 잘 자라는 것: 아이비, 고무나무\n\n**관리 요령:**\n- 물주기: 흙 상태를 확인하고 적절히 조절\n- 분갈이: 뿌리가 화분 밖으로 나오면 큰 화분으로 교체\n- 병충해 관리: 정기적으로 잎 상태 확인\n- 영양 공급: 월 1-2회 액체비료 사용\n\n**계절별 관리:**\n- 봄: 분갈이와 번식의 적기\n- 여름: 물주기 횟수 증가, 직사광선 차단\n- 가을: 물주기 횟수 감소, 실내 이동 준비\n- 겨울: 물주기 최소화, 온도 관리 주의\n\n작은 공간에서도 자연을 느끼며 심신을 힐링할 수 있어요!",
            "keywords": ["베란다 가드닝", "식물 키우기", "관리법", "초보자"]
        }
    ],
    "DIY": [
        {
            "title": "100% 성공하는 {tip_detail} DIY 프로젝트",
            "content": "DIY 초보자도 쉽게 따라할 수 있는 프로젝트를 소개합니다:\n\n**필요한 도구:**\n- 기본 도구: 드라이버, 망치, 줄자, 연필\n- 안전 장비: 장갑, 보안경\n- 부속품: 나사, 못, 접착제\n\n**단계별 제작 과정:**\n1. **계획 단계**: 도면 그리기, 재료 목록 작성\n2. **재료 준비**: 정확한 치수로 재료 구매\n3. **가공 단계**: 재료 자르기, 구멍 뚫기\n4. **조립 단계**: 순서대로 조립하기\n5. **마무리**: 샌딩, 페인팅, 마감재 적용\n\n**성공 팁:**\n- 처음에는 간단한 프로젝트부터 시작\n- 도구 사용법을 미리 익혀두기\n- 안전을 최우선으로 생각하기\n- 실수를 했을 때 당황하지 않기\n\n**주의사항:**\n- 전동 공구 사용 시 안전 수칙 준수\n- 작업 공간 정리정돈\n- 아이들이 접근할 수 없는 곳에서 작업\n\n**완성 후 관리:**\n- 정기적인 점검과 보수\n- 사용 후기 기록하기\n- 다음 프로젝트 계획 세우기\n\n직접 만든 것으로 생활하는 뿌듯함을 느껴보세요!",
            "keywords": ["DIY", "만들기", "도구", "안전"]
        }
    ],
    "건강": [
        {
            "title": "하루 10분 {tip_detail} 운동으로 건강 챙기기",
            "content": "바쁜 일상 속에서도 할 수 있는 간단한 운동법을 소개합니다:\n\n**아침 운동 (5분):**\n- 스트레칭 3가지 동작 (목, 어깨, 허리)\n- 제자리 걷기 2분\n- 심호흡 운동 30초\n\n**점심 운동 (3분):**\n- 의자에 앉아서 할 수 있는 다리 운동\n- 어깨 돌리기 운동\n- 목 좌우 돌리기\n\n**저녁 운동 (2분):**\n- 간단한 요가 자세 2가지\n- 복부 운동 (플랭크 30초 x 2세트)\n- 마무리 스트레칭\n\n**운동 효과:**\n- 혈액 순환 개선\n- 스트레스 해소\n- 근력 유지\n- 체력 향상\n- 수면의 질 개선\n\n**지속하는 방법:**\n- 알람을 설정하여 시간 지키기\n- 운동 달력 만들어 체크하기\n- 가족이나 친구와 함께 하기\n- 작은 목표부터 시작하기\n\n**주의사항:**\n- 무리하지 않는 선에서 시작\n- 몸에 이상이 있으면 즉시 중단\n- 운동 전후 충분한 수분 섭취\n\n건강한 습관을 만들어 더 활기찬 하루를 보내세요!",
            "keywords": ["간단 운동", "건강 관리", "스트레칭", "일상"]
        }
    ],
    "재정관리": [
        {
            "title": "월급쟁이 {tip_detail} 절약법 실전 가이드",
            "content": "실제로 돈이 모이는 절약법을 구체적으로 알려드립니다:\n\n**가계부 작성법:**\n- 수입과 지출을 정확히 기록\n- 고정비와 변동비 분류\n- 월말 결산으로 패턴 파악\n- 목표 금액 설정\n\n**생활비 절약 팁:**\n- 장보기 전 메뉴 계획 세우기\n- 할인 시간대와 할인점 이용\n- 브랜드보다 가성비 중심 선택\n- 외식 횟수 줄이고 집밥 늘리기\n\n**고정비 줄이기:**\n- 통신비: 요금제 재검토\n- 보험료: 중복 가입 확인\n- 구독 서비스: 미사용 서비스 해지\n- 대중교통: 정기권 활용\n\n**비상금 모으기:**\n- 월급의 10% 자동이체\n- 용돈 기입장 작성\n- 소소한 부수입 만들기\n- 연말정산 환급금 저축\n\n**투자 준비:**\n- 긴급자금 3-6개월치 준비\n- 투자 공부하기\n- 소액 투자부터 시작\n- 장기적 관점 갖기\n\n**절약 동기 유지법:**\n- 목표 금액과 목적 명확히 하기\n- 절약 성과 시각화하기\n- 작은 보상 시스템 만들기\n- 절약 커뮤니티 참여\n\n작은 실천이 모여 큰 변화를 만들어냅니다!",
            "keywords": ["절약", "가계부", "재정관리", "저축"]
        }
    ],
    "취미": [
        {
            "title": "집에서 즐기는 {tip_detail} 취미 추천",
            "content": "집에서 새로운 취미를 시작해보고 싶은 분들을 위한 추천 목록입니다:\n\n**창작 활동:**\n- 그림 그리기: 색연필, 수채화, 디지털 드로잉\n- 글쓰기: 일기, 시, 소설, 블로그\n- 음악: 악기 연주, 작곡, 노래\n- 만들기: 뜨개질, 십자수, 모형 제작\n\n**학습 활동:**\n- 언어 공부: 온라인 강의, 언어 교환\n- 요리 배우기: 새로운 레시피 도전\n- 독서: 다양한 장르의 책 읽기\n- 온라인 강의: 관심 분야 전문 지식\n\n**수집 활동:**\n- 우표, 동전 수집\n- 인형, 피규어 수집\n- 향수, 캔들 수집\n- 사진, 엽서 수집\n\n**디지털 취미:**\n- 사진 편집, 영상 제작\n- 게임 (보드게임, 비디오게임)\n- 온라인 커뮤니티 활동\n- SNS 콘텐츠 제작\n\n**시작하는 방법:**\n1. 관심 분야 찾기\n2. 기초 도구나 재료 준비\n3. 온라인 튜토리얼 찾기\n4. 커뮤니티 가입하기\n5. 꾸준히 시간 투자하기\n\n**지속하는 팁:**\n- 완벽하지 않아도 괜찮다는 마음가짐\n- 다른 사람과 공유하기\n- 목표 설정하기\n- 발전 과정 기록하기\n\n새로운 취미로 일상에 활력을 더해보세요!",
            "keywords": ["집콕 취미", "새로운 시작", "창작", "학습"]
        }
    ]
}

async def create_test_user(auth_service: AuthService, email: str, handle: str, name: str) -> User:
    """Create a test user for generating expert tips."""
    user_data = UserCreate(
        email=email,
        user_handle=handle,
        name=name,
        display_name=name,
        password="TestPassword123!"
    )
    
    try:
        # Check if user already exists
        existing_user = await auth_service.user_repository.get_by_email(email)
        if existing_user:
            print(f"✅ User {email} already exists, using existing user")
            return existing_user
    except:
        pass
    
    try:
        user = await auth_service.register_user(user_data)
        print(f"✅ Created test user: {email}")
        return user
    except Exception as e:
        print(f"❌ Failed to create user {email}: {str(e)}")
        raise

def generate_expert_tip_data(expert: Dict[str, Any], category: str) -> Dict[str, Any]:
    """Generate a single expert tip data structure."""
    templates = EXPERT_TIP_TEMPLATES.get(category, [])
    if not templates:
        # Fallback template
        templates = [{
            "title": f"{category} 전문가 팁",
            "content": f"{category} 관련 전문가 조언입니다. 실생활에 도움이 되는 실용적인 팁을 제공합니다.",
            "keywords": [category, "팁", "전문가"]
        }]
    
    template = random.choice(templates)
    keywords = EXPERT_CATEGORIES.get(category, [category])
    
    # Generate specific tip details
    tip_details = [
        "3가지 핵심", "5단계", "완벽한", "실용적인", "간단한", 
        "효과적인", "전문가의", "검증된", "실전", "꿀"
    ]
    
    tip_detail = random.choice(tip_details)
    title = template["title"].format(tip_detail=tip_detail)
    
    # Generate tags
    tags = random.sample(keywords, min(3, len(keywords)))
    
    # Generate view counts and engagement metrics
    views_count = random.randint(150, 2500)
    likes_count = random.randint(10, int(views_count * 0.15))
    saves_count = random.randint(5, int(views_count * 0.08))
    
    # Generate creation date (within last 6 months)
    days_ago = random.randint(1, 180)
    created_at = datetime.now() - timedelta(days=days_ago)
    
    # Determine if it's "new" (within last 7 days)
    is_new = days_ago <= 7
    
    return {
        "title": title,
        "content": template["content"],
        "service": "residential_community",
        "metadata": {
            "type": "expert_tips",
            "category": category,
            "tags": tags,
            "expert_name": expert["name"],
            "expert_title": expert["title"],
            "views_count": views_count,
            "likes_count": likes_count,
            "saves_count": saves_count,
            "is_new": is_new,
            "visibility": "public",
            "editor_type": "markdown"
        }
    }

async def create_expert_tip_posts(posts_service: PostsService, user: User, num_tips: int = 30) -> List[Post]:
    """Create multiple expert tip posts."""
    created_posts = []
    
    for i in range(num_tips):
        # Select random expert and category
        expert = random.choice(EXPERT_PROFILES)
        # Choose category from expert's specialties
        category = random.choice(expert["specialties"])
        
        # Generate tip data
        tip_data = generate_expert_tip_data(expert, category)
        
        # Convert to PostCreate format
        from nadle_backend.models.core import PostCreate, PostMetadata
        
        post_metadata = PostMetadata(**tip_data["metadata"])
        post_create = PostCreate(
            title=tip_data["title"],
            content=tip_data["content"],
            service=tip_data["service"],
            metadata=post_metadata
        )
        
        try:
            post = await posts_service.create_post(post_create, user)
            created_posts.append(post)
            print(f"✅ Created expert tip {i+1}/{num_tips}: {post.title[:50]}...")
        except Exception as e:
            print(f"❌ Failed to create expert tip {i+1}: {str(e)}")
            continue
    
    return created_posts

async def verify_created_tips(posts_service: PostsService) -> Dict[str, Any]:
    """Verify that expert tips were created successfully."""
    try:
        # Query for expert tips
        result = await posts_service.list_posts(
            page=1,
            page_size=50,
            metadata_type="expert_tips"
        )
        
        tips = result.get("items", [])
        print(f"\n📊 Verification Results:")
        print(f"   Total expert tips created: {len(tips)}")
        
        # Analyze by category
        categories = {}
        experts = {}
        
        for tip in tips:
            metadata = tip.get("metadata", {})
            category = metadata.get("category", "Unknown")
            expert_name = metadata.get("expert_name", "Unknown")
            
            categories[category] = categories.get(category, 0) + 1
            experts[expert_name] = experts.get(expert_name, 0) + 1
        
        print(f"   Categories: {dict(categories)}")
        print(f"   Experts: {dict(experts)}")
        
        return {
            "total_tips": len(tips),
            "categories": categories,
            "experts": experts,
            "tips": tips
        }
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return {"error": str(e)}

async def main():
    """Main function to generate expert tips test data."""
    print("🚀 Expert Tips Test Data Generator")
    print("=" * 60)
    
    try:
        # Initialize database connection
        print("1. Connecting to database...")
        await database.connect()
        
        # Initialize services
        auth_service = AuthService()
        posts_service = PostsService()
        
        # Create test user
        print("2. Creating test user...")
        test_user = await create_test_user(
            auth_service, 
            "expert_tips_admin@example.com", 
            "expert_admin", 
            "Expert Tips Admin"
        )
        
        # Generate expert tips
        print("3. Generating expert tips...")
        num_tips = 30  # Generate 30 expert tips
        created_posts = await create_expert_tip_posts(posts_service, test_user, num_tips)
        
        print(f"\n✅ Successfully created {len(created_posts)} expert tips!")
        
        # Verify creation
        print("4. Verifying created tips...")
        verification = await verify_created_tips(posts_service)
        
        # Generate summary report
        print("\n" + "=" * 60)
        print("📋 EXPERT TIPS GENERATION SUMMARY")
        print("=" * 60)
        print(f"✅ Total tips created: {len(created_posts)}")
        print(f"✅ Database connection: Success")
        print(f"✅ Test user created: {test_user.email}")
        print(f"✅ Verification: {verification.get('total_tips', 0)} tips found")
        
        # Show sample tips
        if created_posts:
            print("\n🎯 Sample Expert Tips:")
            for i, post in enumerate(created_posts[:3]):
                metadata = post.metadata
                print(f"\n{i+1}. {post.title}")
                print(f"   Expert: {metadata.expert_name} ({metadata.expert_title})")
                print(f"   Category: {metadata.category}")
                print(f"   Tags: {', '.join(metadata.tags)}")
                print(f"   Views: {metadata.views_count}")
        
        print("\n" + "=" * 60)
        print("🎉 Expert Tips Test Data Generation Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during expert tips generation: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close database connection
        try:
            await database.disconnect()
            print("✅ Database connection closed")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())