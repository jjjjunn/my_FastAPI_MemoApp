import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

class EmailService:
    def send_email(
            self,
            receiver_email: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "회원 가입을 환영합니다."

        body = "메모 앱 서비스를 이용해 주셔서 감사합니다."
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)

class EmailServiceBye:
    def send_email(
            self,
            receiver_email: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "탈퇴 완료 이메일."

        body = "그동안 메모 앱 서비스를 이용해 주셔서 감사합니다."
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)