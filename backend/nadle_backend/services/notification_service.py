"""
알림 서비스

이메일, 디스코드 웹훅을 통한 알림 전송 서비스
"""
import smtplib
import aiohttp
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from nadle_backend.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """종합 알림 서비스"""

    def __init__(self):
        self.smtp_host = getattr(settings, 'smtp_host', None)
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_user = getattr(settings, 'smtp_user', None)
        self.smtp_password = getattr(settings, 'smtp_password', None)
        self.smtp_use_tls = getattr(settings, 'smtp_use_tls', True)
        self.discord_webhook_url = getattr(settings, 'discord_webhook_url', None)
        # SMS 설정 (향후 Twilio, AWS SNS 등 연동)
        self.sms_api_key = getattr(settings, 'sms_api_key', None)
        self.sms_api_secret = getattr(settings, 'sms_api_secret', None)
        self.sms_from_number = getattr(settings, 'sms_from_number', None)

    async def send_email_notification(
        self,
        to_email: str,
        subject: str,
        message: str,
        html_message: Optional[str] = None
    ) -> bool:
        """
        이메일 알림 전송
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            message: 텍스트 메시지
            html_message: HTML 메시지 (선택)
            
        Returns:
            bool: 전송 성공 여부
        """
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.error("SMTP 설정이 완전하지 않습니다")
            return False

        try:
            # 이메일 메시지 구성
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject

            # 텍스트 파트 추가
            text_part = MIMEText(message, 'plain', 'utf-8')
            msg.attach(text_part)

            # HTML 파트 추가 (있는 경우)
            if html_message:
                html_part = MIMEText(html_message, 'html', 'utf-8')
                msg.attach(html_part)

            # SMTP 서버 연결 및 전송
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.smtp_use_tls:
                server.starttls()
            
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"이메일 알림 전송 성공: {to_email}")
            return True

        except Exception as e:
            logger.error(f"이메일 알림 전송 실패: {e}")
            return False

    async def send_discord_notification(
        self,
        message: str,
        title: Optional[str] = None,
        color: Optional[int] = None,
        username: Optional[str] = None
    ) -> bool:
        """
        디스코드 웹훅을 통한 알림 전송
        
        Args:
            message: 메시지 내용
            title: 임베드 제목
            color: 임베드 색상 (16진수)
            username: 봇 사용자명
            
        Returns:
            bool: 전송 성공 여부
        """
        if not self.discord_webhook_url:
            logger.error("Discord 웹훅 URL이 설정되지 않았습니다")
            return False

        try:
            # 웹훅 페이로드 구성
            payload = {}
            
            if username:
                payload['username'] = username
            
            # 임베드 사용 (제목이나 색상이 있는 경우)
            if title or color:
                embed = {
                    'description': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                if title:
                    embed['title'] = title
                
                if color:
                    embed['color'] = color
                
                payload['embeds'] = [embed]
            else:
                # 단순 텍스트 메시지
                payload['content'] = message

            # 웹훅 전송
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook_url,
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status == 204:
                        logger.info("Discord 알림 전송 성공")
                        return True
                    else:
                        logger.error(f"Discord 알림 전송 실패: HTTP {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Discord 알림 전송 실패: {e}")
            return False

    async def send_uptime_alert(
        self,
        monitor_name: str,
        status: str,
        url: str,
        duration: Optional[int] = None,
        email_recipients: Optional[list] = None
    ) -> Dict[str, bool]:
        """
        업타임 모니터링 알림 전송 (이메일 + 디스코드)
        
        Args:
            monitor_name: 모니터 이름
            status: 상태 (up/down)
            url: 모니터링 URL
            duration: 다운타임 지속 시간 (초)
            email_recipients: 이메일 수신자 목록
            
        Returns:
            Dict[str, bool]: 각 채널별 전송 결과
        """
        results = {}
        
        # 상태에 따른 메시지 구성
        if status.lower() == "down":
            emoji = "🔴"
            color = 0xFF0000  # 빨간색
            subject = f"[ALERT] {monitor_name} 서비스 다운"
            if duration:
                message = f"{emoji} **{monitor_name}** 서비스가 다운되었습니다.\n\n"
                message += f"**URL:** {url}\n"
                message += f"**다운타임:** {duration}초\n"
                message += f"**감지 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                message = f"{emoji} **{monitor_name}** 서비스가 다운되었습니다.\n\n"
                message += f"**URL:** {url}\n"
                message += f"**감지 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            emoji = "🟢"
            color = 0x00FF00  # 녹색
            subject = f"[RECOVERY] {monitor_name} 서비스 복구"
            if duration:
                message = f"{emoji} **{monitor_name}** 서비스가 복구되었습니다.\n\n"
                message += f"**URL:** {url}\n"
                message += f"**다운타임:** {duration}초\n"
                message += f"**복구 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                message = f"{emoji} **{monitor_name}** 서비스가 정상입니다.\n\n"
                message += f"**URL:** {url}\n"
                message += f"**확인 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Discord 알림 전송
        discord_result = await self.send_discord_notification(
            message=message,
            title="업타임 모니터링 알림",
            color=color,
            username="Uptime Monitor"
        )
        results['discord'] = discord_result

        # 이메일 알림 전송
        if email_recipients:
            email_results = []
            for email in email_recipients:
                email_result = await self.send_email_notification(
                    to_email=email,
                    subject=subject,
                    message=message.replace('**', '').replace('*', ''),  # 마크다운 제거
                    html_message=self._convert_markdown_to_html(message)
                )
                email_results.append(email_result)
            
            results['email'] = all(email_results) if email_results else False
        else:
            # 기본 이메일 (SMTP 사용자 자신에게)
            if self.smtp_user:
                email_result = await self.send_email_notification(
                    to_email=self.smtp_user,
                    subject=subject,
                    message=message.replace('**', '').replace('*', ''),
                    html_message=self._convert_markdown_to_html(message)
                )
                results['email'] = email_result
            else:
                results['email'] = False

        return results

    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """간단한 마크다운을 HTML로 변환"""
        html = markdown_text
        
        # **bold** → <strong>bold</strong> (정규식 사용하여 올바르게 처리)
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # 줄바꿈 → <br>
        html = html.replace('\n', '<br>')
        return f"<html><body>{html}</body></html>"

    async def send_performance_alert(
        self,
        metric_name: str,
        current_value: float,
        threshold: float,
        trend: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        성능 알림 전송
        
        Args:
            metric_name: 메트릭 이름
            current_value: 현재 값
            threshold: 임계값
            trend: 트렌드 정보
            
        Returns:
            Dict[str, bool]: 각 채널별 전송 결과
        """
        emoji = "⚠️"
        color = 0xFFA500  # 주황색
        subject = f"[PERFORMANCE] {metric_name} 임계값 초과"
        
        message = f"{emoji} **성능 알림**\n\n"
        message += f"**메트릭:** {metric_name}\n"
        message += f"**현재 값:** {current_value}\n"
        message += f"**임계값:** {threshold}\n"
        
        if trend:
            message += f"**트렌드:** {trend}\n"
        
        message += f"**감지 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        results = {}
        
        # Discord 알림
        results['discord'] = await self.send_discord_notification(
            message=message,
            title="성능 모니터링 알림",
            color=color,
            username="Performance Monitor"
        )
        
        # 이메일 알림 (SMTP 사용자에게)
        if self.smtp_user:
            results['email'] = await self.send_email_notification(
                to_email=self.smtp_user,
                subject=subject,
                message=message.replace('**', '').replace('*', ''),
                html_message=self._convert_markdown_to_html(message)
            )
        else:
            results['email'] = False

        return results

    async def send_sms_notification(
        self,
        phone: str,
        message: str,
        urgent: bool = False
    ) -> bool:
        """
        SMS 알림 전송 (Mock 구현 - 실제로는 Twilio, AWS SNS 등 사용)
        
        Args:
            phone: 수신자 전화번호
            message: 메시지 내용
            urgent: 긴급 여부
            
        Returns:
            bool: 전송 성공 여부
        """
        # 개발 중에는 로그로만 처리
        if not all([self.sms_api_key, self.sms_from_number]):
            logger.warning("SMS 설정이 완전하지 않습니다 - Mock 전송으로 처리")
            logger.info(f"[SMS Mock] To: {phone}, Message: {message}, Urgent: {urgent}")
            return True
        
        try:
            # 실제 SMS API 연동 시 여기에 구현
            # 예: Twilio, AWS SNS, 국내 SMS 서비스 등
            logger.info(f"SMS 알림 전송: {phone}")
            
            # Mock 성공 응답
            return True
            
        except Exception as e:
            logger.error(f"SMS 알림 전송 실패: {e}")
            return False


# 의존성 주입을 위한 팩토리 함수
def get_notification_service() -> NotificationService:
    """알림 서비스 인스턴스 반환"""
    return NotificationService()