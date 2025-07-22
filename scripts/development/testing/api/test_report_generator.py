#!/usr/bin/env python3
"""
테스트 보고서 생성기
- 테스트 결과를 수집하고 JSON 및 HTML 보고서 생성
- 실시간 테스트 진행 상황 추적
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TestResult:
    """개별 테스트 결과"""
    name: str
    status: str  # success, warning, danger
    duration: str
    details: str
    error: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass 
class TestSection:
    """테스트 섹션 (예: 게시글 CRUD, 댓글 시스템 등)"""
    name: str
    status: str  # success, warning, danger
    tests: List[TestResult]
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class TestMetadata:
    """테스트 메타데이터"""
    session_id: str
    start_time: str
    end_time: Optional[str]
    duration: Optional[str]
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    environment: str
    api_base_url: str


@dataclass
class TestDataSummary:
    """생성된 테스트 데이터 요약"""
    type: str
    count: int
    pattern: str


@dataclass
class TestReport:
    """전체 테스트 보고서"""
    metadata: TestMetadata
    sections: List[TestSection]
    test_data: List[TestDataSummary]
    generated_data: Dict[str, Any]


class TestReportGenerator:
    """테스트 보고서 생성기"""
    
    def __init__(self, session_id: str = None, environment: str = "development"):
        self.session_id = session_id or self._generate_session_id()
        self.environment = environment
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5173"
        
        self.start_time = datetime.now()
        self.sections: List[TestSection] = []
        self.current_section: Optional[TestSection] = None
        self.generated_data = {
            "posts": [],
            "comments": [],
            "users": [],
            "reactions": []
        }
        
        # 보고서 파일 경로
        self.report_dir = Path(__file__).parent / "reports"
        self.report_dir.mkdir(exist_ok=True)
        
        print(f"📊 테스트 보고서 생성기 초기화")
        print(f"🆔 세션 ID: {self.session_id}")
        print(f"📁 보고서 디렉토리: {self.report_dir}")
    
    def _generate_session_id(self) -> str:
        """세션 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = uuid.uuid4().hex[:4].upper()
        return f"REPORT_{timestamp}_{random_suffix}"
    
    def start_section(self, section_name: str) -> None:
        """테스트 섹션 시작"""
        print(f"\n🚀 테스트 섹션 시작: {section_name}")
        
        if self.current_section:
            self.end_section()
        
        self.current_section = TestSection(
            name=section_name,
            status="success",  # 기본값, 나중에 업데이트
            tests=[],
            start_time=datetime.now().isoformat()
        )
    
    def end_section(self) -> None:
        """현재 테스트 섹션 종료"""
        if not self.current_section:
            return
        
        self.current_section.end_time = datetime.now().isoformat()
        
        # 섹션 상태 결정 (테스트 결과를 기반으로)
        has_danger = any(test.status == "danger" for test in self.current_section.tests)
        has_warning = any(test.status == "warning" for test in self.current_section.tests)
        
        if has_danger:
            self.current_section.status = "danger"
        elif has_warning:
            self.current_section.status = "warning"
        else:
            self.current_section.status = "success"
        
        self.sections.append(self.current_section)
        
        test_count = len(self.current_section.tests)
        success_count = len([t for t in self.current_section.tests if t.status == "success"])
        
        print(f"✅ 테스트 섹션 완료: {self.current_section.name}")
        print(f"   📊 결과: {success_count}/{test_count} 성공, 상태: {self.current_section.status}")
        
        self.current_section = None
    
    def add_test_result(self, name: str, status: str, duration: str, details: str, error: str = None) -> None:
        """테스트 결과 추가"""
        if not self.current_section:
            raise ValueError("테스트 섹션이 시작되지 않았습니다. start_section()을 먼저 호출하세요.")
        
        test_result = TestResult(
            name=name,
            status=status,
            duration=duration,
            details=details,
            error=error,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_section.tests.append(test_result)
        
        # 상태별 이모지
        status_emoji = {
            "success": "✅",
            "warning": "⚠️", 
            "danger": "❌"
        }
        
        print(f"  {status_emoji.get(status, '🔍')} {name}: {details} ({duration})")
        if error:
            print(f"    ❌ 오류: {error}")
    
    def add_generated_data(self, data_type: str, item: Dict[str, Any]) -> None:
        """생성된 테스트 데이터 추가"""
        if data_type not in self.generated_data:
            self.generated_data[data_type] = []
        
        self.generated_data[data_type].append({
            **item,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        })
    
    def generate_report(self) -> TestReport:
        """최종 테스트 보고서 생성"""
        # 현재 섹션이 있다면 종료
        if self.current_section:
            self.end_section()
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # 통계 계산
        total_tests = sum(len(section.tests) for section in self.sections)
        passed_tests = sum(len([t for t in section.tests if t.status == "success"]) for section in self.sections)
        warning_tests = sum(len([t for t in section.tests if t.status == "warning"]) for section in self.sections)
        failed_tests = sum(len([t for t in section.tests if t.status == "danger"]) for section in self.sections)
        
        # 메타데이터 생성
        metadata = TestMetadata(
            session_id=self.session_id,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=self._format_duration(duration.total_seconds()),
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            warning_tests=warning_tests,
            environment=self.environment,
            api_base_url=self.api_base_url
        )
        
        # 테스트 데이터 요약 생성
        test_data_summary = []
        for data_type, items in self.generated_data.items():
            if items:
                test_data_summary.append(TestDataSummary(
                    type=data_type,
                    count=len(items),
                    pattern=self._get_data_pattern(data_type)
                ))
        
        report = TestReport(
            metadata=metadata,
            sections=self.sections,
            test_data=test_data_summary,
            generated_data=self.generated_data
        )
        
        print(f"\n📊 테스트 보고서 생성 완료")
        print(f"   🎯 총 테스트: {total_tests}")
        print(f"   ✅ 성공: {passed_tests}")
        print(f"   ⚠️ 경고: {warning_tests}")
        print(f"   ❌ 실패: {failed_tests}")
        print(f"   ⏱️ 소요 시간: {metadata.duration}")
        
        return report
    
    def save_json_report(self, report: TestReport) -> str:
        """JSON 보고서 파일 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_report_{timestamp}_{self.session_id.split('_')[-1]}.json"
        filepath = self.report_dir / filename
        
        # 직렬화 가능한 딕셔너리로 변환
        report_dict = asdict(report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON 보고서 저장: {filepath}")
        return str(filepath)
    
    def save_html_report(self, report: TestReport) -> str:
        """HTML 보고서 파일 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_report_{timestamp}_{self.session_id.split('_')[-1]}.html"
        filepath = self.report_dir / filename
        
        # HTML 템플릿 로드
        template_path = Path(__file__).parent / "board_test_report_template.html"
        if not template_path.exists():
            raise FileNotFoundError(f"HTML 템플릿 파일을 찾을 수 없습니다: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 보고서 데이터를 JavaScript로 삽입
        report_dict = asdict(report)
        json_data = json.dumps(report_dict, ensure_ascii=False, indent=2)
        
        # fetchTestData 함수에 실제 데이터 삽입
        # 함수 시작과 끝을 정확히 찾아서 교체
        function_start = 'async function fetchTestData() {'
        function_end_pattern = '        }'
        
        start_idx = template_content.find(function_start)
        if start_idx != -1:
            # 함수 내용 시작점 찾기
            content_start = template_content.find('{', start_idx) + 1
            
            # 함수 끝점 찾기 (올바른 indentation의 closing brace)
            brace_count = 1
            current_pos = content_start
            
            while current_pos < len(template_content) and brace_count > 0:
                char = template_content[current_pos]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                current_pos += 1
            
            if brace_count == 0:
                content_end = current_pos - 1
                before = template_content[:content_start]
                after = template_content[content_end:]
                
                updated_content = before + f'''
            // 실제 테스트 결과 데이터
            return {json_data};
        ''' + after
            else:
                updated_content = template_content
        else:
            updated_content = template_content
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"🌐 HTML 보고서 저장: {filepath}")
        print(f"   🔗 브라우저에서 확인: file://{filepath.absolute()}")
        
        return str(filepath)
    
    def _format_duration(self, seconds: float) -> str:
        """초를 읽기 쉬운 형태로 변환"""
        if seconds < 60:
            return f"{seconds:.1f}초"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}분 {remaining_seconds}초"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}시간 {minutes}분"
    
    def _get_data_pattern(self, data_type: str) -> str:
        """데이터 타입별 패턴 반환"""
        patterns = {
            "posts": f"[TEST-{self.session_id}] 게시글 제목",
            "comments": f"테스트 댓글 (세션: {self.session_id})",
            "users": f"testuser_{self.session_id.split('_')[-1].lower()}",
            "reactions": "반응 데이터"
        }
        return patterns.get(data_type, f"{data_type} 데이터")


