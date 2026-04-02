import httpx
from core.config import get_settings
from model.law import LawArticle

settings = get_settings()

LAW_API_BASE = "https://www.law.go.kr/DRF/lawService.do"

async def fetch_law_articles(law_id: str) -> list[LawArticle]:
    """
    법령 ID로 전체 조문 목록을 가져오기
    Args:
        law_id (str): 법령 ID (예: "0000058811")
    Returns:
        list[LawArticle]: 조문 리스트
    """
    params = {
        "OC": settings.law_api_key,
        "target": "law",
        "type": "JSON",
        "ID": law_id,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(LAW_API_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    return _parse_articles(law_id, data)


def _parse_articles(law_id: str, data: dict) -> list[LawArticle]:
    """
    API 응답 JSON → LawArticle 리스트 변환.
    Args:
        law_id (str): 법령 ID
        data (dict): API 응답 JSON
    Returns:
        list[LawArticle]: 조문 리스트
    """
    law_name: str = data.get("법령명한글", "")
    articles_raw: list[dict] = data.get("조문", [])

    articles: list[LawArticle] = []
    for item in articles_raw:
        content = item.get("조문내용", "").strip()
        if not content:
            continue

        articles.append(
            LawArticle(
                law_id=law_id,
                law_name=law_name,
                article_number=item.get("조문번호", ""),
                article_title=item.get("조문제목", ""),
                content=content,
            )
        )

    return articles