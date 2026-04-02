# from datetime import datetime
# from enum import Enum
# from uuid import UUID, uuid4
# from pydantic import BaseModel, Field

# class Difficulty(str, Enum):
#     """"""
#     EASY = "easy"
#     MEDIUM = "medium"
#     HARD = "hard"


# # 문제
# class ExamChoice(BaseModel):
#     number: int             # 1~5
#     content: str


# class ExamQuestion(BaseModel):
#     question_id: UUID = Field(default_factory=uuid4)
#     question: str
#     choices: list[ExamChoice]   # 5지선다
#     law_reference: str          # 근거 법령 (예: 국토계획법 제6조)
#     difficulty: Difficulty = Difficulty.MEDIUM


# # 시험 세션
# class ExamStartRequest(BaseModel):
#     topic: str = Field(default="부동산공법", description="시험 주제")
#     num_questions: int = Field(default=10, ge=1, le=20)
#     difficulty: Difficulty = Difficulty.MEDIUM


# class ExamStartResponse(BaseModel):
#     exam_id: UUID = Field(default_factory=uuid4)
#     questions: list[ExamQuestion]
#     started_at: datetime = Field(default_factory=datetime.utcnow)


# # 제출 / 채점
# class ExamAnswer(BaseModel):
#     question_id: UUID
#     selected: int           # 선택한 번호 (1~5)


# class ExamSubmitRequest(BaseModel):
#     exam_id: UUID
#     answers: list[ExamAnswer]


# class ExamAnswerResult(BaseModel):
#     question_id: UUID
#     question: str
#     selected: int
#     correct: int            # 정답 번호
#     is_correct: bool
#     explanation: str        # LLM 생성 해설
#     law_reference: str


# class ExamResult(BaseModel):
#     exam_id: UUID
#     score: float            # 0~100
#     correct_count: int
#     total_count: int
#     results: list[ExamAnswerResult]
#     finished_at: datetime = Field(default_factory=datetime.utcnow)