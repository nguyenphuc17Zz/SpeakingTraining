from typing import Any

from pydantic import BaseModel, Field

from app.domains.ai.contracts import AIMessage, AIMessageRole


class PromptTemplate(BaseModel):
    id: str
    name: str
    description: str
    system_template: str
    user_template: str | None = None
    default_temperature: float = 0.7
    metadata: dict[str, Any] = Field(default_factory=dict)

    def render_system(self, context: dict[str, Any]) -> str:
        text = self.system_template
        for key, value in context.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text

    def render_user(self, context: dict[str, Any]) -> str:
        if not self.user_template:
            return ""
        text = self.user_template
        for key, value in context.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text

    def build_messages(self, context: dict[str, Any], user_input: str | None = None) -> list[AIMessage]:
        system_content = self.render_system(context)
        user_content = user_input or self.render_user(context)

        messages = [AIMessage(role=AIMessageRole.SYSTEM, content=system_content)]
        if user_content:
            messages.append(AIMessage(role=AIMessageRole.USER, content=user_content))
        return messages


# Built-in prompt presets for speaking training
BUILTIN_PROMPTS: dict[str, PromptTemplate] = {
    "basic_conversation": PromptTemplate(
        id="basic_conversation",
        name="Japanese Conversation Partner",
        description="Standard natural Japanese conversation partner matching learner level.",
        system_template="""You are {persona_name}, a friendly and supportive Japanese speaking partner.
Your persona speaking style is: {speaking_style}.
The user's target JLPT level is: {difficulty}.
Guidelines:
1. Speak entirely in natural Japanese suited for a {difficulty} learner.
2. Keep replies concise (1-3 sentences) so the user gets maximum speaking turns.
3. If the user makes a minor mistake, subtly model the correct phrase naturally.
4. Keep the tone engaging, warm, and conversational.""",
        user_template="{user_message}",
        default_temperature=0.7,
    ),
    "grammar_correction": PromptTemplate(
        id="grammar_correction",
        name="Grammar & Nuance Correction",
        description="Analyze Japanese sentence for grammar, particle correctness, and natural nuance.",
        system_template="""You are an expert Japanese linguist and speaking coach.
Analyze the user's Japanese utterance.
Provide feedback in a clean structured format:
1. Corrected Sentence (自然な日本語)
2. Explanation of mistakes or unnatural particle usage (文法解説)
3. 2 alternative natural ways native speakers would say it (自然な言い換え)""",
        user_template="{user_message}",
        default_temperature=0.3,
    ),
    "translation_helper": PromptTemplate(
        id="translation_helper",
        name="Japanese Translation & Contextual Nuance",
        description="Translate phrases with polite/casual nuance explanations.",
        system_template="""You are a bilingual Japanese-English coach.
Translate the requested text accurately and explain the cultural / situational context (formal vs casual vs honorific).""",
        user_template="{user_message}",
        default_temperature=0.4,
    ),
}


def get_prompt_template(prompt_id: str) -> PromptTemplate | None:
    return BUILTIN_PROMPTS.get(prompt_id)
