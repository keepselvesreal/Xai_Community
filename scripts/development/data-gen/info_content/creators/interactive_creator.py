"""
인터렉티브 차트 콘텐츠 생성기

사용자가 직접 조작 가능한 차트를 포함한 콘텐츠를 생성합니다.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from scripts.info_content.base_creator import BaseContentCreator
from scripts.info_content.content_types import InfoContent, ContentType, InfoCategory


class InteractiveChartCreator(BaseContentCreator):
    """인터렉티브 차트 콘텐츠 생성기"""
    
    async def create_content(
        self,
        title: str = None,
        category: InfoCategory = InfoCategory.MARKET_ANALYSIS,
        chart_type: str = "line",
        data_source: str = None,
        tags: List[str] = None,
        **kwargs
    ) -> InfoContent:
        """인터렉티브 차트 콘텐츠 생성"""
        
        # 기본값 설정
        if not title:
            title = self._get_default_title(category, chart_type)
        
        if not data_source:
            data_source = self._get_default_data_source(category)
        
        if not tags:
            base_tags = self.get_default_tags(category)
            # 최대 3개 태그 제한을 위해 기본 태그 1개 + 차트 관련 태그 2개
            tags = base_tags[:1] + ["차트", "인터렉티브"]
        
        # 차트 설정 생성
        chart_config = self._generate_chart_config(category, chart_type)
        
        # HTML 콘텐츠 생성
        content = self._generate_interactive_content(category, chart_type, chart_config)
        
        # 요약 생성
        summary = self._generate_summary(category, chart_type)
        
        # 메타데이터 생성
        metadata = self.create_metadata(
            category=category,
            content_type=ContentType.INTERACTIVE_CHART,
            tags=tags,
            summary=summary,
            data_source=data_source,
            chart_config=chart_config
        )
        
        # InfoContent 객체 생성
        info_content = InfoContent(
            title=title,
            content=content,
            slug=self.generate_slug(title),
            author_id=self.admin_user_id,
            content_type=ContentType.INTERACTIVE_CHART,
            metadata=metadata
        )
        
        # 유효성 검사
        self.validate_content(info_content)
        
        return info_content
    
    def _get_default_title(self, category: InfoCategory, chart_type: str) -> str:
        """카테고리별 기본 제목 반환"""
        titles = {
            InfoCategory.MARKET_ANALYSIS: f"아파트 시세 동향 {chart_type.upper()} 차트",
            InfoCategory.LEGAL_INFO: f"계약 유형별 분포 {chart_type.upper()} 차트", 
            InfoCategory.MOVE_IN_GUIDE: f"입주 절차 진행률 {chart_type.upper()} 차트",
            InfoCategory.INVESTMENT_TREND: f"투자 수익률 비교 {chart_type.upper()} 차트"
        }
        return titles.get(category, f"부동산 데이터 {chart_type.upper()} 차트")
    
    def _get_default_data_source(self, category: InfoCategory) -> str:
        """카테고리별 기본 데이터 소스 반환"""
        sources = {
            InfoCategory.MARKET_ANALYSIS: "KB부동산, 부동산114",
            InfoCategory.LEGAL_INFO: "법무부, 국토교통부",
            InfoCategory.MOVE_IN_GUIDE: "LH공사, 한국부동산원",
            InfoCategory.INVESTMENT_TREND: "한국은행, 금융감독원"
        }
        return sources.get(category, "공공기관")
    
    def _generate_chart_config(self, category: InfoCategory, chart_type: str) -> Dict[str, Any]:
        """차트 설정 생성"""
        base_config = {
            "type": chart_type,
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": self._get_chart_title(category)
                },
                "legend": {
                    "display": True,
                    "position": "bottom"
                }
            },
            "scales": {
                "x": {
                    "display": True,
                    "title": {
                        "display": True,
                        "text": self._get_x_axis_label(category)
                    }
                },
                "y": {
                    "display": True,
                    "title": {
                        "display": True,
                        "text": self._get_y_axis_label(category)
                    }
                }
            }
        }
        
        # 카테고리별 데이터 생성
        base_config["data"] = self._generate_chart_data(category, chart_type)
        
        return base_config
    
    def _get_chart_title(self, category: InfoCategory) -> str:
        """차트 제목 반환"""
        titles = {
            InfoCategory.MARKET_ANALYSIS: "아파트 시세 월별 변동 추이",
            InfoCategory.LEGAL_INFO: "계약 유형별 분포 현황",
            InfoCategory.MOVE_IN_GUIDE: "입주 절차별 소요 시간",
            InfoCategory.INVESTMENT_TREND: "투자 상품별 수익률 비교"
        }
        return titles.get(category, "부동산 데이터 차트")
    
    def _get_x_axis_label(self, category: InfoCategory) -> str:
        """X축 라벨 반환"""
        labels = {
            InfoCategory.MARKET_ANALYSIS: "월",
            InfoCategory.LEGAL_INFO: "계약 유형",
            InfoCategory.MOVE_IN_GUIDE: "절차 단계",
            InfoCategory.INVESTMENT_TREND: "투자 상품"
        }
        return labels.get(category, "구분")
    
    def _get_y_axis_label(self, category: InfoCategory) -> str:
        """Y축 라벨 반환"""
        labels = {
            InfoCategory.MARKET_ANALYSIS: "가격 (만원)",
            InfoCategory.LEGAL_INFO: "비율 (%)",
            InfoCategory.MOVE_IN_GUIDE: "소요 시간 (일)",
            InfoCategory.INVESTMENT_TREND: "수익률 (%)"
        }
        return labels.get(category, "값")
    
    def _generate_chart_data(self, category: InfoCategory, chart_type: str) -> Dict[str, Any]:
        """차트 데이터 생성"""
        if category == InfoCategory.MARKET_ANALYSIS:
            return {
                "labels": ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"],
                "datasets": [
                    {
                        "label": "강남구",
                        "data": [95000, 96200, 97100, 98500, 99200, 100100, 101500, 102200, 103100, 104000, 104800, 105500],
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "tension": 0.1
                    },
                    {
                        "label": "서초구", 
                        "data": [87000, 88100, 89200, 90500, 91200, 92100, 93500, 94200, 95100, 96000, 96800, 97500],
                        "borderColor": "rgb(255, 99, 132)",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "tension": 0.1
                    }
                ]
            }
        elif category == InfoCategory.LEGAL_INFO:
            return {
                "labels": ["전세", "월세", "매매", "단기임대"],
                "datasets": [
                    {
                        "label": "계약 유형별 비율",
                        "data": [45, 35, 15, 5],
                        "backgroundColor": [
                            "rgba(255, 99, 132, 0.8)",
                            "rgba(54, 162, 235, 0.8)",
                            "rgba(255, 205, 86, 0.8)",
                            "rgba(75, 192, 192, 0.8)"
                        ]
                    }
                ]
            }
        elif category == InfoCategory.MOVE_IN_GUIDE:
            return {
                "labels": ["서류준비", "계약체결", "입주신고", "공과금신청", "이사", "정착"],
                "datasets": [
                    {
                        "label": "평균 소요 시간 (일)",
                        "data": [3, 1, 1, 2, 1, 7],
                        "backgroundColor": "rgba(54, 162, 235, 0.8)",
                        "borderColor": "rgb(54, 162, 235)",
                        "borderWidth": 1
                    }
                ]
            }
        else:  # INVESTMENT_TREND
            return {
                "labels": ["아파트", "오피스텔", "상가", "토지", "REITs"],
                "datasets": [
                    {
                        "label": "2023년 수익률 (%)",
                        "data": [8.5, 6.2, 12.1, 15.3, 7.8],
                        "backgroundColor": "rgba(255, 159, 64, 0.8)",
                        "borderColor": "rgb(255, 159, 64)",
                        "borderWidth": 1
                    },
                    {
                        "label": "2024년 예상 수익률 (%)",
                        "data": [7.2, 5.8, 10.5, 12.1, 8.5],
                        "backgroundColor": "rgba(153, 102, 255, 0.8)",
                        "borderColor": "rgb(153, 102, 255)",
                        "borderWidth": 1
                    }
                ]
            }
    
    def _generate_interactive_content(self, category: InfoCategory, chart_type: str, chart_config: Dict[str, Any]) -> str:
        """인터렉티브 HTML 콘텐츠 생성"""
        chart_data_json = json.dumps(chart_config, ensure_ascii=False, indent=2)
        
        html_content = f"""
