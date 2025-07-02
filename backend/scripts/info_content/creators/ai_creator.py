"""
AI 생성 글 콘텐츠 생성기

스크래핑한 데이터를 바탕으로 AI가 작성한 글을 생성합니다.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from scripts.info_content.base_creator import BaseContentCreator
from scripts.info_content.content_types import InfoContent, ContentType, InfoCategory


class AIContentCreator(BaseContentCreator):
    """AI 생성 글 콘텐츠 생성기"""
    
    async def create_content(
        self,
        title: str = None,
        category: InfoCategory = InfoCategory.MARKET_ANALYSIS,
        data_source: str = None,
        ai_prompt: str = None,
        tags: List[str] = None,
        **kwargs
    ) -> InfoContent:
        """AI 생성 글 콘텐츠 생성"""
        
        # 기본값 설정
        if not title:
            title = self._get_default_title(category)
        
        if not data_source:
            data_source = self._get_default_data_source(category)
        
        if not ai_prompt:
            ai_prompt = self._get_default_ai_prompt(category)
        
        if not tags:
            tags = self.get_default_tags(category)
        
        # AI 생성 콘텐츠 (실제로는 AI API 호출)
        content = self._generate_ai_content(category, data_source, ai_prompt)
        
        # 요약 생성
        summary = self._generate_summary(content)
        
        # 메타데이터 생성
        metadata = self.create_metadata(
            category=category,
            content_type=ContentType.AI_ARTICLE,
            tags=tags,
            summary=summary,
            data_source=data_source,
            ai_prompt=ai_prompt
        )
        
        # InfoContent 객체 생성
        info_content = InfoContent(
            title=title,
            content=content,
            slug=self.generate_slug(title),
            author_id=self.admin_user_id,
            content_type=ContentType.AI_ARTICLE,
            metadata=metadata
        )
        
        # 유효성 검사
        self.validate_content(info_content)
        
        return info_content
    
    def _get_default_title(self, category: InfoCategory) -> str:
        """카테고리별 기본 제목 반환"""
        titles = {
            InfoCategory.MARKET_ANALYSIS: "2024년 아파트 시세 동향 분석",
            InfoCategory.LEGAL_INFO: "전세 계약 시 체크해야 할 필수 사항",
            InfoCategory.MOVE_IN_GUIDE: "신규 입주자를 위한 완벽 가이드",
            InfoCategory.INVESTMENT_TREND: "부동산 투자 전략 및 동향 분석"
        }
        return titles.get(category, "부동산 정보")
    
    def _get_default_data_source(self, category: InfoCategory) -> str:
        """카테고리별 기본 데이터 소스 반환"""
        sources = {
            InfoCategory.MARKET_ANALYSIS: "KB부동산, 국토교통부",
            InfoCategory.LEGAL_INFO: "법무부, 대법원 판례",
            InfoCategory.MOVE_IN_GUIDE: "LH공사, 관리사무소",
            InfoCategory.INVESTMENT_TREND: "한국은행, 금융감독원"
        }
        return sources.get(category, "공공기관")
    
    def _get_default_ai_prompt(self, category: InfoCategory) -> str:
        """카테고리별 기본 AI 프롬프트 반환"""
        prompts = {
            InfoCategory.MARKET_ANALYSIS: "최신 부동산 시세 데이터를 분석하여 향후 전망과 함께 투자자들에게 유용한 인사이트를 제공하는 글을 작성해주세요.",
            InfoCategory.LEGAL_INFO: "부동산 계약 시 주의사항과 법적 권리를 알기 쉽게 설명하는 가이드를 작성해주세요.",
            InfoCategory.MOVE_IN_GUIDE: "신규 입주자가 알아야 할 절차와 팁을 단계별로 정리한 실용적인 가이드를 작성해주세요.",
            InfoCategory.INVESTMENT_TREND: "현재 부동산 투자 환경과 향후 전망을 분석하여 투자 전략을 제시하는 글을 작성해주세요."
        }
        return prompts.get(category, "유용한 부동산 정보를 제공하는 글을 작성해주세요.")
    
    def _generate_ai_content(self, category: InfoCategory, data_source: str, ai_prompt: str) -> str:
        """AI 콘텐츠 생성 (실제로는 AI API 호출 필요)"""
        # 실제 구현에서는 OpenAI API 등을 사용
        # 현재는 샘플 콘텐츠 반환
        
        sample_contents = {
            InfoCategory.MARKET_ANALYSIS: """
# 2024년 아파트 시세 동향 분석

## 현재 시장 상황

2024년 상반기 아파트 시세는 전년 대비 **3.2% 상승**을 기록했습니다. 특히 수도권 지역의 상승률이 두드러지며, 지방 시장도 점진적인 회복세를 보이고 있습니다.

## 주요 분석 포인트

### 1. 지역별 동향
- **서울**: 강남권 중심으로 5.1% 상승
- **경기**: 신도시 지역 4.2% 상승  
- **인천**: 송도, 청라 지역 2.8% 상승

### 2. 향후 전망
- 금리 정책 변화에 따른 영향 예상
- 공급 물량 증가로 인한 가격 안정화 기대
- 하반기 3-4% 추가 상승 전망

## 투자자 관점

현재 시점에서는 **신중한 접근**이 필요합니다. 단기적인 수익보다는 장기적인 관점에서의 투자 전략을 수립하시기 바랍니다.

