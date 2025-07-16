# 외부 모니터링 시스템 연동 가이드

## 🔗 지원 가능한 외부 시스템

현재 구축된 통합 알림 시스템은 다음과 같은 외부 모니터링 시스템과 연동 가능합니다:

### 1. Sentry (에러 추적 시스템)
- **연동 방식**: Webhook 또는 API 폴링
- **주요 메트릭**: 에러율, 에러 빈도, 성능 지표
- **알림 시나리오**: 에러 급증, 새로운 에러 타입 감지

### 2. HetrixTools (업타임 모니터링)
- **연동 방식**: Webhook 또는 API 폴링
- **주요 메트릭**: 업타임 비율, 응답 시간, 서비스 상태
- **알림 시나리오**: 서비스 다운타임, 응답 시간 지연

### 3. Google Analytics 4 (사용자 분석)
- **연동 방식**: API 연동
- **주요 메트릭**: 사용자 수, 페이지 뷰, 이벤트 수
- **알림 시나리오**: 트래픽 급증/급감, 에러 페이지 접근 증가

### 4. 시스템 메트릭 (서버 모니터링)
- **연동 방식**: 직접 수집 또는 외부 도구 연동
- **주요 메트릭**: CPU, 메모리, 디스크, 네트워크
- **알림 시나리오**: 리소스 사용량 임계값 초과

## 🛠️ 실제 연동 구현 예시

### 1. Sentry 연동 구현

#### 1.1 Sentry Webhook 설정
```python
# sentry_integration.py
import json
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.post("/webhooks/sentry")
async def sentry_webhook(request: Request):
    """Sentry webhook 처리"""
    payload = await request.json()
    
    # Sentry 이벤트 처리
    if payload.get("action") == "created":
        event_data = payload.get("data", {})
        issue = event_data.get("issue", {})
        
        # 에러율 계산
        error_count = issue.get("count", 0)
        project = issue.get("project", {}).get("name", "unknown")
        
        # 알림 시스템에 전송
        await send_sentry_alert(
            error_count=error_count,
            project=project,
            issue_url=issue.get("permalink"),
            title=issue.get("title", "Unknown Error")
        )
    
    return {"status": "ok"}

async def send_sentry_alert(error_count: int, project: str, issue_url: str, title: str):
    """Sentry 알림을 통합 알림 시스템으로 전송"""
    
    # 에러율 임계값 확인
    if error_count > 10:  # 10회 이상 에러 발생 시
        severity = "critical" if error_count > 50 else "high"
        
        alert_data = {
            "rule_name": "sentry_error_rate",
            "metric_data": {
                "metric_value": error_count,
                "additional_info": f"Sentry 에러 감지: {title}",
                "sentry_data": {
                    "project": project,
                    "issue_url": issue_url,
                    "error_count": error_count,
                    "title": title
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8000/api/alerts/send",
                json=alert_data
            )
```

