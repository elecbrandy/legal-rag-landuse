from src.model.law import LawArticle, LawChunk

# 청크 설정
CHUNK_SIZE = 500        # 최대 글자 수
CHUNK_OVERLAP = 50      # 청크 간 겹침 글자 수


def split_articles(articles: list[LawArticle]) -> list[LawChunk]:
    """
    조문 리스트 → 청크 리스트 변환
    Args:
        articles (list[LawArticle]): 조문 리스트
    Returns:
        list[LawChunk]: 청크 리스트
    """
    chunks: list[LawChunk] = []
    for article in articles:
        chunks.extend(_split_article(article))
    return chunks


def _split_article(article: LawArticle) -> list[LawChunk]:
    """
    단일 조문을 CHUNK_SIZE 기준으로 분할
    Args:
        article (LawArticle): 조문
    Returns:
        list[LawChunk]: 청크 리스트
        """
    text = _build_text(article)

    # 조문이 충분히 짧으면 분할 없이 반환
    if len(text) <= CHUNK_SIZE:
        return [_make_chunk(article, text)]

    # 슬라이딩 윈도우 방식 분할
    chunks: list[LawChunk] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end]
        chunks.append(_make_chunk(article, chunk_text))
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def _build_text(article: LawArticle) -> str:
    """
    조문 메타 정보 + 본문을 하나의 문자열로 조합
    Args:
        article (LawArticle): 조문
    Returns:
        str: 조합된 텍스트
    """
    header = f"[{article.law_name}] {article.article_number}"
    if article.article_title:
        header += f" ({article.article_title})"
    return f"{header}\n{article.content}"


def _make_chunk(article: LawArticle, text: str) -> LawChunk:
    """
    조문과 텍스트로부터 청크를 생성
    Args:
        article (LawArticle): 조문
        text (str): 청크 텍스트
    Returns:
        LawChunk: 생성된 청크
    """
    return LawChunk(
        law_id=article.law_id,
        law_name=article.law_name,
        article=article.article_number,
        content=text,
    )
