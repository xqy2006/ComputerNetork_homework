import datetime as dt
from pathlib import Path

from email_verification_service import OUTBOX_DIR, UserStore, deliver_email, make_code


def main() -> None:
    db_path = Path(__file__).resolve().parent / "test_users.db"
    if db_path.exists():
        db_path.unlink()
    store = UserStore(db_path)
    created = dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.timezone.utc)

    code = store.register("hw", "secret", "hw@example.com", created)
    assert code == make_code("hw")
    assert store.verify("hw", code, created + dt.timedelta(minutes=30)) is True

    code2 = store.register("temp", "secret", "temp@example.com", created)
    assert store.verify("temp", code2, created + dt.timedelta(hours=2)) is False

    outbox = deliver_email("demo@example.com", "http://127.0.0.1/verify?user=hw&code=ABCDEF")
    assert outbox.exists()
    assert "ABCDEF" in outbox.read_text(encoding="utf-8")
    print("All email verification tests passed.")


if __name__ == "__main__":
    main()
