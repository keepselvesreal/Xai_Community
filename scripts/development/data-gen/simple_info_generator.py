#!/usr/bin/env python3
"""
Simple Property Information Generator

requests 모듈을 사용하여 정보 페이지용 부동산 정보 게시글을 생성하는 간단한 스크립트입니다.
"""

import requests
import json
import random
from datetime import datetime

# API 설정
API_BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"

# 정보 게시글 템플릿
INFO_TEMPLATES = {
    "market_analysis": [
        {
            "title": "2025년 {area} 아파트 시세 전망 분석",
            "content": """# 2025년 {area} 아파트 시세 전망

## 📈 시장 현황
현재 {area} 아파트 시장은 다음과 같은 특징을 보이고 있습니다:

- **평균 시세**: 전년 대비 {change}% {direction}
- **거래량**: 전월 대비 {volume_change}% {volume_direction}
- **전세 시장**: 안정세 유지, 월세 전환 증가

## 🔍 주요 분석 포인트

### 1. 공급 현황
- 신규 분양 예정: {new_supply}세대
- 준공 예정: {completion}년 {total_completion}세대

### 2. 수요 요인
- 교통 인프라 개선 (지하철 연장, 도로 확장)
- 교육 환경 개선 (학교 신설, 학군 변화)
- 상업시설 확충 (대형 쇼핑몰, 병원 등)

### 3. 전망
향후 6개월간 {area} 아파트 시장은:
- 단기적으로 현재 수준 유지 전망
- 하반기 신규 공급 물량에 따른 변동 가능성
- 정부 정책 변화에 따른 영향 주시 필요

## 💡 투자 고려사항
1. **장기 보유 관점**: 인프라 개발 수혜 지역 우선 검토
2. **실거주 목적**: 생활 편의시설과 교육 환경 고려
3. **자금 계획**: 대출 금리 상승에 따른 부담 증가 고려

*본 분석은 공개된 거래 데이터와 시장 동향을 바탕으로 작성되었으며, 투자 결정 시 전문가 상담을 권장합니다.*""",
            "tags": ["시세분석", "부동산전망", "투자분석"],
            "data_source": "부동산원, 국토교통부"
        },
        {
            "title": "{quarter} 분기 수도권 아파트 거래 동향",
            "content": """# {quarter} 분기 수도권 아파트 거래 동향

## 📊 거래량 현황
{quarter} 분기 수도권 아파트 거래량은 전분기 대비 변화를 보였습니다.

### 지역별 거래 현황
- **서울**: {seoul_volume}건 (전분기 대비 {seoul_change}%)
- **경기**: {gyeonggi_volume}건 (전분기 대비 {gyeonggi_change}%)
- **인천**: {incheon_volume}건 (전분기 대비 {incheon_change}%)

## 📈 가격 동향
평균 거래가격은 다음과 같은 변화를 보였습니다:

### 평형별 가격 변화
- **소형평형 (60㎡ 이하)**: 평균 {small_price}만원 ({small_change}%)
- **중형평형 (60~85㎡)**: 평균 {medium_price}만원 ({medium_change}%)
- **대형평형 (85㎡ 이상)**: 평균 {large_price}만원 ({large_change}%)

## 🔍 주요 특징
1. **신축 아파트**: 프리미엄 유지, 입지 조건에 따른 차별화
2. **재건축 단지**: 기대감에 따른 가격 상승
3. **역세권 물건**: 교통 접근성 우수 지역 선호도 증가

## 📋 향후 전망
- 금리 변동에 따른 시장 반응 주시
- 정부 정책 변화 모니터링 필요
- 지역별 개발 계획 검토 권장

*데이터 기준일: {report_date}*""",
            "tags": ["거래동향", "수도권", "분기보고서"],
            "data_source": "부동산원 실거래가 공개시스템"
        }
    ],
    "legal_info": [
        {
            "title": "2025년 부동산 관련 법령 주요 변경사항",
            "content": """# 2025년 부동산 관련 법령 주요 변경사항

## 📜 주요 변경 내용

### 1. 취득세 관련
- **다주택자 중과세율 조정**: 기존 {old_rate}% → {new_rate}%
- **1세대 1주택 특례 확대**: 조정대상지역 기준 완화

### 2. 양도소득세 개편
- **보유기간별 세율 구조 변경**
  - 1년 이하: {short_rate}%
  - 2년 이하: {medium_rate}%
  - 2년 초과: {long_rate}%

### 3. 임대차보호법 개정
- **전월세 상한제**: 연 {rent_limit}% 인상 제한
- **계약갱신청구권**: {renewal_years}년 → {new_renewal_years}년 연장

## ⚖️ 주요 쟁점사항

### 다주택자 과세 강화
정부는 주택 시장 안정을 위해 다주택자에 대한 세금 부담을 지속적으로 강화하고 있습니다.

**적용 대상:**
- 조정대상지역 내 2주택 이상 보유자
- 투기지역 내 1주택 보유자 (일부 조건)

### 1세대 1주택 특례 확대
실거주 목적의 주택 구입을 지원하기 위한 정책입니다.

**혜택 내용:**
- 취득세 감면 또는 경감
- 양도소득세 비과세 혜택

## 📝 실무 적용 가이드

### 주택 구입 시 체크포인트
1. **세금 부담 계산**: 취득세, 등록세 사전 계산
2. **거주 계획**: 실거주 요건 충족 방안 검토
3. **자금 출처**: 자금조달계획서 작성 필요

### 주택 매각 시 주의사항
1. **보유기간**: 세율 구간 확인
2. **거주 여부**: 실거주 특례 적용 가능성 검토
3. **세무 신고**: 정확한 신고를 위한 전문가 상담

## 💡 전문가 조언
- 법령 해석에 있어 개별 사안별 차이가 있을 수 있으므로 세무 전문가 상담 권장
- 정책 변화에 따른 영향을 사전에 검토하여 계획 수립 필요
- 관련 서류 준비와 신고 기한 준수 중요

*본 정보는 {update_date} 기준이며, 최신 법령 변화는 관련 기관 홈페이지를 확인하시기 바랍니다.*""",
            "tags": ["부동산법령", "세금", "법률변경"],
            "data_source": "국토교통부, 기획재정부"
        }
    ],
    "move_in_guide": [
        {
            "title": "신축 아파트 입주 완벽 가이드",
            "content": """# 신축 아파트 입주 완벽 가이드

## 🏠 입주 전 준비사항

### 1. 입주 일정 확인
- **입주지정기간**: 통상 30일간 (변경 불가)
- **사전점검**: 입주 2주 전 하자점검 실시
- **준비물**: 신분증, 인감증명서, 입주금 납부확인서

### 2. 하자점검 체크리스트

#### 구조 및 마감재
- [ ] 벽면 균열, 틈새 확인
- [ ] 바닥 평탄도 및 마감 상태
- [ ] 창호 개폐 상태 및 밀폐성
- [ ] 도어 개폐 상태 및 손잡이 작동

#### 전기 및 설비
- [ ] 전체 콘센트 작동 확인
- [ ] 조명 및 스위치 정상 작동
- [ ] 인터넷/TV 단자 확인
- [ ] 환기시설 작동 상태

#### 수도 및 배관
- [ ] 수압 및 온수 공급 상태
- [ ] 배수 상태 및 누수 확인
- [ ] 화장실 및 욕실 시설
- [ ] 주방 싱크대 및 수전 작동

## 📋 입주 당일 순서

### 1. 서류 제출 및 확인
1. **입주신고서** 작성 및 제출
2. **관리사무소 등록**: 세대 정보 등록
3. **주차장 등록**: 차량번호 신고
4. **우편물 수령**: 우편함 번호 확인

### 2. 각종 신청 및 등록

#### 관리사무소 업무
- 관리비 자동이체 신청
- 무인택배함 이용 신청
- 방문차량 사전등록
- 공동현관 비밀번호/카드키 수령

#### 생활 인프라 신청
- **전기**: 한국전력공사 (국번없이 123)
- **가스**: 지역 도시가스 회사
- **상하수도**: 지자체 상수도과
- **인터넷/TV**: 통신사 설치 예약

## 🛠️ 입주 초기 필수 작업

### 1. 안전 점검
- 가스 안전장치 작동 확인
- 화재감지기 배터리 확인
- 비상구 위치 파악
- 소화기 위치 확인

### 2. 환경 설정
- 실내 환기 (새집증후군 예방)
- 습도 조절 (적정 습도 40-60%)
- 온도 설정 (난방/냉방 시스템 확인)

### 3. 보안 설정
- 현관문 비밀번호 변경
- 공동현관 출입카드 등록
- CCTV 작동 확인
- 방범창 설치 (1층, 반지하)

*입주는 새로운 시작입니다. 꼼꼼한 준비로 쾌적한 주거생활을 시작하세요!*""",
            "tags": ["신축아파트", "입주준비", "체크리스트"],
            "data_source": "한국주택관리공단, 입주민 가이드"
        }
    ],
    "investment_trend": [
        {
            "title": "2025년 부동산 투자 트렌드 전망",
            "content": """# 2025년 부동산 투자 트렌드 전망

## 🎯 2025년 투자 키워드

### 1. 인프라 수혜지역
**교통망 확충 예정지역**
- GTX-{line}선 개통 예정 역세권
- 지하철 연장 구간 (9호선 4단계 등)
- 광역급행철도(GTX) 환승역 주변

**개발사업 진행지역**
- 3기 신도시 (과천, 남양주, 인천 등)
- 역세권 개발사업 (청량리, 용산 등)
- 산업단지 이전 부지 개발

### 2. 새로운 투자 관점
**ESG 부동산**
- 친환경 건축물 인증 (LEED, BREEAM 등)
- 에너지 효율 등급 우수 건물
- 스마트홈 시스템 도입 단지

**디지털 전환**
- 비대면 서비스 인프라
- 스마트 홈케어 시설
- 공유공간 및 코워킹 스페이스

## 📊 투자 유형별 전망

### 1. 주거용 부동산

#### 아파트
- **신축**: 분양가 상한제로 인한 제한적 공급
- **재건축**: 안전진단 통과 단지 중심 상승
- **재개발**: 도심 정비사업 수혜 예상

#### 오피스텔/원룸
- 1인 가구 증가로 소형 평형 수요 지속
- 대학가 및 직장 밀집지역 선호
- 임대수익률 {rental_yield}% 내외 예상

### 2. 상업용 부동산

#### 근린상가
- 배달문화 확산으로 입지 중요성 증대
- 복합용도 건물 선호 증가
- 임대료 수준: 전년 대비 {commercial_change}% 변동

#### 오피스
- 재택근무 확산으로 수요 구조 변화
- 중소형 평형 선호도 증가
- 스마트 오피스 시설 중요성 대두

## 💡 투자 전략별 가이드

### 1. 안정형 투자
**투자 성향**: 원금 보전 중시, 안정적 수익 추구

**추천 전략**:
- 역세권 내 중대형 아파트
- 학군 우수 지역 주택
- 임대수익률 {stable_yield}% 이상 물건

**주의사항**:
- 과도한 레버리지 피하기
- 유지관리비 사전 계산
- 장기보유 계획 수립

*투자는 신중하게, 정보는 정확하게 확인하시기 바랍니다.*""",
            "tags": ["부동산투자", "투자전망", "투자트렌드"],
            "data_source": "한국부동산원, 투자분석기관"
        }
    ]
}

