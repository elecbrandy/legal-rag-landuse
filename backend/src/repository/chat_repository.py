import aiosqlite
from uuid import UUID
from model.chat import ChatMessage
from core.config import get_settings

settings = get_settings()
DB_PATH = settings.sqlite_db_path

async def init_db() -> None:
    """
    앱 시작 시 테이블 생성.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                role        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            )
        """)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_session ON chat_messages(session_id)"
        )
        await db.commit()

async def save_message(message: ChatMessage) -> None:
    """
    단일 메시지 저장
    Args:
        message (ChatMessage): 저장할 메시지 객체
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(message.session_id),
                message.role,
                message.content,
                message.created_at.isoformat(),
            ),
        )
        await db.commit()


async def get_history(session_id: UUID, limit: int = 20) -> list[ChatMessage]:
    """
    세션 ID로 최근 대화 히스토리 조회
    Args:
        session_id (UUID): 대화 세션 ID
        limit (int): 조회할 메시지 수 (기본 20)
    Returns:
        list[ChatMessage]: 메시지 리스트 (최신순)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (str(session_id), limit),
        ) as cursor:
            rows = await cursor.fetchall()

    # 최신순으로 가져왔으니 역순으로 반환
    return [
        ChatMessage(
            id=row["id"],
            session_id=UUID(row["session_id"]),
            role=row["role"],
            content=row["content"],
        )
        for row in reversed(rows)
    ]


async def delete_session(session_id: UUID) -> int:
    """
    세션 전체 삭제. 삭제된 메시지 수 반환.
    Args:
        session_id (UUID): 삭제할 세션 ID
    Returns:
        int: 삭제된 메시지 수
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM chat_messages WHERE session_id = ?",
            (str(session_id),),
        )
        await db.commit()
        return cursor.rowcount