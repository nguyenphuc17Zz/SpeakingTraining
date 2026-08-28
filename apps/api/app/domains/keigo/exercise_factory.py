"""Keigo exercise factory — composable scenario dimensions, not hardcoded giant list."""

from __future__ import annotations

import random
from typing import Any

from app.domains.keigo.social_context import Group, PersonRole, Register, Relationship, Situation, SocialContext, SpeechAct
from app.domains.keigo.transformation_engine import KeigoTransformationEngine

# Scenario dimensions (small ontology, not vocabulary)
RELATIONSHIPS = [Relationship.BUSINESS, Relationship.CUSTOMER_PROVIDER, Relationship.PEER, Relationship.HIERARCHICAL]
SITUATIONS = [Situation.BUSINESS_MEETING, Situation.PHONE, Situation.RECEPTION, Situation.EMAIL]
SPEECH_ACTS = [SpeechAct.REQUEST, SpeechAct.APOLOGIZE, SpeechAct.CONFIRM, SpeechAct.REPORT, SpeechAct.INTRODUCE]

# Sample source sentences by register (tiny templates, not database)
SOURCE_TEMPLATES = {
    Register.TAMEGUCHI: [
        "明日、社長に会うよ。",
        "この資料、見た？",
        "ちょっと待って。",
        "お茶を飲む？",
        "田中さんはどこにいる？",
        "この件、知ってる？",
        "メールを送ったよ。",
        "企画書を読んでね。",
        "会議は何時から？",
        "名前を教えて。",
        "後で電話するよ。",
        "この本を借りるね。",
    ],
    Register.POLITE: [
        "明日、社長に会います。",
        "この資料を見ましたか？",
        "少々お待ちください。",
        "お茶を飲みますか？",
        "田中さんはどこにいますか？",
        "この件を知っていますか？",
        "メールを送りました。",
        "企画書を読んでください。",
        "会議は何時からですか？",
        "お名前を教えてください。",
        "後で電話します。",
        "この本をお借りします。",
    ],
    Register.BUSINESS_POLITE: [
        "明日、社長にお会いします。",
        "こちらの資料をご確認いただけますか？",
        "少々お待ちいただけますでしょうか。",
        "お茶をお召し上がりになりますか？",
        "田中様はどちらにいらっしゃいますか？",
        "こちらの件をご存知でしょうか？",
        "メールをお送りいたしました。",
        "企画書をご一読いただけますと幸いです。",
        "会議は何時から始まりますでしょうか？",
        "お名前をお伺いしてもよろしいでしょうか？",
        "後ほどお電話を差し上げます。",
        "こちらの本を拝借いたします。",
    ],
}

TIMER_DEFAULTS = {
    "keigo_sonkeigo": 5000,
    "keigo_kenjougo": 5000,
    "keigo_teineigo": 5000,
    "keigo_transformation": 5000,
    "keigo_context": 6000,
    "keigo_doctor": 5000,
    "keigo_naturalness": 5000,
}


