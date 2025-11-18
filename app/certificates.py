import os
from datetime import datetime

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app import db
from app.models import Certificate


def generate_certificate(submission):
    """
    Tạo certificate PDF cho submission (nếu chưa có).
    """
    user = submission.user
    quiz = submission.quiz

    # đã có rồi thì return luôn
    cert = Certificate.query.filter_by(
        user_id=user.id,
        quiz_id=quiz.id,
    ).first()
    if cert:
        return cert

    folder_name = current_app.config.get("CERT_FOLDER", "certificates")
    folder_path = os.path.join(current_app.instance_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    filename = f"cert_user{user.id}_quiz{quiz.id}.pdf"
    full_path = os.path.join(folder_path, filename)

    c = canvas.Canvas(full_path, pagesize=A4)
    width, height = A4

    c.setTitle("Quiz Certificate")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 120, "CERTIFICATE OF ACHIEVEMENT")

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 180, "This is to certify that")

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 220, user.username)

    c.setFont("Helvetica", 14)
    c.drawCentredString(
        width / 2,
        height - 260,
        f"has successfully completed the quiz '{quiz.title}'",
    )

    c.drawCentredString(
        width / 2,
        height - 290,
        f"Score: {submission.score:.1f}/10",
    )

    c.setFont("Helvetica", 12)
    c.drawString(80, 100, f"Issued at: {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}")

    c.drawRightString(width - 80, 100, "Quiz System")

    c.showPage()
    c.save()

    cert = Certificate(
        user_id=user.id,
        quiz_id=quiz.id,
        file_path=filename,
    )
    db.session.add(cert)
    db.session.commit()
    return cert
