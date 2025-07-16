# 통합 알림 시스템 API 사용 예시

## 🔧 기본 설정

### 환경 변수
```bash
# .env 파일에 추가
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
```

### 서비스 시작
```bash
cd backend
uv run python main.py
```

## 📊 실제 사용 시나리오

### 1. 웹 서비스 모니터링 설정

#### CPU 사용률 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cpu_usage_high",
    "description": "CPU 사용률이 80% 이상 5분 지속",
    "condition": "greater_than",
    "threshold": {
      "metric": "cpu_usage",
      "value": 80.0,
      "duration_minutes": 5
    },
    "severity": "high",
    "channels": ["email", "discord"],
    "cooldown_minutes": 30,
    "escalation_minutes": 60,
    "enabled": true,
    "tags": {
      "service": "web-server",
      "environment": "production"
    }
  }'
```

#### 메모리 사용률 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "memory_usage_critical",
    "description": "메모리 사용률 90% 이상",
    "condition": "greater_than",
    "threshold": {
      "metric": "memory_usage",
      "value": 90.0,
      "duration_minutes": 2
    },
    "severity": "critical",
    "channels": ["email", "discord"],
    "cooldown_minutes": 15,
    "escalation_minutes": 30,
    "enabled": true
  }'
```

#### 디스크 공간 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "disk_space_low",
    "description": "디스크 여유 공간 10% 미만",
    "condition": "less_than",
    "threshold": {
      "metric": "disk_free_percent",
      "value": 10.0,
      "duration_minutes": 1
    },
    "severity": "critical",
    "channels": ["email", "discord"],
    "cooldown_minutes": 60,
    "escalation_minutes": 120,
    "enabled": true
  }'
```

### 2. API 성능 모니터링

#### 응답 시간 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api_response_slow",
    "description": "API 응답 시간 2초 초과",
    "condition": "greater_than",
    "threshold": {
      "metric": "response_time_ms",
      "value": 2000.0,
      "duration_minutes": 3
    },
    "severity": "medium",
    "channels": ["discord"],
    "cooldown_minutes": 15,
    "enabled": true
  }'
```

#### 에러율 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "error_rate_high",
    "description": "에러율 5% 이상",
    "condition": "greater_than",
    "threshold": {
      "metric": "error_rate",
      "value": 5.0,
      "duration_minutes": 2
    },
    "severity": "high",
    "channels": ["email", "discord"],
    "cooldown_minutes": 20,
    "enabled": true
  }'
```

### 3. 데이터베이스 모니터링

#### 연결 수 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "db_connections_high",
    "description": "데이터베이스 연결 수 100개 이상",
    "condition": "greater_than",
    "threshold": {
      "metric": "db_connections",
      "value": 100.0,
      "duration_minutes": 5
    },
    "severity": "medium",
    "channels": ["discord"],
    "cooldown_minutes": 30,
    "enabled": true
  }'
```

#### 쿼리 실행 시간 모니터링
```bash
curl -X POST "http://localhost:8000/api/alerts/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "slow_query_detected",
    "description": "느린 쿼리 감지 (5초 이상)",
    "condition": "greater_than",
    "threshold": {
      "metric": "query_execution_time",
      "value": 5000.0,
      "duration_minutes": 1
    },
    "severity": "high",
    "channels": ["email", "discord"],
    "cooldown_minutes": 10,
    "enabled": true
  }'
```

## 🔄 알림 관리 작업

### 1. 규칙 목록 조회
```bash
# 모든 규칙 조회
curl -X GET "http://localhost:8000/api/alerts/rules"

# 활성화된 규칙만 조회
curl -X GET "http://localhost:8000/api/alerts/rules?enabled=true"

# 특정 심각도 규칙 조회
curl -X GET "http://localhost:8000/api/alerts/rules?severity=high"

# 조건부 조회
curl -X GET "http://localhost:8000/api/alerts/rules?enabled=true&severity=critical"
```

### 2. 특정 규칙 조회
```bash
curl -X GET "http://localhost:8000/api/alerts/rules/cpu_usage_high"
```