class KeigoExerciseFactory:
    def __init__(self):
        self.engine = KeigoTransformationEngine()

    def _random_context(self, target: Register) -> SocialContext:
        return SocialContext(
            speaker_role=random.choice([PersonRole.SELF, PersonRole.EMPLOYEE]),
            listener_role=random.choice([PersonRole.CUSTOMER, PersonRole.MANAGER, PersonRole.CLIENT]),
            referent_role=random.choice([PersonRole.MANAGER, PersonRole.CUSTOMER, PersonRole.SELF]),
            speaker_group=Group.UCHI,
            listener_group=Group.SOTO if target in (Register.BUSINESS_KEIGO, Register.VERY_FORMAL) else Group.UNKNOWN,
            referent_group=random.choice([Group.UCHI, Group.SOTO]),
            relationship=random.choice(RELATIONSHIPS),
            situation=random.choice(SITUATIONS),
            register_target=target,
            business_context=True,
            familiarity_level=random.randint(1,3),
            hierarchy_level=random.randint(3,5),
        )

    def generate_shift(self, source_register: Register = Register.TAMEGUCHI, target_register: Register = Register.BUSINESS_KEIGO, difficulty: str = "normal") -> dict[str, Any]:
        source = random.choice(SOURCE_TEMPLATES.get(source_register, SOURCE_TEMPLATES[Register.TAMEGUCHI]))
        ctx = self._random_context(target_register)
        result = self.engine.transform(source, target_register, ctx)
        return {
            "title": f"Register Shift: {source_register.value} → {target_register.value}",
            "objective": f"Chuyển '{source}' sang {target_register.value} phù hợp ngữ cảnh {ctx.relationship.value}/{ctx.situation.value}",
            "scenario": f"Bạn là {ctx.speaker_role.value}, nói với {ctx.listener_role.value} ({ctx.relationship.value}) — {ctx.situation.value}",
            "instructions": f"Nghe câu gốc '{source}' và nói lại ở dạng {target_register.value} trước khi hết giờ.",
            "prompt": source,
            "source": source,
            "target_register": target_register.value,
            "canonical": result.canonical,
            "accepted": result.accepted,
            "alternatives": result.alternatives,
            "social_context": ctx.to_dict(),
            "timer_limit_ms": TIMER_DEFAULTS["keigo_transformation"],
            "difficulty": difficulty,
            "constraints": ["Giữ nguyên ý nghĩa, đúng hướng kính ngữ"],
            "target_patterns": result.accepted[:2],
            "estimated_minutes": 4,
        }

    def generate_doctor(self, difficulty: str = "normal") -> dict[str, Any]:
        # Generate valid then mutate
        valid = self.generate_shift(Register.POLITE, Register.BUSINESS_KEIGO, difficulty)
        # Simple mutation: double keigo or wrong direction
        mutated = valid["canonical"] or valid["source"]
        error_type = random.choice(["DOUBLE_KEIGO", "WRONG_DIRECTION", "UNDER_FORMAL"])
        if error_type == "DOUBLE_KEIGO" and "お" in mutated:
            mutated = mutated.replace("お", "お") + "になられる"  # force double
        elif error_type == "WRONG_DIRECTION":
            mutated = mutated.replace("いらっしゃる", "参る").replace("ご覧になる", "拝見する")
        return {
            "title": "Keigo Doctor: Sửa lỗi kính ngữ",
            "objective": "Phát hiện lỗi và nói lại câu đúng",
            "scenario": f"Câu có vấn đề: '{mutated}' — Hãy sửa",
            "instructions": "Nghe câu lỗi, phát hiện loại lỗi và nói lại câu đúng.",
            "prompt": mutated,
            "error_type": error_type,
            "canonical": valid["canonical"],
            "accepted": valid["accepted"],
            "social_context": valid["social_context"],
            "timer_limit_ms": TIMER_DEFAULTS["keigo_doctor"],
            "difficulty": difficulty,
            "constraints": ["Sửa đúng hướng kính ngữ"],
            "target_patterns": valid["accepted"][:1],
            "estimated_minutes": 5,
        }

    def generate_uchi_soto(self, difficulty: str = "normal") -> dict[str, Any]:
        ctx = SocialContext(
            speaker_role=PersonRole.EMPLOYEE,
            listener_role=PersonRole.CUSTOMER,
            referent_role=random.choice([PersonRole.MANAGER, PersonRole.CUSTOMER]),
            speaker_group=Group.UCHI,
            listener_group=Group.SOTO,
            referent_group=Group.UCHI if random.random()<0.5 else Group.SOTO,
            relationship=Relationship.CUSTOMER_PROVIDER,
            situation=Situation.PHONE,
            register_target=Register.BUSINESS_KEIGO,
            business_context=True,
        )
        # Scenario: customer asks about company's president
        if ctx.referent_group == Group.UCHI:
            prompt = "御社の社長は資料をご覧になりましたか？ (Khách hỏi về sếp bên bạn)"
            expected_action = "kenjougo"  # need to humble own president when talking to customer (actually soto? but for uchi president, humble? — simplified)
        else:
            prompt = "田中様は資料をご覧になりましたか？ (Bạn hỏi về khách)"
            expected_action = "sonkeigo"
        result = self.engine.transform("見る", Register.BUSINESS_KEIGO, ctx)
        return {
            "title": "Uchi/Soto Battle",
            "objective": "Chọn đúng hướng kính ngữ theo Uchi/Soto",
            "scenario": prompt,
            "instructions": "Nghe tình huống, trả lời với kính ngữ đúng hướng.",
            "prompt": prompt,
            "expected_direction": expected_action,
            "canonical": result.canonical,
            "accepted": result.accepted,
            "social_context": ctx.to_dict(),
            "timer_limit_ms": TIMER_DEFAULTS["keigo_context"],
            "difficulty": difficulty,
            "constraints": ["Đúng Uchi/Soto, đúng 尊敬/謙譲"],
            "target_patterns": result.accepted[:1],
            "estimated_minutes": 5,
        }

    def generate_situation(self, difficulty: str = "normal") -> dict[str, Any]:
        ctx = self._random_context(Register.BUSINESS_KEIGO)
        acts = random.choice(SPEECH_ACTS)
        prompts = {
            SpeechAct.REQUEST: "お客様の田中様からお電話です。",
            SpeechAct.APOLOGIZE: "申し訳ございません、資料がまだです。",
            SpeechAct.TRANSFER: "少々お待ちいただけますか？担当にお繋ぎします。",
        }
        prompt = prompts.get(acts, "いらっしゃいませ。")
        result = self.engine.transform(prompt, Register.BUSINESS_KEIGO, ctx)
        return {
            "title": f"Situation Response: {acts.value}",
            "objective": "Phản hồi tự nhiên đúng kính ngữ theo tình huống",
            "scenario": f"Tình huống: {prompt} ({ctx.situation.value})",
            "instructions": "Nghe tình huống và trả lời tự nhiên đúng register.",
            "prompt": prompt,
            "speech_act": acts.value,
            "canonical": result.canonical,
            "accepted": result.accepted,
            "social_context": ctx.to_dict(),
            "timer_limit_ms": TIMER_DEFAULTS["keigo_context"],
            "difficulty": difficulty,
            "constraints": ["Tự nhiên, đúng kính ngữ, đủ ý"],
            "target_patterns": [],
            "estimated_minutes": 4,
        }

    def generate_naturalness(self, difficulty: str = "normal") -> dict[str, Any]:
        # Pick a sentence and ask to judge
        base = random.choice(["明日、社長に会うよ。", "お客様が参りました。", "社長が申しました。"])
        # Heuristic: second and third are wrong direction (customer uses kenjougo etc)
        is_natural = base == "明日、社長に会うよ。"  # tame but natural for friend
        label = "NATURAL" if is_natural else "INAPPROPRIATE"
        return {
            "title": "Naturalness Check",
            "objective": "Đánh giá câu có tự nhiên không",
            "scenario": f"Câu: '{base}' — Bạn đánh giá?",
            "instructions": "Chọn NATURAL / SLIGHTLY_AWKWARD / INAPPROPRIATE và nói lại nếu cần.",
            "prompt": base,
            "expected_label": label,
            "canonical": base if is_natural else "明日、社長に会います。",
            "accepted": [base] if is_natural else ["明日、社長に会います。"],
            "social_context": self._random_context(Register.POLITE).to_dict(),
            "timer_limit_ms": TIMER_DEFAULTS["keigo_naturalness"],
            "difficulty": difficulty,
            "constraints": ["Chọn đúng nhãn"],
            "target_patterns": [],
            "estimated_minutes": 3,
        }

    def generate(self, sub_mode: str, **kwargs) -> dict[str, Any]:
        if sub_mode == "keigo_sonkeigo":
            return self.generate_shift(Register.TAMEGUCHI, Register.BUSINESS_KEIGO, **kwargs)
        if sub_mode == "keigo_kenjougo":
            return self.generate_shift(Register.TAMEGUCHI, Register.BUSINESS_KEIGO, **kwargs)
        if sub_mode == "keigo_teineigo":
            return self.generate_shift(Register.TAMEGUCHI, Register.POLITE, **kwargs)
        if sub_mode == "keigo_transformation":
            return self.generate_shift(**kwargs)
        if sub_mode == "keigo_doctor":
            return self.generate_doctor(**kwargs)
        if sub_mode == "keigo_context":
            return self.generate_uchi_soto(**kwargs)
        if sub_mode == "keigo_situation":
            return self.generate_situation(**kwargs)
        if sub_mode == "keigo_naturalness":
            return self.generate_naturalness(**kwargs)
        # fallback
        return self.generate_shift(**kwargs)
