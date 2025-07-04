#!/usr/bin/env python3
"""
Property Information Content Generator

이 스크립트는 정보 페이지용 부동산 정보 게시글을 생성합니다.
관리자가 실행하여 정보 페이지에 표시할 콘텐츠를 생성하는 스크립트입니다.
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

# 정보 카테고리별 콘텐츠 템플릿
PROPERTY_INFO_CATEGORIES = {
    "market_analysis": {
        "label": "시세분석",
        "templates": [
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
        ]
    },
    "legal_info": {
        "label": "법률정보",
        "templates": [
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
            },
            {
                "title": "아파트 매매계약 시 필수 확인사항",
                "content": """# 아파트 매매계약 시 필수 확인사항

## 📋 계약 전 필수 점검사항

### 1. 물건 기본정보 확인
- **등기부등본**: 소유권, 근저당권, 전세권 등 권리관계 확인
- **건축물대장**: 실제 면적, 용도, 구조 등 기본 정보
- **토지이용계획**: 개발제한구역, 도시계획시설 등

### 2. 세금 및 공과금 확인
- **재산세**: 연체 여부 및 부과 현황
- **관리비**: 미납 관리비 및 사용료
- **공과금**: 전기, 가스, 수도요금 정산

## 📝 계약서 작성 시 주의사항

### 필수 기재사항
1. **물건의 표시**: 정확한 주소, 면적, 층수
2. **매매대금**: 계약금, 중도금, 잔금 일정
3. **특약사항**: 양 당사자 합의된 특별 조건

### 계약금 관련
- **적정 금액**: 매매대금의 10% 내외 권장
- **보관 방법**: 공인중개사 사무소 예치 또는 에스크로 서비스 이용
- **계약해제**: 계약금 포기/배상 조건 명시

## ⚠️ 주의해야 할 함정

### 1. 권리관계 복잡한 물건
- 경매나 공매 예정 물건
- 다수의 근저당권 설정 물건
- 임차인이 다수인 경우

### 2. 가격 관련 리스크
- 시세보다 현저히 저렴한 물건
- 급매물이라며 서두르게 하는 경우
- 중개수수료 할인을 내세우는 경우

## 🛡️ 안전한 거래를 위한 팁

### 전문가 활용
- **공인중개사**: 믿을 만한 업체 선택
- **법무사**: 등기 업무 및 법률 검토
- **세무사**: 세금 계산 및 절세 방안

### 금융 준비
- **대출 사전승인**: 실행 가능성 확인
- **자금 조달**: 계획적인 자금 준비
- **보험 가입**: 화재보험 등 필수 보험

## 📞 도움받을 수 있는 곳
- **부동산거래신고센터**: 거래신고 관련 문의
- **소비자보호원**: 분쟁 조정 및 상담
- **법률상담센터**: 계약서 검토 및 법률 상담