<div class="interactive-chart-container">
    <div class="chart-header">
        <h2>{self._get_chart_title(category)}</h2>
        <p class="chart-description">{self._get_chart_description(category)}</p>
    </div>
    
    <div class="chart-controls">
        <button onclick="resetZoom()" class="btn btn-secondary">줌 리셋</button>
        <button onclick="downloadChart()" class="btn btn-primary">차트 다운로드</button>
    </div>
    
    <div class="chart-wrapper">
        <canvas id="interactiveChart" width="800" height="400"></canvas>
    </div>
    
    <div class="chart-info">
        <h3>차트 조작 방법</h3>
        <ul>
            <li><strong>줌</strong>: 마우스 휠 또는 드래그하여 확대/축소</li>
            <li><strong>패닝</strong>: 차트를 드래그하여 이동</li>
            <li><strong>범례</strong>: 클릭하여 데이터 시리즈 표시/숨김</li>
            <li><strong>툴팁</strong>: 데이터 포인트에 마우스 오버</li>
        </ul>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>

<script>
const chartConfig = {chart_data_json};

// Chart.js 차트 생성
const ctx = document.getElementById('interactiveChart').getContext('2d');
const chart = new Chart(ctx, {{
    ...chartConfig,
    plugins: [ChartZoom],
    options: {{
        ...chartConfig.options,
        plugins: {{
            ...chartConfig.plugins,
            zoom: {{
                zoom: {{
                    wheel: {{
                        enabled: true,
                    }},
                    pinch: {{
                        enabled: true
                    }},
                    mode: 'xy',
                }},
                pan: {{
                    enabled: true,
                    mode: 'xy',
                }}
            }}
        }},
        interaction: {{
            intersect: false,
            mode: 'index'
        }},
        onHover: (event, activeElements) => {{
            event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
        }}
    }}
}});