### 3. 규칙 수정
```bash
# CPU 사용률 임계값 변경
curl -X PUT "http://localhost:8000/api/alerts/rules/cpu_usage_high" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": {
      "metric": "cpu_usage",
      "value": 85.0,
      "duration_minutes": 3
    },
    "severity": "critical",
    "cooldown_minutes": 20
  }'
```

### 4. 규칙 삭제
```bash
curl -X DELETE "http://localhost:8000/api/alerts/rules/cpu_usage_high"
```

## 📊 알림 평가 및 전송

### 1. 모든 활성 규칙 평가
```bash
curl -X POST "http://localhost:8000/api/alerts/evaluate" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 2. 특정 규칙들만 평가
```bash
curl -X POST "http://localhost:8000/api/alerts/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_names": ["cpu_usage_high", "memory_usage_critical"]
  }'
```

### 3. 수동 알림 전송
```bash
curl -X POST "http://localhost:8000/api/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "cpu_usage_high",
    "metric_data": {
      "metric_value": 85.0,
      "additional_info": "CPU 사용률이 85%에 도달했습니다. 서버 확인이 필요합니다.",
      "server_info": {
        "hostname": "web-server-01",
        "ip": "192.168.1.100"
      }
    }
  }'
```

## 📈 모니터링 및 분석

### 1. 알림 이력 조회
```bash
# 24시간 이력 조회
curl -X GET "http://localhost:8000/api/alerts/history/cpu_usage_high"

# 48시간 이력 조회
curl -X GET "http://localhost:8000/api/alerts/history/cpu_usage_high?hours=48"
```

### 2. 알림 통계 조회
```bash
curl -X GET "http://localhost:8000/api/alerts/statistics"
```

**응답 예시:**
```json
{
  "total_rules": 6,
  "active_rules": 5,
  "total_alerts": 23,
  "alerts_sent_today": 8,
  "alerts_by_severity": {
    "low": 2,
    "medium": 8,
    "high": 10,
    "critical": 3
  },
  "alerts_by_channel": {
    "email": 15,
    "discord": 23
  },
  "alert_rate_per_hour": 1.2
}
```

### 3. 시스템 헬스체크
```bash
curl -X GET "http://localhost:8000/api/alerts/health"
```

## 🔗 외부 시스템 연동 예시

### 1. Sentry 연동 시뮬레이션
```bash
# Sentry 에러 감지 시 알림
curl -X POST "http://localhost:8000/api/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "error_rate_high",
    "metric_data": {
      "metric_value": 7.5,
      "additional_info": "Sentry에서 에러율 증가 감지",
      "sentry_data": {
        "error_count": 25,
        "project": "xai-community-backend",
        "environment": "production",
        "url": "https://sentry.io/organizations/your-org/issues/"
      }
    }
  }'
```

### 2. HetrixTools 업타임 연동 시뮬레이션
```bash
# 서비스 다운타임 감지
curl -X POST "http://localhost:8000/api/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_name": "service_downtime",
    "metric_data": {
      "metric_value": 95.0,
      "additional_info": "HetrixTools에서 서비스 다운타임 감지",
      "uptime_data": {
        "service_name": "XAI Community API",
        "downtime_duration": "5분",
        "last_check": "2025-07-15T10:30:00Z",
        "status_url": "https://status.example.com"
      }
    }
  }'
```

## 🛠️ Python 코드 예시

### 1. 알림 규칙 생성 함수
```python
import httpx
import asyncio

async def create_alert_rule(rule_data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/alerts/rules",
            json=rule_data
        )
        if response.status_code == 201:
            print(f"알림 규칙 생성 성공: {response.json()}")
        else:
            print(f"알림 규칙 생성 실패: {response.text}")

