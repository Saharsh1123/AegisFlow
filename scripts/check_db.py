from sqlalchemy import text

from app.db.session import SessionLocal


def main():
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT 1"))
        print(result.scalar())
    finally:
        db.close()


if __name__ == "__main__":
    main()