def create_admin_and_login():
    """관리자 계정 생성 및 로그인"""
    print("1. 관리자 계정 생성/로그인 중...")
    
    # 먼저 계정 생성 시도
    register_data = {
        "email": ADMIN_EMAIL,
        "user_handle": "admin",
        "name": "Property Info Admin",
        "display_name": "Property Info Admin",
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ 관리자 계정 생성 성공")
        elif response.status_code == 409:
            print("✅ 관리자 계정이 이미 존재함")
        else:
            print(f"⚠️ 계정 생성 상태: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ 계정 생성 오류: {e}")
    
    # 로그인 시도 (OAuth2PasswordRequestForm 형식)
    login_data = {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/auth/login", data=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ 로그인 성공")
            return token
        else:
            print(f"❌ 로그인 실패: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def generate_post_content(category, template):
    """게시글 내용 생성"""
    if category == "market_analysis":
        areas = ["강남구", "서초구", "송파구", "분당구", "판교", "용산구", "마포구"]
        area = random.choice(areas)
        change = random.randint(-5, 8)
        direction = "상승" if change > 0 else "하락" if change < 0 else "보합"
        volume_change = random.randint(-15, 20)
        volume_direction = "증가" if volume_change > 0 else "감소" if volume_change < 0 else "보합"
        
        content = template["content"].format(
            area=area,
            change=abs(change),
            direction=direction,
            volume_change=abs(volume_change),
            volume_direction=volume_direction,
            new_supply=random.randint(500, 2000),
            completion=random.randint(2025, 2027),
            total_completion=random.randint(1000, 5000),
            quarter=random.choice(["1", "2", "3", "4"]),
            seoul_volume=random.randint(3000, 8000),
            seoul_change=random.randint(-10, 15),
            gyeonggi_volume=random.randint(5000, 12000),
            gyeonggi_change=random.randint(-8, 12),
            incheon_volume=random.randint(1000, 3000),
            incheon_change=random.randint(-12, 10),
            small_price=random.randint(30000, 80000),
            small_change=random.randint(-3, 8),
            medium_price=random.randint(60000, 120000),
            medium_change=random.randint(-5, 10),
            large_price=random.randint(100000, 200000),
            large_change=random.randint(-3, 12),
            report_date=datetime.now().strftime("%Y년 %m월 %d일")
        )
        title = template["title"].format(area=area, quarter=f"{random.choice(['1', '2', '3', '4'])}분기")
        
    elif category == "legal_info":
        content = template["content"].format(
            old_rate=random.choice([8, 10, 12]),
            new_rate=random.choice([10, 12, 15]),
            short_rate=random.choice([40, 50, 60]),
            medium_rate=random.choice([30, 40, 50]),
            long_rate=random.choice([6, 10, 20]),
            rent_limit=random.choice([4, 5, 6]),
            renewal_years=2,
            new_renewal_years=4,
            update_date=datetime.now().strftime("%Y년 %m월 %d일")
        )
        title = template["title"]
        
    elif category == "investment_trend":
        content = template["content"].format(
            line=random.choice(["A", "B", "C"]),
            rental_yield=round(random.uniform(3.5, 5.5), 1),
            commercial_change=random.randint(-5, 10),
            stable_yield=round(random.uniform(4.0, 6.0), 1)
        )
        title = template["title"]
        
    else:
        content = template["content"]
        title = template["title"]
    
    return title, content

def create_info_posts(token, num_posts=10):
    """정보 게시글 생성"""
    print(f"2. {num_posts}개의 정보 게시글 생성 중...")
    
    headers = {"Authorization": f"Bearer {token}"}
    created_posts = []
    
    categories = list(INFO_TEMPLATES.keys())
    
    for i in range(num_posts):
        category = categories[i % len(categories)]
        template = random.choice(INFO_TEMPLATES[category])
        
        # 게시글 내용 생성
        title, content = generate_post_content(category, template)
        
        post_data = {
            "title": title,
            "content": content,
            "service": "residential_community",  # 필수 필드 추가
            "metadata": {
                "type": "property_information",
                "category": category,
                "tags": template["tags"],
                "summary": title[:100],  # 제목의 처음 100자를 요약으로 사용
                "data_source": template["data_source"],
                "content_type": "ai_article"
            }
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/posts/", 
                json=post_data, 
                headers=headers
            )
            
            if response.status_code == 201:
                result = response.json()
                created_posts.append(result)
                print(f"✅ 게시글 생성 성공 ({len(created_posts)}/{num_posts}): {title[:30]}...")
            else:
                print(f"❌ 게시글 생성 실패 ({i+1}): {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 게시글 생성 오류 ({i+1}): {e}")
    
    return created_posts

def verify_posts():
    """생성된 게시글 확인"""
    print("3. 생성된 게시글 확인 중...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/posts/",
            params={
                "metadata_type": "property_information",
                "page_size": 50
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            posts = result.get("items", [])
            
            print(f"📊 확인 결과:")
            print(f"   총 정보 게시글: {len(posts)}개")
            
            # 카테고리별 분석
            categories = {}
            for post in posts:
                metadata = post.get("metadata", {})
                category = metadata.get("category", "Unknown")
                categories[category] = categories.get(category, 0) + 1
            
            print(f"   카테고리별 분포: {dict(categories)}")
            
            return {
                "total_posts": len(posts),
                "categories": categories,
                "posts": posts
            }
        else:
            print(f"❌ 게시글 확인 실패: {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ 게시글 확인 오류: {e}")
        return {"error": str(e)}

def main():
    """메인 함수"""
    print("🚀 간단한 정보 페이지 게시글 생성기")
    print("=" * 50)
    
    # 1. 로그인
    token = create_admin_and_login()
    if not token:
        print("❌ 로그인 실패로 종료합니다.")
        return
    
    # 2. 게시글 생성
    created_posts = create_info_posts(token, num_posts=12)
    
    if not created_posts:
        print("❌ 게시글이 생성되지 않았습니다.")
        return
    
    # 3. 확인
    verification = verify_posts()
    
    # 4. 결과 요약
    print("\n" + "=" * 50)
    print("📋 작업 완료 요약")
    print("=" * 50)
    print(f"✅ 생성된 게시글: {len(created_posts)}개")
    print(f"✅ 전체 정보 게시글: {verification.get('total_posts', 0)}개")
    
    if created_posts:
        print("\n🎯 생성된 게시글 샘플:")
        for i, post in enumerate(created_posts[:3]):
            metadata = post.get("metadata", {})
            print(f"\n{i+1}. {post['title']}")
            print(f"   카테고리: {metadata.get('category', 'N/A')}")
            print(f"   태그: {', '.join(metadata.get('tags', []))}")
    
    print("\n🌐 프론트엔드에서 확인: http://localhost:3000/info")
    print("=" * 50)

if __name__ == "__main__":
    main()