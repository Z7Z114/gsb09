from __future__ import annotations
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
from dotenv import load_dotenv

try:  # aiosmtplib 可选：缺失时按"未配置"处理
    import aiosmtplib
    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    aiosmtplib = None
    AIOSMTPLIB_AVAILABLE = False

load_dotenv()


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "")
        self.default_email_to = os.getenv("EMAIL_TO", "feiyi_protection@example.org")

    async def send_archive_email(self, archive_data: Dict[str, Any],
                                  html_content: str,
                                  recipient_email: Optional[str] = None,
                                  custom_message: Optional[str] = None) -> Dict[str, Any]:
        if not AIOSMTPLIB_AVAILABLE:
            return {
                "success": False,
                "message": "邮件依赖 aiosmtplib 未安装",
                "mock_mode": True,
                "recipient": recipient_email or self.default_email_to
            }

        if not self.smtp_user or not self.smtp_password:
            return {
                "success": False,
                "message": "SMTP credentials not configured",
                "mock_mode": True,
                "recipient": recipient_email or self.default_email_to
            }

        recipient = recipient_email or self.default_email_to

        msg = MIMEMultipart()
        msg['From'] = f"弓道纪要 <{self.email_from}>"
        msg['To'] = recipient
        msg['Subject'] = f"【工艺档案】{archive_data.get('title', '传统弓箭制作工艺档案')}"

        body = f"""
尊敬的非遗保护中心工作人员：

您好！这是由弓道纪要平台自动生成的传统弓箭制作工艺档案。

{custom_message or '本次档案包含了匠人交流会议的核心内容、工艺要点和流派分析，希望能为非遗保护工作提供参考。'}

档案摘要：
{archive_data.get('summary', '')}

核心工艺要点：
{chr(10).join(['- ' + point for point in archive_data.get('key_points', [])])}

关键词：{', '.join(archive_data.get('keywords', []))}

详细内容请查看附件中的完整档案。

此致
敬礼！

弓道纪要 - 传统弓箭制作工艺传承平台
        """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        filename = f"工艺档案_{archive_data.get('title', '传统弓箭制作')}.html"
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(html_content.encode('utf-8'))
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{filename}"'
        )
        msg.attach(attachment)

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True
            )

            return {
                "success": True,
                "message": "Email sent successfully",
                "recipient": recipient,
                "subject": msg['Subject']
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "recipient": recipient
            }

    def send_archive_email_sync(self, archive_data: Dict[str, Any],
                                 html_content: str,
                                 recipient_email: Optional[str] = None,
                                 custom_message: Optional[str] = None) -> Dict[str, Any]:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                self.send_archive_email(archive_data, html_content, recipient_email, custom_message)
            )
            return result
        finally:
            loop.close()


email_service = EmailService()
