"""
migrate_status.py
------------------
Adds the app_status column to the interactions table.
Run ONCE with:
    docker compose exec backend python migrate_status.py
"""

from app import create_app
from app.extensions import db
from sqlalchemy import text


def run():
    app = create_app("development")
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE interactions
                ADD COLUMN IF NOT EXISTS app_status VARCHAR(20) DEFAULT 'saved';
            """))
            conn.commit()
        print("Done! app_status column added to interactions table.")


if __name__ == "__main__":
    run()
