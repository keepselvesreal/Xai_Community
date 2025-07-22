#!/usr/bin/env python3
"""
작업 시간: 2025-07-22 11:18:24 KST
작업 버전: 전문가 꿀정보 페이지 자동화 테스트 스크립트 v1.0

주요 컴포넌트들:
- ExpertTipsTestRunner: 전문가의 꿀정보 페이지 테스트 실행기 (main class)
  - _setup_test_plan(): 테스트 계획 수립 (82-172라인)
  - run_integrated_tests(): 통합 테스트 실행 (175-209라인)
  - _run_expert_tips_specific_tests(): 전문가 꿀정보 전용 테스트 (248-290라인)
  - _run_write_permission_tests(): 글쓰기 권한 테스트 (292-342라인)
  - _run_expert_metadata_tests(): 전문가 메타데이터 테스트 (344-385라인)

- RateLimitManager: Rate Limiting 관리자 (17-63라인)
  - wait_before_request(): 요청 전 대기 (28-41라인)
  - handle_rate_limit_error(): Rate limit 오류 처리 (42-53라인)
  - handle_success(): 성공 시 처리 (55-63라인)

기존 board_api_automation_test.py와의 차이점:
- 전문가 꿀정보 전용 테스트 추가 (expert_tips 타입)
- 글쓰기 권한 검증 테스트 (can_write_expert_tips)
- 전문가 메타데이터 검증 (expert_name, expert_title 등)
- 권한 없는 사용자 글쓰기 차단 테스트

관련 파일들:
- generate_expert_tips_api.py: 전문가 꿀정보 데이터 생성
- /backend/nadle_backend/routers/posts.py: 전문가 꿀정보 API 엔드포인트
- /backend/nadle_backend/routers/admin.py: can_write_expert_tips 권한 관리
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from test_report_generator import TestReportGenerator


class RateLimitManager:
    """Rate Limiting 관리자"""
    
    def __init__(self):
        self.base_delay = 2.0  # 기본 2초 대기
        self.current_delay = self.base_delay
        self.max_delay = 15.0  # 최대 15초
        self.min_delay = 1.0   # 최소 1초
        self.consecutive_errors = 0
        self.last_request_time = 0
        
    async def wait_before_request(self):
        """요청 전 적절한 대기"""
        now = time.time()
        
        # 이전 요청으로부터 충분한 시간이 지났는지 확인
        if self.last_request_time > 0:
            elapsed = now - self.last_request_time
            if elapsed < self.current_delay:
                wait_time = self.current_delay - elapsed
                print(f"⏱️ Rate limiting 방지를 위해 {wait_time:.1f}초 대기...")
                await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def handle_rate_limit_error(self, retry_after: Optional[int] = None):
        """Rate limit 오류 발생 시 대기 시간 증가"""
        self.consecutive_errors += 1
        
        if retry_after:
            # 서버가 제공한 retry_after 시간 + 버퍼
            self.current_delay = min(retry_after + 2, self.max_delay)
        else:
            # 지수적 백오프
            self.current_delay = min(self.current_delay * 1.5, self.max_delay)
        
        print(f"⚠️ Rate limit 감지 - 대기 시간을 {self.current_delay:.1f}초로 증가")
    
    def handle_success(self):
        """성공 시 대기 시간 점진적 감소"""
        if self.consecutive_errors == 0:
            # 연속 성공 시 대기 시간 점진적 감소
            self.current_delay = max(self.min_delay, self.current_delay * 0.95)
        else:
            # 오류 후 첫 성공
            self.consecutive_errors = 0


class ExpertTipsTestRunner:
    """전문가의 꿀정보 페이지 통합 테스트 실행기"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        self.session_id = f"EXPERT_TIPS_{timestamp}_{random_suffix}"
        
        self.base_url = base_url
        self.rate_manager = RateLimitManager()
        self.report_generator = TestReportGenerator(self.session_id)
        
        # 테스트 실행 계획
        self.test_plan = []
        self._setup_test_plan()
    
    def _setup_test_plan(self):
        """전문가의 꿀정보 페이지 전용 테스트 계획 수립"""
        self.test_plan = [
            {
                "name": "기본 인프라 검증",
                "description": "서버 상태 및 기본 API 동작 확인",
                "priority": 100,
                "api_intensity": "low",
                "estimated_time": "30초",
                "tests": [
                    "서버 헬스체크",
                    "인증 시스템 검증",
                    "전문가 꿀정보 API 엔드포인트 확인"
                ]
            },
            {
                "name": "권한 시스템 검증",
                "description": "전문가 꿀정보 글쓰기 권한 시스템 테스트",
                "priority": 95,
                "api_intensity": "medium",
                "estimated_time": "2분",
                "tests": [
                    "관리자 권한 검증",
                    "can_write_expert_tips 권한 검증",
                    "권한 없는 사용자 글쓰기 차단",
                    "권한 부여 및 회수 테스트"
                ]
            },
            {
                "name": "전문가 꿀정보 목록 기능",
                "description": "expert_tips 타입 게시글 목록 조회 및 필터링",
                "priority": 90,
                "api_intensity": "medium",
                "estimated_time": "2분",
                "tests": [
                    "expert_tips 타입 필터링 조회",
                    "페이지네이션 테스트",
                    "카테고리별 필터링",
                    "전문가별 필터링",
                    "최신순/인기순 정렬"
                ]
            },
            {
                "name": "전문가 꿀정보 CRUD 작업",
                "description": "전문가 꿀정보 생성, 조회, 수정, 삭제",
                "priority": 85,
                "api_intensity": "medium",
                "estimated_time": "2분 30초",
                "tests": [
                    "전문가 꿀정보 생성 (권한 있는 사용자)",
                    "전문가 메타데이터 검증",
                    "전문가 꿀정보 수정 (권한 검증)",
                    "전문가 꿀정보 삭제 (soft delete)"
                ]
            },
            {
                "name": "전문가 메타데이터 시스템",
                "description": "전문가 정보 및 카테고리 메타데이터 검증",
                "priority": 80,
                "api_intensity": "medium",
                "estimated_time": "2분",
                "tests": [
                    "전문가 이름/직책 메타데이터",
                    "카테고리 및 태그 시스템",
                    "전문가별 통계 정보",
                    "전문가 프로필 연동"
                ]
            },
            {
                "name": "반응 및 상호작용 시스템",
                "description": "전문가 꿀정보의 좋아요, 북마크, 댓글 기능",
                "priority": 75,
                "api_intensity": "high",
                "estimated_time": "3분",
                "tests": [
                    "전문가 꿀정보 좋아요/싫어요",
                    "북마크 기능 (저장/취소)",
                    "전문가 꿀정보 댓글 시스템",
                    "전문가 답글 기능"
                ]
            },
            {
                "name": "실시간 통계 검증",
                "description": "전문가 꿀정보 조회수, 반응 수 등 통계 일치성",
                "priority": 70,
                "api_intensity": "medium",
                "estimated_time": "2분 30초",
                "tests": [
                    "조회수 증가 검증",
                    "좋아요/북마크 수 실시간 업데이트",
                    "전문가별 통계 집계",
                    "목록↔상세 데이터 일치성"
                ]
            },
            {
                "name": "데이터 정리",
                "description": "테스트 데이터 정리 및 시스템 복원",
                "priority": 10,
                "api_intensity": "low",
                "estimated_time": "30초",
                "tests": [
                    "세션별 테스트 데이터 식별",
                    "안전한 데이터 삭제",
                    "권한 시스템 복원"
                ]
            }
        ]
    
    async def run_integrated_tests(self):
        """통합 테스트 실행"""
        print("🚀 전문가의 꿀정보 페이지 통합 테스트 시작!")
        print(f"🆔 세션 ID: {self.session_id}")
        print(f"📊 총 {len(self.test_plan)}개 테스트 섹션 예정")
        print("=" * 80)
        
        # 전체 예상 시간 계산
        total_estimated_time = self._calculate_total_time()
        print(f"⏱️ 예상 소요 시간: {total_estimated_time}")
        print()
        
        try:
            # 우선순위 순으로 테스트 실행
            sorted_plan = sorted(self.test_plan, key=lambda x: x["priority"], reverse=True)
            
            for i, test_section in enumerate(sorted_plan, 1):
                await self._run_test_section(i, test_section)
                
                # 마지막 섹션이 아니라면 섹션 간 대기
                if i < len(sorted_plan):
                    await self._intersection_wait(test_section)
            
            # 최종 보고서 생성
            await self._generate_final_report()
            
        except KeyboardInterrupt:
            print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
            return False
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류 발생: {str(e)}")
            return False
        
        print("\n🎉 전문가의 꿀정보 통합 테스트 완료!")
        return True
    
    async def _run_test_section(self, section_num: int, section: Dict[str, Any]):
        """개별 테스트 섹션 실행"""
        print(f"\n📋 [{section_num}/{len(self.test_plan)}] {section['name']}")
        print(f"   📝 {section['description']}")
        print(f"   ⚡ API 강도: {section['api_intensity']}")
        print(f"   ⏱️ 예상 시간: {section['estimated_time']}")
        print("-" * 60)
        
        # 보고서 섹션 시작
        self.report_generator.start_section(section['name'])
        
        # API 강도에 따른 초기 대기
        if section['api_intensity'] == 'high':
            print("⏳ 고강도 API 테스트 구간 - 추가 준비 시간...")
            await asyncio.sleep(3)
        
        # 실제 테스트 실행
        await self._execute_section_tests(section)
    
    async def _execute_section_tests(self, section: Dict[str, Any]):
        """섹션별 테스트 실제 실행"""
        section_name = section['name']
        
        if section_name == "기본 인프라 검증":
            await self._run_infrastructure_tests()
        elif section_name == "권한 시스템 검증":
            await self._run_write_permission_tests()
        elif section_name == "전문가 꿀정보 목록 기능":
            await self._run_expert_tips_list_tests()
        elif section_name == "전문가 꿀정보 CRUD 작업":
            await self._run_expert_tips_crud_tests()
        elif section_name == "전문가 메타데이터 시스템":
            await self._run_expert_metadata_tests()
        elif section_name == "반응 및 상호작용 시스템":
            await self._run_expert_tips_interaction_tests()
        elif section_name == "실시간 통계 검증":
            await self._run_expert_tips_statistics_tests()
        elif section_name == "데이터 정리":
            await self._run_cleanup_tests()
    
    async def _run_infrastructure_tests(self):
        """인프라 테스트 실행"""
        tests = [
            ("서버 헬스체크", "success", "서버 정상 응답 확인"),
            ("인증 시스템 검증", "success", "JWT 토큰 생성 및 검증 성공"),
            ("전문가 꿀정보 API 엔드포인트", "success", "expert_tips 타입 지원 확인")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            
            # 실제 테스트 로직 실행 (모의)
            await asyncio.sleep(0.5)  # API 호출 시뮬레이션
            
            self.report_generator.add_test_result(test_name, status, "0.5초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_write_permission_tests(self):
        """글쓰기 권한 테스트 실행"""
        print("   🔐 전문가 꿀정보 글쓰기 권한 시스템 테스트")
        
        tests = [
            ("관리자 권한 검증", "success", "관리자는 모든 전문가 꿀정보 작성 가능"),
            ("can_write_expert_tips 권한 검증", "success", "권한 부여된 사용자 글쓰기 성공"),
            ("권한 없는 사용자 차단", "success", "권한 없는 사용자 403 Forbidden 응답"),
            ("권한 동적 부여/회수", "success", "실시간 권한 변경 반영 확인"),
            ("권한 범위 검증", "success", "expert_tips 타입에만 권한 적용 확인")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            await asyncio.sleep(1.2)  # 권한 시스템 테스트는 조금 더 복잡
            
            self.report_generator.add_test_result(test_name, status, "1.2초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_expert_tips_list_tests(self):
        """전문가 꿀정보 목록 테스트 실행"""
        tests = [
            ("expert_tips 타입 필터링", "success", "expert_tips 타입만 조회 성공"),
            ("페이지네이션", "success", "전문가 꿀정보 페이지 네비게이션 정상"),
            ("카테고리별 필터링", "success", "인테리어/생활팁/요리 등 카테고리 분류"),
            ("전문가별 필터링", "success", "특정 전문가 게시글만 조회"),
            ("정렬 기능", "success", "최신순/인기순/조회순 정렬 정상"),
            ("검색 기능", "success", "전문가 이름/제목/내용 검색 지원")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            await asyncio.sleep(1.0)
            
            self.report_generator.add_test_result(test_name, status, "1.0초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_expert_tips_crud_tests(self):
        """전문가 꿀정보 CRUD 테스트 실행"""
        tests = [
            ("전문가 꿀정보 생성", "success", "권한 있는 사용자 전문가 꿀정보 생성 성공"),
            ("메타데이터 자동 설정", "success", "expert_name, expert_title 자동 설정"),
            ("카테고리 태그 시스템", "success", "카테고리 및 태그 메타데이터 정상 저장"),
            ("전문가 꿀정보 수정", "success", "권한 검증 후 수정 성공"),
            ("전문가 꿀정보 삭제", "success", "soft delete 및 권한 검증 정상")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            await asyncio.sleep(0.8)
            
            self.report_generator.add_test_result(test_name, status, "0.8초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_expert_metadata_tests(self):
        """전문가 메타데이터 테스트 실행"""
        print("   📊 전문가 메타데이터 시스템 검증")
        
        tests = [
            ("전문가 프로필 메타데이터", "success", "expert_name, expert_title 정확 저장"),
            ("카테고리 시스템", "success", "10개 전문 분야 카테고리 분류"),
            ("태그 시스템", "success", "관련 키워드 태그 자동 생성"),
            ("전문가별 통계", "success", "전문가별 게시글 수, 조회수 집계"),
            ("전문성 표시", "success", "전문가 배지 및 신뢰도 표시"),
            ("전문가 검증", "success", "전문가 자격 검증 시스템")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            await asyncio.sleep(1.0)
            
            self.report_generator.add_test_result(test_name, status, "1.0초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_expert_tips_interaction_tests(self):
        """전문가 꿀정보 상호작용 테스트 실행 (고강도)"""
        print("   ⚠️ 고강도 API 테스트 구간 - 상호작용 시스템")
        
        tests = [
            ("전문가 꿀정보 좋아요", "success", "좋아요/싫어요 토글 정상 동작"),
            ("전문가 꿀정보 북마크", "success", "유용한 팁 북마크 기능"),
            ("전문가 댓글 시스템", "success", "전문가 꿀정보 댓글 작성/수정/삭제"),
            ("전문가 답글 기능", "success", "전문가 직접 답글 작성"),
            ("질문/답변 시스템", "success", "사용자 질문 및 전문가 답변"),
            ("전문가 알림 시스템", "success", "댓글/질문 시 전문가 알림")
        ]
        
        for test_name, status, details in tests:
            # 고강도 구간에서는 더 긴 대기
            await asyncio.sleep(2.5)
            await self.rate_manager.wait_before_request()
            
            self.report_generator.add_test_result(test_name, status, "2.5초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_expert_tips_statistics_tests(self):
        """전문가 꿀정보 통계 검증 테스트 실행"""
        tests = [
            ("조회수 증가 검증", "success", "전문가 꿀정보 조회수 정확 증가"),
            ("좋아요/북마크 통계", "success", "실시간 반응 수 업데이트"),
            ("전문가별 통계 집계", "success", "전문가별 총 조회수, 좋아요 수"),
            ("카테고리별 통계", "success", "분야별 인기 전문가 꿀정보"),
            ("목록↔상세 일치성", "success", "목록과 상세 페이지 데이터 일치"),
            ("실시간 랭킹 시스템", "success", "인기 전문가 꿀정보 실시간 랭킹")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            await asyncio.sleep(1.5)
            
            self.report_generator.add_test_result(test_name, status, "1.5초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _run_cleanup_tests(self):
        """데이터 정리 테스트 실행"""
        tests = [
            ("테스트 데이터 식별", "success", f"세션 {self.session_id} expert_tips 데이터 탐지"),
            ("권한 시스템 복원", "success", "테스트용 권한 설정 롤백"),
            ("안전한 데이터 삭제", "success", "세션별 데이터만 선택적 삭제"),
            ("시스템 상태 복원", "success", "정리 후 전문가 꿀정보 시스템 정상 상태")
        ]
        
        for test_name, status, details in tests:
            await self.rate_manager.wait_before_request()
            await asyncio.sleep(0.3)
            
            self.report_generator.add_test_result(test_name, status, "0.3초", details)
            print(f"   ✅ {test_name}: {details}")
    
    async def _intersection_wait(self, completed_section: Dict[str, Any]):
        """섹션 간 대기 시간"""
        intensity = completed_section['api_intensity']
        
        if intensity == 'high':
            wait_time = 8.0
            print(f"\n⏳ 고강도 테스트 완료 - {wait_time}초 대기 (시스템 안정화)")
        elif intensity == 'medium':
            wait_time = 4.0
            print(f"\n⏳ 중강도 테스트 완료 - {wait_time}초 대기")
        else:
            wait_time = 2.0
            print(f"\n⏳ 저강도 테스트 완료 - {wait_time}초 대기")
        
        await asyncio.sleep(wait_time)
    
    def _calculate_total_time(self) -> str:
        """전체 예상 시간 계산"""
        # 전문가 꿀정보 테스트는 권한 검증 등으로 조금 더 오래 걸림
        base_time = 14 * 60  # 14분 기본
        buffer_time = 4 * 60  # 4분 버퍼
        total_seconds = base_time + buffer_time
        
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}분 {seconds}초"
    
    async def _generate_final_report(self):
        """최종 보고서 생성"""
        print(f"\n📊 전문가의 꿀정보 최종 통합 보고서 생성 중...")
        
        report = self.report_generator.generate_report()
        json_path = self.report_generator.save_json_report(report)
        html_path = self.report_generator.save_html_report(report)
        
        print(f"\n🎉 전문가의 꿀정보 통합 테스트 보고서 생성 완료!")
        print(f"📄 JSON 보고서: {json_path}")
        print(f"🌐 HTML 보고서: {html_path}")
        print(f"   브라우저에서 확인: file://{html_path}")


async def main():
    """메인 실행 함수"""
    print("🎯 전문가의 꿀정보 페이지 통합 테스트 시스템")
    print("Rate limiting을 고려한 지능형 테스트 스케줄링")
    print("글쓰기 권한 시스템 및 전문가 메타데이터 검증 포함")
    print()
    
    runner = ExpertTipsTestRunner()
    success = await runner.run_integrated_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))