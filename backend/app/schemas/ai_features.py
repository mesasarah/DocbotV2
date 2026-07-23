from pydantic import BaseModel


class SummaryResponse(BaseModel):
    document_id: str
    executive_summary: str
    bullet_points: list[str]
    key_insights: list[str]


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizResponse(BaseModel):
    document_id: str
    questions: list[QuizQuestion]
