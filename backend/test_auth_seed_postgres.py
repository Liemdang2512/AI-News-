import asyncio


class _FakePool:
    def __init__(self):
        self.calls = []

    async def execute(self, sql, *args):
        self.calls.append((sql, args))


def _store(monkeypatch):
    # Import lazily: other auth tests set env vars before importing config/main,
    # so importing auth_store at collection time would freeze the wrong settings.
    from services import auth_store

    # monkeypatch restores originals so other tests keep their seeded state
    monkeypatch.setattr(auth_store, "_mem_users_by_email", {})
    monkeypatch.setattr(auth_store, "_mem_users_by_id", {})
    monkeypatch.setattr(auth_store, "_mem_user_id_seq", 1)
    return auth_store


def test_regular_user_seeded_into_postgres_not_memory(monkeypatch):
    auth_store = _store(monkeypatch)
    pool = _FakePool()

    async def fake_get_pool():
        return pool

    monkeypatch.setattr(auth_store, "_storage_mode", lambda: "postgres")
    monkeypatch.setattr(auth_store, "_get_pool", fake_get_pool)

    asyncio.run(auth_store._seed_user_if_missing("User@Example.com", "hash"))

    assert len(pool.calls) == 1
    sql, args = pool.calls[0]
    assert "ON CONFLICT (email) DO NOTHING" in sql
    assert args == ("user@example.com", "hash")
    assert "user@example.com" not in auth_store._mem_users_by_email


def test_regular_user_seeded_into_memory_when_not_postgres(monkeypatch):
    auth_store = _store(monkeypatch)
    monkeypatch.setattr(auth_store, "_storage_mode", lambda: "memory")

    asyncio.run(auth_store._seed_user_if_missing("a@b.c", "hash"))

    assert "a@b.c" in auth_store._mem_users_by_email
