from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ExampleSentence(BaseModel):
    ja: str = Field(description="Câu ví dụ thực tế bằng tiếng Nhật tự nhiên")
    vi: str = Field(description="Dịch nghĩa tiếng Việt tự nhiên, chuẩn ngữ cảnh")
    situation: str = Field(
        default="",
        description="Bối cảnh/Tình huống giao tiếp (vd: Trong cuộc họp với cấp trên, Khi trò chuyện với bạn thân)",
    )


class AlternativeItem(BaseModel):
    expression: str = Field(description="Từ/cụm từ thay thế hoặc đồng nghĩa")
    reading: str = Field(description="Cách đọc (Hiragana/Furigana)")
    meaning_vi: str = Field(description="Nghĩa tiếng Việt")
    difference_explanation: str = Field(
        description="Giải thích sự khác biệt về sắc thái (độ trang trọng, hoàn cảnh dùng, mức độ cảm xúc) so với từ gốc"
    )


class BestMatch(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    expression: str = Field(description="Từ hoặc cụm từ chuẩn xác (dạng kanji/từ điển phù hợp)")
    reading: str = Field(description="Cách đọc Hiragana / Furigana")
    meaning_vi: str = Field(description="Nghĩa tiếng Việt chuẩn xác nhất trong ngữ cảnh câu đã cho")
    part_of_speech: str = Field(
        default="Từ vựng",
        description="Từ loại (Danh từ, Động từ nhóm 1/2/3, Tính từ đuôi い/な, Phó từ, Quán dụng ngữ, v.v.)",
    )
    jlpt_level: str = Field(default="N3", description="Cấp độ ước tính (N5, N4, N3, N2, N1)")
    register: str = Field(
        default="Polite",
        description="Sắc thái / Phong cách giao tiếp (Casual / Thân mật, Polite / Lịch sự, Business Keigo / Kính ngữ công sở)",
    )
    naturalness_score: int = Field(
        default=95,
        description="Điểm độ tự nhiên trong văn cảnh (0-100)",
    )
    nuance_explanation: str = Field(
        description="Phân tích sư phạm chuyên sâu: vì sao từ vựng này phù hợp trong ngữ cảnh câu văn đã bôi đen, thái độ/hàm ý của người nói",
    )
    usage_collocation: str = Field(
        default="",
        description="Cụm từ liên kết tự nhiên (Collocations thường đi cùng)",
    )
    examples: list[ExampleSentence] = Field(
        default_factory=list,
        description="Tối thiểu 2 câu ví dụ thực tế kèm hoàn cảnh và bản dịch tiếng Việt",
    )


class VocabularyLookupRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Từ vựng hoặc cụm từ được bôi đen cần tra cứu")
    context: str = Field(
        default="",
        max_length=2000,
        description="Ngữ cảnh xung quanh (nguyên câu văn hoặc đoạn văn chứa từ)",
    )
    target_level: str = Field(
        default="N3",
        description="Cấp độ mục tiêu của người học (N5, N4, N3, N2, N1)",
    )
    register_preference: str = Field(
        default="auto",
        description="Tùy chọn sắc thái mong muốn: auto, casual, polite, business",
    )


class VocabularyLookupResponse(BaseModel):
    best_match: BestMatch
    alternatives: list[AlternativeItem] = Field(default_factory=list)
    original_query: str
    context: str = ""
    searched_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SaveVocabularyNotebookRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    expression: str = Field(..., description="Từ hoặc cụm từ")
    reading: str = Field(default="", description="Cách đọc Hiragana")
    meaning_vi: str = Field(..., description="Nghĩa tiếng Việt")
    nuance_explanation: str = Field(default="", description="Giải thích sắc thái")
    context: str = Field(default="", description="Câu văn mẫu / ngữ cảnh trích xuất")
    jlpt_level: str = Field(default="N3", description="Cấp độ JLPT")
    part_of_speech: str = Field(default="Từ vựng", description="Từ loại")
    register: str = Field(default="Polite", description="Sắc thái giao tiếp")
    tags: list[str] = Field(default_factory=list, description="Thẻ phân loại")


class SaveVocabularyNotebookResponse(BaseModel):
    success: bool
    item_id: str
    message: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