# 사용 예시
cpu_rule = {
    "name": "cpu_usage_high",
    "description": "CPU 사용률 모니터링",
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

asyncio.run(create_alert_rule(cpu_rule))
```

### 2. 메트릭 기반 알림 전송
```python
import psutil
import asyncio
import httpx

async def monitor_system_metrics():
    """시스템 메트릭을 모니터링하고 알림 전송"""
    async with httpx.AsyncClient() as client:
        while True:
            # CPU 사용률 확인
            cpu_usage = psutil.cpu_percent(interval=1)
            
            if cpu_usage > 80:
                await client.post(
                    "http://localhost:8000/api/alerts/send",
                    json={
                        "rule_name": "cpu_usage_high",
                        "metric_data": {
                            "metric_value": cpu_usage,
                            "additional_info": f"현재 CPU 사용률: {cpu_usage}%",
                            "timestamp": "2025-07-15T10:30:00Z"
                        }
                    }
                )
            
            # 메모리 사용률 확인
            memory_usage = psutil.virtual_memory().percent
            
            if memory_usage > 90:
                await client.post(
                    "http://localhost:8000/api/alerts/send",
                    json={
                        "rule_name": "memory_usage_critical",
                        "metric_data": {
                            "metric_value": memory_usage,
                            "additional_info": f"현재 메모리 사용률: {memory_usage}%",
                            "timestamp": "2025-07-15T10:30:00Z"
                        }
                    }
                )
            
            await asyncio.sleep(60)  # 1분마다 확인

# 백그라운드 모니터링 시작
asyncio.run(monitor_system_metrics())
```

### 3. 알림 통계 분석
```python
import httpx
import asyncio
import json

async def get_alert_statistics():
    """알림 통계 조회 및 분석"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/alerts/statistics")
        
        if response.status_code == 200:
            stats = response.json()
            
            print("=== 알림 시스템 통계 ===")
            print(f"총 규칙 수: {stats['total_rules']}")
            print(f"활성 규칙 수: {stats['active_rules']}")
            print(f"총 알림 수: {stats['total_alerts']}")
            print(f"오늘 전송된 알림: {stats['alerts_sent_today']}")
            print(f"시간당 알림 비율: {stats['alert_rate_per_hour']}")
            
            print("\n=== 심각도별 알림 ===")
            for severity, count in stats['alerts_by_severity'].items():
                print(f"{severity}: {count}개")
                
            print("\n=== 채널별 알림 ===")
            for channel, count in stats['alerts_by_channel'].items():
                print(f"{channel}: {count}개")
        else:
            print(f"통계 조회 실패: {response.text}")

asyncio.run(get_alert_statistics())
```

## 🚀 자동화 스크립트

### 1. 시스템 초기 설정 스크립트
```bash
#!/bin/bash
# setup_alerting.sh

API_BASE="http://localhost:8000/api/alerts"

echo "🔧 통합 알림 시스템 초기 설정 시작..."

# 기본 알림 규칙들 생성
curl -X POST "${API_BASE}/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cpu_usage_high",
    "description": "CPU 사용률 80% 이상",
    "condition": "greater_than",
    "threshold": {"metric": "cpu_usage", "value": 80.0, "duration_minutes": 5},
    "severity": "high",
    "channels": ["email", "discord"],
    "cooldown_minutes": 30,
    "enabled": true
  }'

curl -X POST "${API_BASE}/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "memory_usage_critical",
    "description": "메모리 사용률 90% 이상",
    "condition": "greater_than",
    "threshold": {"metric": "memory_usage", "value": 90.0, "duration_minutes": 2},
    "severity": "critical",
    "channels": ["email", "discord"],
    "cooldown_minutes": 15,
    "enabled": true
  }'

echo "✅ 알림 시스템 초기 설정 완료!"
```

### 2. 정기 헬스체크 스크립트
```bash
#!/bin/bash
# health_check.sh

API_BASE="http://localhost:8000/api/alerts"

echo "🏥 알림 시스템 헬스체크 시작..."

# 헬스체크 API 호출
HEALTH_STATUS=$(curl -s "${API_BASE}/health" | jq -r '.status')

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "✅ 알림 시스템 정상 동작 중"
else
    echo "❌ 알림 시스템 상태 이상: $HEALTH_STATUS"
    # 추가적인 알림 로직 (예: 이메일 전송)
fi

# 통계 정보 출력
echo "📊 현재 알림 통계:"
curl -s "${API_BASE}/statistics" | jq '.total_alerts, .alerts_sent_today, .alert_rate_per_hour'
```

이 문서는 통합 알림 시스템의 실제 사용법과 다양한 시나리오를 다룹니다. 필요에 따라 각 예시를 수정하여 사용할 수 있습니다.