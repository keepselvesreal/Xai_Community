"""
알림 서비스 모듈

이메일과 Discord 웹훅을 통한 알림 전송을 담당하는 서비스
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional, Dict, Any, List
import aiohttp
import logging

from nadle_backend.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """
    통합 알림 서비스

    이메일(SMTP)과 Discord 웹훅을 통한 알림 전송을 지원합니다.
    """

    def __init__(self):
        """알림 서비스 초기화"""
        # SMTP 설정
        self.smtp_host = getattr(settings, "smtp_server", None)
        self.smtp_port = getattr(settings, "smtp_port", 587)
        self.smtp_user = getattr(settings, "smtp_username", None)
        self.smtp_password = getattr(settings, "smtp_password", None)
        self.smtp_use_tls = getattr(settings, "smtp_use_tls", True)

        # Discord 설정
        self.discord_webhook_url = getattr(settings, "discord_webhook_url", None)

        logger.info("NotificationService 초기화 완료")

    async def send_email_notification(
        self,
        to_email: str,
        subject: str,
        message: str,
        html_message: Optional[str] = None,
    ) -> bool:
        """
        이메일 알림 전송

        Args:
            to_email: 수신자 이메일 주소
            subject: 이메일 제목
            message: 이메일 본문 (텍스트)
            html_message: 이메일 본문 (HTML, 선택사항)

        Returns:
            전송 성공 여부
        """
        try:
            # SMTP 설정 확인
            if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
                logger.error("SMTP 설정이 누락되었습니다")
                return False

            # 이메일 메시지 구성
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to_email

            # 텍스트 파트 추가
            text_part = MIMEText(message, "plain", "utf-8")
            msg.attach(text_part)

            # HTML 파트 추가 (있는 경우)
            if html_message:
                html_part = MIMEText(html_message, "html", "utf-8")
                msg.attach(html_part)

            # SMTP 서버 연결 및 전송
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            try:
                if self.smtp_use_tls:
                    server.starttls()

                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            finally:
                server.quit()

            logger.info(f"이메일 알림 전송 성공: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP 인증 실패: {e}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP 연결 실패: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"이메일 전송 중 예외 발생: {e}")
            return False

    async def send_discord_notification(
        self,
        message: str,
        title: Optional[str] = None,
        color: Optional[int] = None,
        username: Optional[str] = None,
    ) -> bool:
        """
        Discord 웹훅 알림 전송

        Args:
            message: 알림 메시지
            title: 임베드 제목 (선택사항)
            color: 임베드 색상 (선택사항)
            username: 사용자 이름 (선택사항)

        Returns:
            전송 성공 여부
        """
        try:
            # 웹훅 URL 확인
            if not self.discord_webhook_url:
                logger.error("Discord 웹훅 URL이 설정되지 않았습니다")
                return False

            # 페이로드 구성
            payload = {}

            if username:
                payload["username"] = username

            # 제목이나 색상이 있으면 임베드 사용, 없으면 단순 메시지
            if title or color:
                embed = {
                    "description": message,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                if title:
                    embed["title"] = title
                if color:
                    embed["color"] = color

                payload["embeds"] = [embed]
            else:
                payload["content"] = message

            # HTTP 요청 전송
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook_url, json=payload
                ) as response:
                    if response.status == 204:
                        logger.info("Discord 알림 전송 성공")
                        return True
                    else:
                        logger.error(f"Discord 웹훅 요청 실패: {response.status}")
                        return False

        except asyncio.TimeoutError:
            logger.error("Discord 웹훅 요청 타임아웃")
            return False
        except aiohttp.ClientError as e:
            logger.error(f"Discord 웹훅 클라이언트 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"Discord 알림 전송 중 예외 발생: {e}")
            return False

    async def send_uptime_alert(
        self,
        monitor_name: str,
        status: str,
        url: str,
        duration: int,
        email_recipients: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """
        업타임 모니터링 알림 전송

        Args:
            monitor_name: 모니터 이름
            status: 상태 ('up' 또는 'down')
            url: 모니터링 URL
            duration: 지속 시간 (초)
            email_recipients: 이메일 수신자 목록 (선택사항)

        Returns:
            각 채널별 전송 결과
        """
        results = {}

        # 상태에 따른 메시지 및 색상 설정
        if status.lower() == "down":
            discord_message = f"🚨 **{monitor_name}**이(가) 다운되었습니다!\n\n• **URL:** {url}\n• **지속 시간:** {duration}초"
            discord_color = 0xFF0000  # 빨간색
            email_subject = f"[ALERT] {monitor_name} 다운 알림"
        else:  # up/recovery
            discord_message = f"✅ **{monitor_name}**이(가) 복구되었습니다!\n\n• **URL:** {url}\n• **다운타임:** {duration}초"
            discord_color = 0x00FF00  # 녹색
            email_subject = f"[RECOVERY] {monitor_name} 복구 알림"

        email_message = f"""
