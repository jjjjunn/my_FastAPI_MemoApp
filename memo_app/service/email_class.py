import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import logging

load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)

# 회원가입 환영 이메일
class EmailServiceWelcome:
    def send_email(
            self,
            receiver_email: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "회원 가입을 환영합니다."

        # HTML 본문 구성
        html_body = f"""
        <html>
            <body>
                <p><strong>메모 앱</strong> 회원가입을 환영합니다!</p>
                <p>앞으로 많은 이용 부탁 드리며, 사용에 불편함이 있거나, 제안사항이 있으시면</p>
                <p>언제든 피드백 부탁 드립니다! 👍🏻</p>
                <p><a href="http://localhost:8000" target="_blank">✅ 로그인하러 가기</a></p>
            </body>
        </html>
        """

        message.attach(MIMEText(html_body, "html"))
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            logger.info(f"회원가입 이메일이 {receiver_email}로 성공적으로 전송되었습니다.")
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")

# 회원 탈퇴 이메일
class EmailServiceBye:
    def send_email(
            self,
            receiver_email: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "탈퇴 완료 이메일."

        # HTML 본문 구성
        html_body = f"""
        <html>
            <body>
                <p><strong>메모 앱</strong> 회원 탈퇴가 완료되었습니다.</p>
                <p>그동안 고객님의 이용에 감사 드리며, 더 나은 서비스가 되도록 노력하겠습니다.🙇🏻‍♀️</p>
                <p>곧 고객님을 다시 만날 날을 기다리겠습니다. 🙋🏻‍♂️</p>
                <p><a href="http://localhost:8000" target="_blank">✅ 회원가입하러 가기</a></p>
            </body>
        </html>
        """

        message.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            logger.info(f"탈퇴 안내 이메일이 {receiver_email}로 성공적으로 전송되었습니다.")
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")

# 아이디 찾기 이메일
class EmailServiceFindId:
    def send_email(
            self,
            receiver_email: str,
            username: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "아이디 찾기 이메일."

        # HTML 본문 구성
        html_body = f"""
        <html>
            <body>
                <p>사용자님의 아이디는 <strong>{username}</strong> 입니다.</p>
                <p><a href="http://localhost:8000" target="_blank">✅ 로그인하러 가기</a></p>
            </body>
        </html>
        """

        message.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            logger.info(f"아이디가 {receiver_email}로 성공적으로 전송되었습니다.")
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")

class EmailRequest(BaseModel):
    email: str

# 임시 비밀번호 이메일
class EmailServiceSendTempPW:
    def send_email(
        self,
        receiver_email: str,
        username: str,
        temp_password: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "임시 비밀번호 이메일"

         # HTML 본문 구성
        html_body = f"""
        <html>
            <body>
                <p><strong>{username}</strong>님의 임시비밀번호는 {temp_password} 입니다.</p>
                <p>해당 비밀번호는 임시 비밀번호이므로, 비밀번호를 변경하는 것을 권장 드립니다.</p>
                <p>아래 링크를 통해 비밀번호를 변경해 주세요.</p>
                <p><a href="http://localhost:8000/change_pw" target="_blank">➡️ 비밀번호 변경하러 가기</a></p>
            </body>
        </html>
        """

        message.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            logger.info(f"임시 비밀번호가 {receiver_email}로 성공적으로 전송되었습니다.")
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")

class UsernameEmailRequest(BaseModel):
    username: str
    email: str

# 비밀번호 변경 이메일
class EmailServiceSendNewPW:
    def send_email(
        self,
        receiver_email: str,
        username: str,
    ):
        sender_email = os.getenv('EMAIL_ADDRESS')
        password = os.getenv('EMAIL_PASSWORD')

        message = MIMEMultipart("alternative")  # <-- 중요! HTML을 포함하려면 "alternative"로 설정
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = "비밀번호 변경 안내 이메일"

        # HTML 본문 구성
        html_body = f"""
        <html>
            <body>
                <p><strong>{username}</strong> 사용자님의 비밀번호가 변경되었습니다.</p>
                <p>만약 본인이 변경한 것이 아니라면 아래 링크를 통해 비밀번호를 즉시 변경해 주세요.</p>
                <p><a href="http://localhost:8000/change_pw" target="_blank">➡️ 비밀번호 변경하러 가기</a></p>
            </body>
        </html>
        """

        message.attach(MIMEText(html_body, "html"))  # HTML 형식으로 첨부

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, password)
                server.send_message(message)
            print(f"이메일이 {receiver_email}로 성공적으로 전송되었습니다.")
        except Exception as e:
            print(f"이메일 전송 실패: {e}")