# 편의 함수들
def create_test_report(session_id: str = None) -> TestReportGenerator:
    """테스트 보고서 생성기 인스턴스 생성"""
    return TestReportGenerator(session_id)


def demo_report():
    """데모 보고서 생성"""
    print("🎯 데모 테스트 보고서 생성 중...")
    
    generator = create_test_report()
    
    # 게시글 목록 기능 테스트
    generator.start_section("게시글 목록 기능")
    generator.add_test_result("기본 목록 조회", "success", "0.8초", "20개 게시글 정상 조회")
    generator.add_test_result("페이지네이션", "success", "0.6초", "5페이지 정상 동작")
    generator.add_test_result("카테고리 필터", "success", "0.7초", "3개 카테고리 필터링 성공")
    generator.add_test_result("검색 기능", "warning", "1.2초", "한글 검색 일부 이슈")
    
    # 게시글 CRUD 테스트
    generator.start_section("게시글 CRUD")
    generator.add_test_result("게시글 생성", "success", "1.1초", "마크다운 콘텐츠 정상 생성")
    generator.add_test_result("게시글 조회", "success", "0.5초", "조회수 정상 증가")
    generator.add_test_result("게시글 수정", "success", "0.9초", "메타데이터 포함 수정 성공")
    generator.add_test_result("게시글 삭제", "success", "0.4초", "soft delete 정상 동작")
    
    # 생성된 테스트 데이터 추가
    for i in range(5):
        generator.add_generated_data("posts", {
            "id": f"post_{i+1}",
            "title": f"테스트 게시글 {i+1}",
            "slug": f"test-post-{i+1}"
        })
    
    for i in range(10):
        generator.add_generated_data("comments", {
            "id": f"comment_{i+1}",
            "content": f"테스트 댓글 {i+1}",
            "post_id": f"post_{(i//2)+1}"
        })
    
    # 보고서 생성 및 저장
    report = generator.generate_report()
    json_path = generator.save_json_report(report)
    html_path = generator.save_html_report(report)
    
    print(f"\n🎉 데모 보고서 생성 완료!")
    print(f"📄 JSON: {json_path}")
    print(f"🌐 HTML: {html_path}")
    
    return json_path, html_path


if __name__ == "__main__":
    demo_report()