*데이터 출처: {data_source}*
            """.format(data_source=data_source),
            
            InfoCategory.LEGAL_INFO: """
# 전세 계약 시 체크해야 할 필수 사항

## 계약 전 필수 확인사항

### 1. 등기부등본 확인
- **소유권**: 임대인이 실제 소유자인지 확인
- **근저당권**: 설정된 근저당권 금액과 전세금 비교
- **가압류, 압류**: 법적 제약 사항 여부 확인

### 2. 건물 상태 점검
- 누수, 균열 등 하자 여부
- 방수, 단열 상태 확인
- 전기, 가스, 상하수도 시설 점검

## 계약서 작성 시 주의사항

### 필수 기재 사항
1. **정확한 주소**: 지번, 도로명 주소 모두 기재
2. **전세금액**: 숫자와 한글로 병기
3. **계약기간**: 시작일과 종료일 명시
4. **특약사항**: 수리, 관리비 등 합의사항

### 보증금 보호
- **전세권 설정**: 우선변제권 확보
- **전세보증보험**: HUG 전세보증보험 가입
- **임대차신고**: 관할 구청에 신고

## 분쟁 예방 팁

계약서는 반드시 **공인중개사 사무소**에서 작성하고, 모든 조건을 명문화하여 향후 분쟁을 예방하시기 바랍니다.

*법률 자료 출처: {data_source}*
            """.format(data_source=data_source),
            
            InfoCategory.MOVE_IN_GUIDE: """
# 신규 입주자를 위한 완벽 가이드

## 입주 전 준비사항 (D-7)

### 1. 필수 서류 준비
- [ ] 주민등록등본
- [ ] 전입신고서
- [ ] 인감증명서
- [ ] 통장사본

### 2. 공과금 신청
- **전기**: 한국전력 콜센터 (123)
- **가스**: 도시가스 공급업체 
- **상수도**: 관할 구청 상수도과
- **인터넷**: 통신업체 설치 신청

## 입주 당일 체크리스트

### 오전 (10:00-12:00)
1. 열쇠 수령 및 비밀번호 변경
2. 전체 시설 점검 (누수, 하자 확인)
3. 계량기 수치 기록

### 오후 (14:00-18:00)  
1. 관리사무소 방문 및 입주신고
2. 택배보관함 신청
3. 주차등록증 발급

## 입주 후 1주일 내 할 일

### 행정 업무
- **전입신고**: 입주 후 14일 이내 필수
- **자동차 등록**: 주소 변경 신고
- **아이 전학**: 학교 및 학원 등록

### 생활 편의
- 병원, 약국 위치 파악
- 마트, 편의점 이용 방법 숙지
- 대중교통 노선 확인

## 커뮤니티 적응

이웃과의 원활한 관계를 위해 **층간소음 주의**와 **분리수거 규칙 준수**를 당부드립니다.

*정보 제공: {data_source}*
            """.format(data_source=data_source),
            
            InfoCategory.INVESTMENT_TREND: """
# 부동산 투자 전략 및 동향 분석

## 2024년 투자 환경 분석

### 거시경제 지표
- **기준금리**: 3.5% 유지 (동결 기조)
- **물가상승률**: 2.8% (안정세)
- **가계부채**: 전년 대비 2.1% 증가

### 정책 변화
- **DSR 규제**: 40% 한도 유지
- **LTV 비율**: 지역별 차등 적용
- **종합부동산세**: 세율 조정 논의

## 투자 전략별 분석

### 1. 수익형 부동산
**장점**
- 안정적인 임대수익 확보
- 인플레이션 헤지 효과

**주의사항**  
- 공실 리스크 관리 필요
- 관리비용 사전 검토

### 2. 개발 예정지 투자
**고려요소**
- 개발계획 실현 가능성
- 교통 인프라 개선 계획
- 지역 상권 발달 전망

## 투자 시 주의사항

### 리스크 관리
1. **분산투자**: 지역, 유형별 분산
2. **자금계획**: 대출 한도 내 투자
3. **시장조사**: 충분한 사전 조사

### 세금 계획
- **양도소득세**: 보유기간별 세율 확인
- **종합부동산세**: 보유 부동산 가액 합산
- **재산세**: 연간 세부담 계산

## 전문가 조언

현재 시점에서는 **보수적 접근**을 권장합니다. 무리한 레버리지보다는 안정적인 현금흐름을 우선시하는 투자 전략이 바람직합니다.

*분석 자료: {data_source}*
            """.format(data_source=data_source)
        }
        
        return sample_contents.get(category, "AI가 생성한 부동산 정보 콘텐츠입니다.")
    
    def _generate_summary(self, content: str) -> str:
        """콘텐츠 요약 생성"""
        # 실제로는 AI API로 요약 생성
        # 현재는 간단한 요약 반환
        if "시세" in content:
            return "2024년 부동산 시세 동향과 투자 전망을 분석한 전문 자료입니다."
        elif "계약" in content:
            return "전세 계약 시 반드시 확인해야 할 법적 사항과 체크리스트를 제공합니다."
        elif "입주" in content:
            return "신규 입주자를 위한 단계별 준비사항과 행정절차 안내입니다."
        elif "투자" in content:
            return "현재 부동산 투자 환경 분석과 리스크 관리 전략을 제시합니다."
        else:
            return "부동산 관련 유용한 정보를 제공하는 AI 생성 콘텐츠입니다."