// 유틸리티 함수들
function resetZoom() {{
    chart.resetZoom();
}}

function downloadChart() {{
    const link = document.createElement('a');
    link.download = 'chart.png';
    link.href = chart.toBase64Image();
    link.click();
}}

// 차트 데이터 업데이트 함수 (필요시 사용)
function updateChartData(newData) {{
    chart.data = newData;
    chart.update();
}}
</script>

<style>
.interactive-chart-container {{
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

.chart-header {{
    text-align: center;
    margin-bottom: 20px;
}}

.chart-header h2 {{
    color: #333;
    margin-bottom: 10px;
}}

.chart-description {{
    color: #666;
    font-size: 14px;
}}

.chart-controls {{
    text-align: center;
    margin-bottom: 20px;
}}

.btn {{
    padding: 8px 16px;
    margin: 0 5px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}}

.btn-primary {{
    background-color: #007bff;
    color: white;
}}

.btn-secondary {{
    background-color: #6c757d;
    color: white;
}}

.btn:hover {{
    opacity: 0.9;
}}

.chart-wrapper {{
    position: relative;
    margin-bottom: 20px;
}}

.chart-info {{
    background: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
}}

.chart-info h3 {{
    margin-top: 0;
    color: #333;
}}

.chart-info ul {{
    margin-bottom: 0;
    padding-left: 20px;
}}

.chart-info li {{
    margin-bottom: 5px;
    color: #666;
}}
</style>
        """
        
        return html_content
    
    def _get_chart_description(self, category: InfoCategory) -> str:
        """차트 설명 반환"""
        descriptions = {
            InfoCategory.MARKET_ANALYSIS: "지역별 아파트 시세 변동을 월별로 추적할 수 있는 인터렉티브 차트입니다.",
            InfoCategory.LEGAL_INFO: "부동산 계약 유형별 비율을 시각화한 차트입니다.",
            InfoCategory.MOVE_IN_GUIDE: "입주 절차별 평균 소요 시간을 확인할 수 있습니다.",
            InfoCategory.INVESTMENT_TREND: "부동산 투자 상품별 수익률을 비교 분석할 수 있습니다."
        }
        return descriptions.get(category, "부동산 관련 데이터를 시각화한 인터렉티브 차트입니다.")
    
    def _generate_summary(self, category: InfoCategory, chart_type: str) -> str:
        """콘텐츠 요약 생성"""
        summaries = {
            InfoCategory.MARKET_ANALYSIS: f"부동산 시세 데이터를 {chart_type} 차트로 시각화하여 동향을 분석할 수 있습니다.",
            InfoCategory.LEGAL_INFO: f"계약 관련 데이터를 {chart_type} 차트로 표현한 인터렉티브 시각화입니다.",
            InfoCategory.MOVE_IN_GUIDE: f"입주 절차를 {chart_type} 차트로 시각화하여 이해를 돕습니다.",
            InfoCategory.INVESTMENT_TREND: f"투자 상품별 데이터를 {chart_type} 차트로 비교 분석할 수 있습니다."
        }
        return summaries.get(category, f"부동산 데이터를 {chart_type} 차트로 시각화한 인터렉티브 콘텐츠입니다.")