안녕하세요,

모니터링 시스템에서 다음과 같은 상태 변경이 감지되었습니다:

모니터 이름: {monitor_name}
URL: {url}
상태: {status}
지속 시간: {duration}초
감지 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

확인이 필요합니다.

감사합니다.
모니터링 시스템
"""

        # Discord 알림 전송
        results["discord"] = await self.send_discord_notification(
            message=discord_message,
            title=f"업타임 알림 - {monitor_name}",
            color=discord_color,
            username="Uptime Monitor",
        )

        # 이메일 알림 전송
        email_result = True
        if email_recipients:
            for recipient in email_recipients:
                individual_result = await self.send_email_notification(
                    to_email=recipient, subject=email_subject, message=email_message
                )
                if not individual_result:
                    email_result = False
        else:
            # 기본 수신자가 있다면 전송
            if self.smtp_user:
                email_result = await self.send_email_notification(
                    to_email=self.smtp_user,
                    subject=email_subject,
                    message=email_message,
                )

        results["email"] = email_result

        return results

    async def send_performance_alert(
        self, metric_name: str, current_value: float, threshold: float, trend: str
    ) -> Dict[str, bool]:
        """
        성능 알림 전송

        Args:
            metric_name: 메트릭 이름
            current_value: 현재 값
            threshold: 임계값
            trend: 트렌드 ('increasing', 'decreasing', 'stable')

        Returns:
            각 채널별 전송 결과
        """
        results = {}

        # 알림 메시지 구성
        discord_message = f"""
⚠️ **성능 알림**

메트릭에서 임계값 초과가 감지되었습니다:

• **메트릭:** {metric_name}
• **현재 값:** {current_value}
• **임계값:** {threshold}
• **트렌드:** {trend}
• **감지 시간:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

확인이 필요합니다.
"""

        email_message = f"""
안녕하세요,

성능 모니터링 시스템에서 다음과 같은 이상 상황이 감지되었습니다:

메트릭 이름: {metric_name}
현재 값: {current_value}
임계값: {threshold}
트렌드: {trend}
감지 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

즉시 확인이 필요합니다.

감사합니다.
성능 모니터링 시스템
"""

        # Discord 알림 전송
        results["discord"] = await self.send_discord_notification(
            message=discord_message,
            title=f"성능 경고 - {metric_name}",
            color=0xFFA500,  # 주황색
            username="Performance Monitor",
        )

        # 이메일 알림 전송 (기본 수신자)
        if self.smtp_user:
            results["email"] = await self.send_email_notification(
                to_email=self.smtp_user,
                subject=f"[PERFORMANCE] {metric_name} 임계값 초과 알림",
                message=email_message,
            )
        else:
            results["email"] = True  # 설정되지 않으면 성공으로 처리

        return results

    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """
        마크다운 텍스트를 HTML로 변환

        Args:
            markdown_text: 마크다운 텍스트

        Returns:
            변환된 HTML
        """
        try:
            # 간단한 마크다운 -> HTML 변환
            html_content = markdown_text

            # **굵게** -> <strong>굵게</strong>
            import re

            html_content = re.sub(
                r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_content
            )

            # 줄바꿈 -> <br>
            html_content = html_content.replace("\n", "<br>")

            # HTML 문서로 감싸기
            html_result = f"<html><body>{html_content}</body></html>"

            return html_result

        except Exception as e:
            logger.error(f"마크다운 변환 중 오류: {e}")
            return f"<html><body>{markdown_text}</body></html>"


def get_notification_service() -> NotificationService:
    """
    알림 서비스 팩토리 함수

    Returns:
        NotificationService 인스턴스
    """
    return NotificationService()