*계약은 신중하게, 확인은 철저하게 하시기 바랍니다.*""",
                "tags": ["매매계약", "계약서", "부동산거래"],
                "data_source": "국토교통부 부동산거래관리시스템"
            }
        ]
    },
    "move_in_guide": {
        "label": "입주가이드",
        "templates": [
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

## 📞 긴급상황 대응

### 비상연락처
- **관리사무소**: [단지별 번호]
- **가스 응급센터**: 국번없이 030-9119
- **전기 고장신고**: 국번없이 123
- **상수도 고장신고**: [지자체별 번호]

### 응급상황 행동요령
1. **화재 발생 시**: 119 신고 → 대피 → 관리소 연락
2. **가스 누출 시**: 환기 → 가스밸브 차단 → 전기차단 → 대피
3. **정전 시**: 관리소 연락 → 한전 신고
4. **단수 시**: 관리소 확인 → 상수도 사업소 연락

## 💡 입주 팁

### 비용 절약 방법
- 이사업체 여러 곳 견적 비교
- 포장이사 vs 반포장이사 선택
- 입주 성수기 피하기 (3, 12월)

### 생활 편의 향상
- 동별 커뮤니티 가입
- 주변 상권 및 교통편 파악
- 생활편의시설(병원, 학교 등) 위치 확인

*입주는 새로운 시작입니다. 꼼꼼한 준비로 쾌적한 주거생활을 시작하세요!*""",
                "tags": ["신축아파트", "입주준비", "체크리스트"],
                "data_source": "한국주택관리공단, 입주민 가이드"
            },
            {
                "title": "아파트 이사 준비 단계별 가이드",
                "content": """# 아파트 이사 준비 단계별 가이드

## 📅 이사 2개월 전 준비사항

### 이사업체 선정
- **견적 비교**: 최소 3곳 이상 견적서 요청
- **업체 확인**: 사업자등록증, 보험가입 여부 확인
- **후기 검토**: 온라인 후기 및 추천업체 정보 수집

### 이사 일정 결정
- **성수기 피하기**: 3월, 7-8월, 12월 피하기
- **요일 선택**: 주중이 주말보다 저렴
- **시간대**: 오전 이사가 일반적으로 유리

## 📋 이사 1개월 전 체크리스트

### 1. 관공서 업무
- [ ] 전입신고 (이사 후 14일 이내)
- [ ] 자동차 등록 변경
- [ ] 건강보험 주소 변경
- [ ] 국민연금 주소 변경

### 2. 금융기관 업무
- [ ] 은행 주소 변경
- [ ] 신용카드 주소 변경
- [ ] 보험 주소 변경
- [ ] 증권계좌 주소 변경

### 3. 생활서비스 변경
- [ ] 인터넷/케이블TV 이전 신청
- [ ] 휴대폰 주소 변경
- [ ] 우편물 이전서비스 신청
- [ ] 택배업체 주소 변경

## 📦 이사 2주 전 포장 준비

### 포장 원칙
1. **무거운 것은 작은 상자에**
2. **가벼운 것은 큰 상자에**
3. **깨지기 쉬운 것은 별도 포장**
4. **즉시 필요한 것은 따로 보관**

### 포장 순서
1. **계절용품**: 비시즌 의류, 이불 등
2. **장식품**: 액자, 소품, 책 등
3. **주방용품**: 그릇, 조리도구 (일부 남겨두기)
4. **생활용품**: 마지막에 포장

### 포장재 준비
- **골판지 상자**: 다양한 크기 준비
- **뽁뽁이**: 깨지기 쉬운 물건용
- **신문지**: 빈 공간 메우기용
- **테이프**: 박스테이프, 포장테이프
- **매직**: 내용물 표시용

## 🚛 이사 당일 체크리스트

### 이사 전 확인사항
- [ ] 전기/가스/수도 차단
- [ ] 냉장고 물빼기 (전날 실시)
- [ ] 세탁기 물빼기
- [ ] 귀중품 별도 보관
- [ ] 청소용품 준비

### 이사업체와 확인사항
- [ ] 운송보험 가입 여부
- [ ] 파손 시 배상 기준
- [ ] 추가 비용 발생 조건
- [ ] 작업 완료 예상 시간

### 신거주지 준비
- [ ] 관리사무소 입주 신고
- [ ] 전기/가스/수도 개통 신청
- [ ] 엘리베이터 사용 신청
- [ ] 주차공간 확보

## 🏠 이사 후 정착 가이드

### 즉시 해야 할 일
1. **전입신고**: 이사 후 14일 이내 필수
2. **공과금 정산**: 이전 거주지 최종 고지서 확인
3. **생필품 구입**: 당일 필요한 최소한의 물품
4. **안전점검**: 가스, 전기, 소화기 등

### 1주일 내 완료사항
- 인터넷/TV 설치
- 동네 상권 파악
- 의료기관 확인
- 대중교통 노선 파악

### 1개월 내 정착 과정
- 이웃 인사
- 주민센터 서비스 안내 받기
- 자녀 전학 수속 (해당시)
- 생활 동선 최적화

## 💰 이사 비용 절약 팁

### 견적 받을 때
- 정확한 물품량 제시
- 포장이사 vs 반포장이사 비교
- 평일/주말 요금차이 확인
- 거리별 추가요금 확인

### 직접 할 수 있는 일
- 소형 물품 직접 운반
- 기본 청소 작업
- 포장 일부 직접 진행
- 귀중품 직접 운반

*계획적인 준비로 스트레스 없는 이사를 완성하세요!*""",
                "tags": ["이사준비", "체크리스트", "이사팁"],
                "data_source": "한국소비자원, 이사가이드"
            }
        ]
    },
    "investment_trend": {
        "label": "투자동향",
        "templates": [
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

### 2. 성장형 투자
**투자 성향**: 중간 위험 감수, 자본이득 추구

**추천 전략**:
- 인프라 개발 예정 지역
- 재개발/재건축 가능성 높은 구역
- 신흥 주거지역 (3기 신도시 등)

**주의사항**:
- 개발 계획 변경 리스크
- 인허가 지연 가능성
- 시장 타이밍 중요

### 3. 적극형 투자
**투자 성향**: 높은 위험 감수, 고수익 추구

**추천 전략**:
- 경매/공매 물건
- 상업용 부동산
- 개발사업 참여 (리츠, 펀드 등)

**주의사항**:
- 충분한 시장 조사 필수
- 전문가 자문 활용
- 분산투자 원칙 준수

## ⚠️ 2025년 투자 리스크 요인

### 정책 리스크
- 부동산 세제 변화
- 대출 규제 강화/완화
- 공급 정책 변동

### 시장 리스크
- 금리 변동성 확대
- 경기 둔화 가능성
- 공급 물량 증가

### 외부 리스크
- 글로벌 경제 불확실성
- 환율 변동 영향
- 지정학적 리스크

## 📈 투자 성공을 위한 체크포인트

### 1. 사전 준비
- [ ] 투자 목표 명확화
- [ ] 자금 조달 계획 수립
- [ ] 세금 부담 사전 계산
- [ ] 시장 동향 지속 모니터링

### 2. 물건 선정
- [ ] 입지 분석 (교통, 상권, 교육)
- [ ] 시설 현황 점검
- [ ] 법적 제약사항 확인
- [ ] 수익성 분석

### 3. 거래 과정
- [ ] 계약 조건 면밀 검토
- [ ] 전문가 자문 활용
- [ ] 리스크 관리 방안 수립
- [ ] 출구 전략 계획

*투자는 신중하게, 정보는 정확하게 확인하시기 바랍니다.*""",
                "tags": ["부동산투자", "투자전망", "투자트렌드"],
                "data_source": "한국부동산원, 투자분석기관"
            }
        ]
    }
}

async def create_test_user(auth_service: AuthService, email: str, handle: str, name: str) -> User:
    """Create a test user for generating property info."""
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

def generate_property_info_data(category: str, template: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a single property info data structure."""
    
    # Template 변수 채우기
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
            rental_yield=random.uniform(3.5, 5.5),
            commercial_change=random.randint(-5, 10),
            stable_yield=random.uniform(4.0, 6.0)
        )
        title = template["title"]
        
    else:
        content = template["content"]
        title = template["title"]
    
    # Generate view counts and engagement metrics
    views_count = random.randint(500, 5000)
    likes_count = random.randint(20, int(views_count * 0.1))
    saves_count = random.randint(10, int(views_count * 0.05))
    
    # Generate creation date (within last 3 months)
    days_ago = random.randint(1, 90)
    created_at = datetime.now() - timedelta(days=days_ago)
    
    return {
        "title": title,
        "content": content,
        "service": "residential_community",
        "metadata": {
            "type": "property_information",
            "category": category,
            "tags": template["tags"],
            "summary": title,  # 제목을 요약으로 사용
            "data_source": template["data_source"],
            "content_type": "ai_article",
            "views_count": views_count,
            "likes_count": likes_count,
            "saves_count": saves_count,
            "visibility": "public",
            "editor_type": "markdown"
        }
    }

async def create_property_info_posts(posts_service: PostsService, user: User, num_posts: int = 20) -> List[Post]:
    """Create multiple property info posts."""
    created_posts = []
    
    # 카테고리별로 고르게 분배
    categories = list(PROPERTY_INFO_CATEGORIES.keys())
    posts_per_category = num_posts // len(categories)
    
    for category_key in categories:
        category_data = PROPERTY_INFO_CATEGORIES[category_key]
        
        for i in range(posts_per_category):
            # 해당 카테고리의 템플릿 중 랜덤 선택
            template = random.choice(category_data["templates"])
            
            # 데이터 생성
            post_data = generate_property_info_data(category_key, template)
            
            # Convert to PostCreate format
            from nadle_backend.models.core import PostCreate, PostMetadata
            
            post_metadata = PostMetadata(**post_data["metadata"])
            post_create = PostCreate(
                title=post_data["title"],
                content=post_data["content"],
                service=post_data["service"],
                metadata=post_metadata
            )
            
            try:
                post = await posts_service.create_post(post_create, user)
                created_posts.append(post)
                print(f"✅ Created property info {len(created_posts)}/{num_posts}: {post.title[:50]}...")
            except Exception as e:
                print(f"❌ Failed to create property info: {str(e)}")
                continue
    
    return created_posts

async def verify_created_posts(posts_service: PostsService) -> Dict[str, Any]:
    """Verify that property info posts were created successfully."""
    try:
        # Query for property information posts
        result = await posts_service.list_posts(
            page=1,
            page_size=50,
            metadata_type="property_information"
        )
        
        posts = result.get("items", [])
        print(f"\n📊 Verification Results:")
        print(f"   Total property info posts created: {len(posts)}")
        
        # Analyze by category
        categories = {}
        
        for post in posts:
            metadata = post.get("metadata", {})
            category = metadata.get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
        
        print(f"   Categories: {dict(categories)}")
        
        return {
            "total_posts": len(posts),
            "categories": categories,
            "posts": posts
        }
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return {"error": str(e)}

async def main():
    """Main function to generate property info test data."""
    print("🚀 Property Information Test Data Generator")
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
            "property_info_admin@example.com", 
            "property_admin", 
            "Property Info Admin"
        )
        
        # Generate property info posts
        print("3. Generating property information posts...")
        num_posts = 20  # Generate 20 property info posts
        created_posts = await create_property_info_posts(posts_service, test_user, num_posts)
        
        print(f"\n✅ Successfully created {len(created_posts)} property info posts!")
        
        # Verify creation
        print("4. Verifying created posts...")
        verification = await verify_created_posts(posts_service)
        
        # Generate summary report
        print("\n" + "=" * 60)
        print("📋 PROPERTY INFO GENERATION SUMMARY")
        print("=" * 60)
        print(f"✅ Total posts created: {len(created_posts)}")
        print(f"✅ Database connection: Success")
        print(f"✅ Test user created: {test_user.email}")
        print(f"✅ Verification: {verification.get('total_posts', 0)} posts found")
        
        # Show sample posts
        if created_posts:
            print("\n🎯 Sample Property Info Posts:")
            for i, post in enumerate(created_posts[:3]):
                metadata = post.metadata
                print(f"\n{i+1}. {post.title}")
                print(f"   Category: {metadata.category}")
                print(f"   Tags: {', '.join(metadata.tags)}")
                print(f"   Data Source: {metadata.data_source}")
        
        print("\n" + "=" * 60)
        print("🎉 Property Information Test Data Generation Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during property info generation: {str(e)}")
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