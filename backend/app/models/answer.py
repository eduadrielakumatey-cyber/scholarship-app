"""
app/models/answer.py
-----------------------
A student's answer to one of a scholarship's application questions
(Scholarship.questions), saved as they type so they can paste it into the
official form. Keyed by the question's stable key, not its position.
"""

from datetime import datetime

from app.extensions import db


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scholarship_id = db.Column(
        db.Integer, db.ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_key = db.Column(db.String(16), nullable=False)
    body = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "scholarship_id", "question_key", name="uq_answer_user_question"),
    )
