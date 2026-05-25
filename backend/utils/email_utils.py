import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "panaderia.victoria.sistema@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "hendry.angeldones09@gmail.com")


SENDER_NAME = "Panadería Victoria"
FROM_ADDRESS = f"{SENDER_NAME} <{SMTP_EMAIL}>"


def enviar_email_pdf(
    destinatario: str,
    asunto: str,
    cuerpo: str,
    pdf_bytes: bytes,
    filename: str,
) -> bool:
    if not SMTP_PASSWORD:
        print("[EMAIL] SMTP_PASSWORD no configurado. Revisa .env")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_ADDRESS
        msg["To"] = destinatario
        msg["Subject"] = asunto

        msg.attach(MIMEText(cuerpo, "plain"))

        attach = MIMEBase("application", "pdf")
        attach.set_payload(pdf_bytes)
        encoders.encode_base64(attach)
        attach.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(attach)

        with smtplib.SMTP("smtp.gmail.com", 587, local_hostname="localhost") as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] OK: {filename} enviado a {destinatario}")
        return True

    except Exception as e:
        print(f"[EMAIL] Error: {e}")
        return False
