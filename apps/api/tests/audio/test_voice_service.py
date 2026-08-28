import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audio.models import VoiceProfileModel
from app.domains.audio.voice_service import VoiceService
from app.domains.personas.models import Persona
from app.domains.users.service import UserService


@pytest.mark.asyncio
async def test_voice_service_resolution_hierarchy(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    voice_service = VoiceService(db_session)

    # 1. Base defaults
    prov, v_id, spd, ptch = await voice_service.resolve_voice_configuration(user_id=user.id)
    assert prov == "voicevox"
    assert v_id == "1"
    assert spd == 1.0
    assert ptch == 0.0

    # 2. Add user default profile
    profile = VoiceProfileModel(
        user_id=user.id,
        name="My Default Voice",
        provider="voicevox",
        voice_id="8",
        settings_json={"speed": 0.9, "pitch": 0.05},
        is_default=True,
    )
    db_session.add(profile)
    await db_session.commit()

    prov, v_id, spd, ptch = await voice_service.resolve_voice_configuration(user_id=user.id)
    assert v_id == "8"
    assert spd == 0.9
    assert ptch == 0.05

    # 3. Persona overrides user default profile
    persona = Persona(
        id="pers_senpai",
        name="Senpai",
        description="Friendly senpai",
        role="Senpai",
        personality="Helpful and friendly",
        speaking_style="Casual Tameguchi",
    )
    # Give persona custom voice via dynamic attributes or preferences
    setattr(persona, "tts_voice_id", "11")
    setattr(persona, "tts_speed", 1.05)
    setattr(persona, "tts_pitch", 0.0)

    prov, v_id, spd, ptch = await voice_service.resolve_voice_configuration(
        user_id=user.id, persona=persona
    )
    assert v_id == "11"
    assert spd == 1.05

    # 4. Session explicit override takes top priority
    prov, v_id, spd, ptch = await voice_service.resolve_voice_configuration(
        user_id=user.id,
        persona=persona,
        session_override_voice="3",
        session_override_speed=0.75,
    )
    assert v_id == "3"
    assert spd == 0.75
