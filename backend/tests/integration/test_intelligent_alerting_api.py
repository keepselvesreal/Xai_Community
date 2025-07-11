"""
지능형 알림 시스템 API 통합 테스트

알림 규칙 관리, 알림 전송, 알림 이력 조회 등 API 엔드포인트 테스트
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import AsyncMock, patch
import json

from nadle_backend.services.intelligent_alerting import AlertSeverity, AlertChannel, AlertCondition


class TestIntelligentAlertingAPI:
    """지능형 알림 시스템 API 테스트"""

    @pytest.mark.asyncio
    async def test_create_alert_rule(self, async_client: AsyncClient):
        """알림 규칙 생성 API 테스트"""
        # Given: 알림 규칙 생성 데이터
        rule_data = {
            "name": "high_cpu_usage",
            "description": "CPU 사용률이 높을 때 알림",
            "condition": "greater_than",
            "threshold": {
                "metric": "cpu_usage",
                "value": 80.0,
                "duration_minutes": 5
            },
            "severity": "high",
            "channels": ["email", "discord"],
            "cooldown_minutes": 30,
            "enabled": True
        }

        # When: 알림 규칙 생성 요청
        response = await async_client.post("/api/alerts/rules", json=rule_data)

        # Then: 성공 응답
        assert response.status_code == status.HTTP_201_CREATED
        
        response_data = response.json()
        assert response_data["name"] == "high_cpu_usage"
        assert response_data["severity"] == "high"
        assert "email" in response_data["channels"]
        assert "discord" in response_data["channels"]
        assert response_data["enabled"] is True
        assert "id" in response_data

    @pytest.mark.asyncio
    async def test_create_alert_rule_validation_error(self, async_client: AsyncClient):
        """알림 규칙 생성 유효성 검사 오류 테스트"""
        # Given: 잘못된 알림 규칙 데이터
        invalid_rule_data = {
            "name": "",  # 빈 이름
            "condition": "invalid_condition",  # 잘못된 조건
            "threshold": {
                "metric": "cpu_usage",
                "value": -10.0,  # 잘못된 값
            },
            "severity": "invalid_severity",  # 잘못된 심각도
            "channels": []  # 빈 채널 목록
        }

        # When: 잘못된 데이터로 규칙 생성 요청
        response = await async_client.post("/api/alerts/rules", json=invalid_rule_data)

        # Then: 유효성 검사 오류
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_alert_rules(self, async_client: AsyncClient):
        """알림 규칙 목록 조회 API 테스트"""
        # Given: 여러 알림 규칙 생성
        rules_data = [
            {
                "name": "cpu_alert",
                "description": "CPU 알림",
                "condition": "greater_than",
                "threshold": {"metric": "cpu_usage", "value": 80.0},
                "severity": "high",
                "channels": ["email"]
            },
            {
                "name": "memory_alert",
                "description": "메모리 알림",
                "condition": "greater_than",
                "threshold": {"metric": "memory_usage", "value": 90.0},
                "severity": "critical",
                "channels": ["discord"]
            }
        ]

        for rule_data in rules_data:
            await async_client.post("/api/alerts/rules", json=rule_data)

        # When: 알림 규칙 목록 조회
        response = await async_client.get("/api/alerts/rules")

        # Then: 성공 응답과 규칙 목록
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "rules" in response_data
        assert len(response_data["rules"]) >= 2
        
        rule_names = [rule["name"] for rule in response_data["rules"]]
        assert "cpu_alert" in rule_names
        assert "memory_alert" in rule_names

    @pytest.mark.asyncio
    async def test_get_alert_rule_by_name(self, async_client: AsyncClient):
        """이름으로 알림 규칙 조회 API 테스트"""
        # Given: 알림 규칙 생성
        rule_data = {
            "name": "disk_space_alert",
            "description": "디스크 공간 부족 알림",
            "condition": "less_than",
            "threshold": {"metric": "disk_free_space", "value": 10.0},
            "severity": "medium",
            "channels": ["email", "discord"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 특정 규칙 조회
        response = await async_client.get("/api/alerts/rules/disk_space_alert")

        # Then: 성공 응답과 규칙 정보
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["name"] == "disk_space_alert"
        assert response_data["description"] == "디스크 공간 부족 알림"
        assert response_data["condition"] == "less_than"
        assert response_data["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_get_alert_rule_not_found(self, async_client: AsyncClient):
        """존재하지 않는 알림 규칙 조회 테스트"""
        # When: 존재하지 않는 규칙 조회
        response = await async_client.get("/api/alerts/rules/nonexistent_rule")

        # Then: 404 응답
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_alert_rule(self, async_client: AsyncClient):
        """알림 규칙 수정 API 테스트"""
        # Given: 알림 규칙 생성
        rule_data = {
            "name": "network_latency_alert",
            "description": "네트워크 지연 알림",
            "condition": "greater_than",
            "threshold": {"metric": "network_latency", "value": 100.0},
            "severity": "medium",
            "channels": ["email"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 규칙 수정
        updated_data = {
            "description": "네트워크 지연 알림 (수정됨)",
            "threshold": {"metric": "network_latency", "value": 150.0},
            "severity": "high",
            "channels": ["email", "discord"],
            "enabled": False
        }
        
        response = await async_client.put("/api/alerts/rules/network_latency_alert", json=updated_data)

        # Then: 성공 응답과 수정된 내용
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["description"] == "네트워크 지연 알림 (수정됨)"
        assert response_data["threshold"]["value"] == 150.0
        assert response_data["severity"] == "high"
        assert "discord" in response_data["channels"]
        assert response_data["enabled"] is False

    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, async_client: AsyncClient):
        """알림 규칙 삭제 API 테스트"""
        # Given: 알림 규칙 생성
        rule_data = {
            "name": "temp_alert_rule",
            "description": "임시 알림 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "temperature", "value": 70.0},
            "severity": "low",
            "channels": ["email"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 규칙 삭제
        response = await async_client.delete("/api/alerts/rules/temp_alert_rule")

        # Then: 성공 응답
        assert response.status_code == status.HTTP_200_OK
        
        # 삭제 확인
        get_response = await async_client.get("/api/alerts/rules/temp_alert_rule")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @patch('nadle_backend.services.intelligent_alerting.IntelligentAlertingService.evaluate_rule')
    async def test_evaluate_alert_rules(self, mock_evaluate, async_client: AsyncClient):
        """알림 규칙 평가 API 테스트"""
        # Given: Mock 평가 결과
        mock_evaluate.return_value = True

        # 알림 규칙 생성
        rule_data = {
            "name": "test_evaluation_rule",
            "description": "평가 테스트 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "test_metric", "value": 50.0},
            "severity": "medium",
            "channels": ["email"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 모든 규칙 평가 요청
        response = await async_client.post("/api/alerts/evaluate")

        # Then: 성공 응답과 평가 결과
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "evaluation_results" in response_data
        assert len(response_data["evaluation_results"]) >= 1
        
        # 평가 결과 확인
        for result in response_data["evaluation_results"]:
            assert "rule_name" in result
            assert "should_alert" in result
            assert "evaluated_at" in result

    @pytest.mark.asyncio
    @patch('nadle_backend.services.intelligent_alerting.IntelligentAlertingService.send_alert')
    async def test_send_manual_alert(self, mock_send_alert, async_client: AsyncClient):
        """수동 알림 전송 API 테스트"""
        # Given: Mock 알림 전송 결과
        mock_send_alert.return_value = {"email": True, "discord": True}

        # 알림 규칙 생성
        rule_data = {
            "name": "manual_test_rule",
            "description": "수동 테스트 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "test_metric", "value": 75.0},
            "severity": "high",
            "channels": ["email", "discord"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 수동 알림 전송 요청
        alert_data = {
            "rule_name": "manual_test_rule",
            "metric_data": {
                "metric_value": 85.0,
                "additional_info": "Manual test alert"
            }
        }
        
        response = await async_client.post("/api/alerts/send", json=alert_data)

        # Then: 성공 응답과 전송 결과
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["email"] is True
        assert response_data["discord"] is True
        
        # Mock 함수 호출 확인
        mock_send_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_alert_history(self, async_client: AsyncClient):
        """알림 이력 조회 API 테스트"""
        # Given: 알림 규칙과 이력 생성을 위한 설정
        rule_data = {
            "name": "history_test_rule",
            "description": "이력 테스트 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "test_metric", "value": 60.0},
            "severity": "medium",
            "channels": ["email"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 알림 이력 조회
        response = await async_client.get("/api/alerts/history/history_test_rule")

        # Then: 성공 응답 (이력이 없어도 빈 목록 반환)
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "history" in response_data
        assert isinstance(response_data["history"], list)

    @pytest.mark.asyncio
    async def test_get_alert_history_with_params(self, async_client: AsyncClient):
        """알림 이력 조회 (파라미터 포함) API 테스트"""
        # Given: 알림 규칙 생성
        rule_data = {
            "name": "param_history_rule",
            "description": "파라미터 이력 테스트 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "test_metric", "value": 70.0},
            "severity": "high",
            "channels": ["discord"]
        }
        
        create_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # When: 파라미터와 함께 알림 이력 조회
        params = {"hours": 48, "limit": 50}
        response = await async_client.get("/api/alerts/history/param_history_rule", params=params)

        # Then: 성공 응답
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "history" in response_data
        assert "rule_name" in response_data
        assert response_data["rule_name"] == "param_history_rule"

    @pytest.mark.asyncio
    async def test_get_alert_statistics(self, async_client: AsyncClient):
        """알림 통계 조회 API 테스트"""
        # When: 알림 통계 조회
        response = await async_client.get("/api/alerts/statistics")

        # Then: 성공 응답과 통계 정보
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "total_rules" in response_data
        assert "active_rules" in response_data
        assert "alerts_sent_today" in response_data
        assert "alerts_by_severity" in response_data
        assert "alerts_by_channel" in response_data

    @pytest.mark.asyncio
    async def test_alert_rule_name_uniqueness(self, async_client: AsyncClient):
        """알림 규칙 이름 중복 방지 테스트"""
        # Given: 첫 번째 알림 규칙 생성
        rule_data = {
            "name": "unique_test_rule",
            "description": "첫 번째 규칙",
            "condition": "greater_than",
            "threshold": {"metric": "test_metric", "value": 50.0},
            "severity": "medium",
            "channels": ["email"]
        }
        
        first_response = await async_client.post("/api/alerts/rules", json=rule_data)
        assert first_response.status_code == status.HTTP_201_CREATED

        # When: 같은 이름으로 두 번째 규칙 생성 시도
        duplicate_rule_data = {
            "name": "unique_test_rule",  # 중복된 이름
            "description": "두 번째 규칙",
            "condition": "less_than",
            "threshold": {"metric": "other_metric", "value": 30.0},
            "severity": "low",
            "channels": ["discord"]
        }
        
        second_response = await async_client.post("/api/alerts/rules", json=duplicate_rule_data)

        # Then: 중복 오류
        assert second_response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_alert_suppression(self, async_client: AsyncClient):
        """알림 억제 설정 API 테스트"""
        # Given: 억제 규칙 데이터
        suppression_data = {
            "type": "maintenance_window",
            "name": "weekend_maintenance",
            "start_time": "2024-12-21T02:00:00Z",
            "end_time": "2024-12-21T06:00:00Z",
            "affected_services": ["api", "database"],
            "description": "주말 유지보수"
        }

        # When: 알림 억제 규칙 생성
        response = await async_client.post("/api/alerts/suppression", json=suppression_data)

        # Then: 성공 응답
        assert response.status_code == status.HTTP_201_CREATED
        
        response_data = response.json()
        assert response_data["name"] == "weekend_maintenance"
        assert response_data["type"] == "maintenance_window"
        assert "api" in response_data["affected_services"]

    @pytest.mark.asyncio
    async def test_get_suppression_rules(self, async_client: AsyncClient):
        """알림 억제 규칙 목록 조회 API 테스트"""
        # When: 억제 규칙 목록 조회
        response = await async_client.get("/api/alerts/suppression")

        # Then: 성공 응답
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "suppression_rules" in response_data
        assert isinstance(response_data["suppression_rules"], list)

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """알림 시스템 헬스체크 API 테스트"""
        # When: 헬스체크 요청
        response = await async_client.get("/api/alerts/health")

        # Then: 성공 응답과 상태 정보
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "status" in response_data
        assert "services" in response_data
        assert "last_check" in response_data
        
        # 서비스 상태 확인
        services = response_data["services"]
        assert "notification_service" in services
        assert "monitoring_service" in services
        assert "rule_engine" in services


class TestAlertingAPIErrorHandling:
    """알림 API 에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_invalid_json_format(self, async_client: AsyncClient):
        """잘못된 JSON 형식 처리 테스트"""
        # When: 잘못된 JSON으로 요청
        response = await async_client.post(
            "/api/alerts/rules",
            content="invalid json content",
            headers={"Content-Type": "application/json"}
        )

        # Then: JSON 파싱 오류
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """필수 필드 누락 처리 테스트"""
        # Given: 필수 필드가 누락된 데이터
        incomplete_data = {
            "description": "불완전한 규칙"
            # name, condition, threshold 등 필수 필드 누락
        }

        # When: 불완전한 데이터로 요청
        response = await async_client.post("/api/alerts/rules", json=incomplete_data)

        # Then: 유효성 검사 오류
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        error_detail = response.json()["detail"]
        assert any("name" in str(error) for error in error_detail)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """인증되지 않은 접근 처리 테스트 (향후 인증 구현 시)"""
        # NOTE: 현재는 인증이 구현되어 있지 않으므로 스킵
        # 향후 인증 시스템 구현 시 활성화
        pass

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client: AsyncClient):
        """API 요청 제한 처리 테스트 (향후 구현 시)"""
        # NOTE: 현재는 요청 제한이 구현되어 있지 않으므로 스킵
        # 향후 요청 제한 시스템 구현 시 활성화
        pass