#### 1.2 Sentry API 폴링 구현
```python
# sentry_polling.py
import asyncio
import httpx
from datetime import datetime, timedelta

class SentryMonitor:
    def __init__(self, sentry_token: str, org_slug: str):
        self.sentry_token = sentry_token
        self.org_slug = org_slug
        self.base_url = "https://sentry.io/api/0"
        
    async def monitor_projects(self):
        """Sentry 프로젝트들을 주기적으로 모니터링"""
        while True:
            try:
                await self._check_error_rates()
                await self._check_performance_issues()
                await asyncio.sleep(300)  # 5분마다 확인
            except Exception as e:
                print(f"Sentry 모니터링 오류: {e}")
                await asyncio.sleep(60)
    
    async def _check_error_rates(self):
        """에러율 확인"""
        headers = {"Authorization": f"Bearer {self.sentry_token}"}
        
        # 최근 1시간 동안의 이벤트 조회
        since = datetime.utcnow() - timedelta(hours=1)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/{self.org_slug}/events/",
                headers=headers,
                params={
                    "statsPeriod": "1h",
                    "query": "!event.type:transaction"
                }
            )
            
            if response.status_code == 200:
                events = response.json()
                error_count = len(events.get("data", []))
                
                # 에러율이 임계값 초과 시 알림
                if error_count > 20:
                    await self._send_error_rate_alert(error_count)
    
    async def _check_performance_issues(self):
        """성능 이슈 확인"""
        headers = {"Authorization": f"Bearer {self.sentry_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/organizations/{self.org_slug}/events/",
                headers=headers,
                params={
                    "statsPeriod": "1h",
                    "query": "transaction.duration:>2000"  # 2초 이상 트랜잭션
                }
            )
            
            if response.status_code == 200:
                events = response.json()
                slow_transactions = len(events.get("data", []))
                
                if slow_transactions > 10:
                    await self._send_performance_alert(slow_transactions)
    
    async def _send_error_rate_alert(self, error_count: int):
        """에러율 알림 전송"""
        alert_data = {
            "rule_name": "sentry_error_rate",
            "metric_data": {
                "metric_value": error_count,
                "additional_info": f"Sentry에서 최근 1시간 동안 {error_count}개 에러 감지",
                "sentry_data": {
                    "error_count": error_count,
                    "time_period": "1h",
                    "dashboard_url": f"https://sentry.io/organizations/{self.org_slug}/dashboard/"
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8000/api/alerts/send",
                json=alert_data
            )
    
    async def _send_performance_alert(self, slow_count: int):
        """성능 알림 전송"""
        alert_data = {
            "rule_name": "sentry_performance_issue",
            "metric_data": {
                "metric_value": slow_count,
                "additional_info": f"Sentry에서 {slow_count}개 느린 트랜잭션 감지",
                "sentry_data": {
                    "slow_transactions": slow_count,
                    "threshold": "2000ms",
                    "time_period": "1h"
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8000/api/alerts/send",
                json=alert_data
            )

# 사용 예시
async def main():
    monitor = SentryMonitor(
        sentry_token="your-sentry-token",
        org_slug="your-org-slug"
    )
    await monitor.monitor_projects()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. HetrixTools 연동 구현

#### 2.1 HetrixTools API 모니터링
```python
# hetrixtools_integration.py
import asyncio
import httpx
from datetime import datetime

class HetrixToolsMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hetrixtools.com/v2/"
        
    async def monitor_uptime(self):
        """업타임 모니터링"""
        while True:
            try:
                await self._check_uptime_status()
                await self._check_response_times()
                await asyncio.sleep(300)  # 5분마다 확인
            except Exception as e:
                print(f"HetrixTools 모니터링 오류: {e}")
                await asyncio.sleep(60)
    
    async def _check_uptime_status(self):
        """업타임 상태 확인"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/uptime/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                monitors = data.get("monitors", [])
                
                for monitor in monitors:
                    uptime_percentage = monitor.get("uptime_percentage", 100)
                    service_name = monitor.get("name", "Unknown Service")
                    status = monitor.get("status", "unknown")
                    
                    # 업타임이 99% 미만이거나 서비스가 다운된 경우
                    if uptime_percentage < 99 or status == "down":
                        await self._send_uptime_alert(
                            service_name=service_name,
                            uptime_percentage=uptime_percentage,
                            status=status,
                            monitor_data=monitor
                        )
    
    async def _check_response_times(self):
        """응답 시간 확인"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/uptime/response-times/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                monitors = data.get("monitors", [])
                
                for monitor in monitors:
                    avg_response_time = monitor.get("avg_response_time", 0)
                    service_name = monitor.get("name", "Unknown Service")
                    
                    # 응답 시간이 3초 이상인 경우
                    if avg_response_time > 3000:
                        await self._send_response_time_alert(
                            service_name=service_name,
                            response_time=avg_response_time,
                            monitor_data=monitor
                        )
    
    async def _send_uptime_alert(self, service_name: str, uptime_percentage: float, 
                                status: str, monitor_data: dict):
        """업타임 알림 전송"""
        severity = "critical" if status == "down" else "high"
        
        alert_data = {
            "rule_name": "hetrixtools_uptime",
            "metric_data": {
                "metric_value": uptime_percentage,
                "additional_info": f"HetrixTools: {service_name} 업타임 이슈 감지",
                "hetrixtools_data": {
                    "service_name": service_name,
                    "uptime_percentage": uptime_percentage,
                    "status": status,
                    "monitor_id": monitor_data.get("id"),
                    "url": monitor_data.get("url"),
                    "last_check": datetime.utcnow().isoformat()
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8000/api/alerts/send",
                json=alert_data
            )
    
    async def _send_response_time_alert(self, service_name: str, response_time: float,
                                       monitor_data: dict):
        """응답 시간 알림 전송"""
        alert_data = {
            "rule_name": "hetrixtools_response_time",
            "metric_data": {
                "metric_value": response_time,
                "additional_info": f"HetrixTools: {service_name} 응답 시간 지연 감지",
                "hetrixtools_data": {
                    "service_name": service_name,
                    "response_time_ms": response_time,
                    "threshold_ms": 3000,
                    "monitor_id": monitor_data.get("id"),
                    "url": monitor_data.get("url")
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8000/api/alerts/send",
                json=alert_data
            )

# 사용 예시
async def main():
    monitor = HetrixToolsMonitor(api_key="your-hetrixtools-api-key")
    await monitor.monitor_uptime()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 2.2 HetrixTools Webhook 설정
```python
# hetrixtools_webhook.py
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.post("/webhooks/hetrixtools")
async def hetrixtools_webhook(request: Request):
    """HetrixTools webhook 처리"""
    payload = await request.json()
    
    # HetrixTools 이벤트 처리
    event_type = payload.get("event_type")
    monitor_data = payload.get("monitor", {})
    
    if event_type == "monitor_down":
        await send_downtime_alert(monitor_data)
    elif event_type == "monitor_up":
        await send_recovery_alert(monitor_data)
    elif event_type == "slow_response":
        await send_slow_response_alert(monitor_data)
    
    return {"status": "ok"}

async def send_downtime_alert(monitor_data: dict):
    """다운타임 알림 전송"""
    alert_data = {
        "rule_name": "hetrixtools_downtime",
        "metric_data": {
            "metric_value": 0,  # 서비스 다운 = 0% 업타임
            "additional_info": f"HetrixTools: {monitor_data.get('name')} 서비스 다운 감지",
            "hetrixtools_data": {
                "service_name": monitor_data.get("name"),
                "url": monitor_data.get("url"),
                "downtime_start": monitor_data.get("downtime_start"),
                "status": "down"
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:8000/api/alerts/send",
            json=alert_data
        )

async def send_recovery_alert(monitor_data: dict):
    """복구 알림 전송"""
    alert_data = {
        "rule_name": "hetrixtools_recovery",
        "metric_data": {
            "metric_value": 100,  # 서비스 복구 = 100% 업타임
            "additional_info": f"HetrixTools: {monitor_data.get('name')} 서비스 복구됨",
            "hetrixtools_data": {
                "service_name": monitor_data.get("name"),
                "url": monitor_data.get("url"),
                "recovery_time": monitor_data.get("recovery_time"),
                "downtime_duration": monitor_data.get("downtime_duration"),
                "status": "up"
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:8000/api/alerts/send",
            json=alert_data
        )
```

### 3. 시스템 메트릭 모니터링

#### 3.1 시스템 리소스 모니터링
```python
# system_monitor.py
import asyncio
import psutil
import httpx
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.alert_api_url = "http://localhost:8000/api/alerts/send"
        
    async def monitor_system(self):
        """시스템 리소스 모니터링"""
        while True:
            try:
                await self._check_cpu_usage()
                await self._check_memory_usage()
                await self._check_disk_usage()
                await self._check_network_stats()
                await asyncio.sleep(60)  # 1분마다 확인
            except Exception as e:
                print(f"시스템 모니터링 오류: {e}")
                await asyncio.sleep(30)
    
    async def _check_cpu_usage(self):
        """CPU 사용률 확인"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent > 80:
            await self._send_cpu_alert(cpu_percent)
    
    async def _check_memory_usage(self):
        """메모리 사용률 확인"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 90:
            await self._send_memory_alert(memory_percent, memory)
    
    async def _check_disk_usage(self):
        """디스크 사용률 확인"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 90:
            await self._send_disk_alert(disk_percent, disk)
    
    async def _check_network_stats(self):
        """네트워크 통계 확인"""
        net_io = psutil.net_io_counters()
        
        # 네트워크 오류 패킷 확인
        if net_io.errin > 100 or net_io.errout > 100:
            await self._send_network_alert(net_io)
    
    async def _send_cpu_alert(self, cpu_percent: float):
        """CPU 알림 전송"""
        alert_data = {
            "rule_name": "system_cpu_high",
            "metric_data": {
                "metric_value": cpu_percent,
                "additional_info": f"시스템 CPU 사용률 높음: {cpu_percent}%",
                "system_data": {
                    "cpu_percent": cpu_percent,
                    "cpu_count": psutil.cpu_count(),
                    "load_avg": psutil.getloadavg(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
        
        await self._send_alert(alert_data)
    
    async def _send_memory_alert(self, memory_percent: float, memory_info):
        """메모리 알림 전송"""
        alert_data = {
            "rule_name": "system_memory_high",
            "metric_data": {
                "metric_value": memory_percent,
                "additional_info": f"시스템 메모리 사용률 높음: {memory_percent}%",
                "system_data": {
                    "memory_percent": memory_percent,
                    "memory_total_gb": memory_info.total / (1024**3),
                    "memory_available_gb": memory_info.available / (1024**3),
                    "memory_used_gb": memory_info.used / (1024**3),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
        
        await self._send_alert(alert_data)
    
    async def _send_disk_alert(self, disk_percent: float, disk_info):
        """디스크 알림 전송"""
        alert_data = {
            "rule_name": "system_disk_high",
            "metric_data": {
                "metric_value": disk_percent,
                "additional_info": f"시스템 디스크 사용률 높음: {disk_percent:.1f}%",
                "system_data": {
                    "disk_percent": disk_percent,
                    "disk_total_gb": disk_info.total / (1024**3),
                    "disk_used_gb": disk_info.used / (1024**3),
                    "disk_free_gb": disk_info.free / (1024**3),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
        
        await self._send_alert(alert_data)
    
    async def _send_network_alert(self, net_io):
        """네트워크 알림 전송"""
        alert_data = {
            "rule_name": "system_network_error",
            "metric_data": {
                "metric_value": net_io.errin + net_io.errout,
                "additional_info": f"네트워크 오류 패킷 감지: 입력 {net_io.errin}, 출력 {net_io.errout}",
                "system_data": {
                    "error_packets_in": net_io.errin,
                    "error_packets_out": net_io.errout,
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
        
        await self._send_alert(alert_data)
    
    async def _send_alert(self, alert_data: dict):
        """알림 전송"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(self.alert_api_url, json=alert_data)
            except Exception as e:
                print(f"알림 전송 실패: {e}")

# 사용 예시
async def main():
    monitor = SystemMonitor()
    await monitor.monitor_system()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 통합 모니터링 서비스

모든 외부 시스템을 하나의 서비스로 통합하는 예시:

```python
# integrated_monitor.py
import asyncio
import logging
from typing import List, Dict, Any

class IntegratedMonitoringService:
    def __init__(self):
        self.monitors = []
        self.logger = logging.getLogger(__name__)
        
    def add_monitor(self, monitor):
        """모니터 추가"""
        self.monitors.append(monitor)
        
    async def start_monitoring(self):
        """모든 모니터링 시작"""
        tasks = []
        
        for monitor in self.monitors:
            if hasattr(monitor, 'monitor_system'):
                tasks.append(asyncio.create_task(monitor.monitor_system()))
            elif hasattr(monitor, 'monitor_projects'):
                tasks.append(asyncio.create_task(monitor.monitor_projects()))
            elif hasattr(monitor, 'monitor_uptime'):
                tasks.append(asyncio.create_task(monitor.monitor_uptime()))
        
        self.logger.info(f"총 {len(tasks)}개의 모니터링 태스크 시작")
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"모니터링 서비스 오류: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """모니터링 상태 조회"""
        return {
            "active_monitors": len(self.monitors),
            "monitor_types": [type(monitor).__name__ for monitor in self.monitors],
            "status": "running"
        }

# 사용 예시
async def main():
    # 통합 모니터링 서비스 초기화
    integrated_service = IntegratedMonitoringService()
    
    # 각종 모니터 추가
    integrated_service.add_monitor(SystemMonitor())
    integrated_service.add_monitor(SentryMonitor(
        sentry_token="your-token",
        org_slug="your-org"
    ))
    integrated_service.add_monitor(HetrixToolsMonitor(
        api_key="your-api-key"
    ))
    
    # 모니터링 시작
    await integrated_service.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🚀 배포 및 실행

### 1. Docker를 사용한 배포
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "integrated_monitor.py"]
```

### 2. Docker Compose 설정
```yaml
# docker-compose.yml
version: '3.8'

services:
  alert-system:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SMTP_SERVER=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  monitoring-service:
    build: .
    depends_on:
      - alert-system
    environment:
      - SENTRY_TOKEN=${SENTRY_TOKEN}
      - SENTRY_ORG=${SENTRY_ORG}
      - HETRIXTOOLS_API_KEY=${HETRIXTOOLS_API_KEY}
    command: python integrated_monitor.py
    restart: unless-stopped
```

### 3. 환경 변수 설정
```bash
# .env
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
SENTRY_TOKEN=your-sentry-token
SENTRY_ORG=your-org-slug
HETRIXTOOLS_API_KEY=your-hetrixtools-api-key
```

이 가이드를 통해 기존 모니터링 시스템들을 통합 알림 시스템과 연동하여 중앙 집중식 알림 관리를 구현할 수 있습니다.