import httpx
import xml.etree.ElementTree as ET
from src.core.config import get_settings
from src.model.law import LawArticle

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

async def search_law_id_by_name(law_name: str) -> str | None:
    """
    법령명으로 검색하여 법령일련번호(MST)를 반환.
    Args:
        law_name (str): 검색할 법령명 (예: "국토계획법")
    Returns:
        str | None: 일련번호(MST) 또는 검색 실패 시 None
    """
    url = "http://www.law.go.kr/DRF/lawSearch.do"
    params = {
        "OC": settings.law_api_key,
        "target": "law",
        "type": "XML",
        "query": law_name,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None
        
        root = ET.fromstring(resp.content)
        for law in root.findall(".//law"):
            fetched_name = law.findtext("법령명한글")
            mst = law.findtext("법령일련번호")
            
            # 검색 결과 중 이름이 정확히 일치하는 것만 추출
            if fetched_name and fetched_name.strip() == law_name:
                return mst
                
    return None