import re

# 1. Update ReflexPromptCard.tsx
reflex_path = r"E:\SpeakingTraining\apps\web\features\reflex\components\ReflexPromptCard.tsx"
with open(reflex_path, "r", encoding="utf-8") as f:
    r_text = f.read()

if "UniversalFurigana" not in r_text:
    r_text = 'import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";\n' + r_text
    r_text = r_text.replace(
        '<div className="text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground">\n                {verb || prompt}\n              </div>',
        '<div className="text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground flex justify-center">\n                <UniversalFurigana text={verb || prompt} fontSize="xl" />\n              </div>'
    )
    r_text = r_text.replace(
        '<div className="text-xl md:text-2xl font-bold font-jp leading-relaxed text-foreground tracking-tight">\n                {prompt}\n              </div>',
        '<div className="text-lg md:text-xl font-bold font-jp leading-relaxed text-foreground tracking-tight flex justify-center">\n                <UniversalFurigana text={prompt} fontSize="lg" />\n              </div>'
    )
    with open(reflex_path, "w", encoding="utf-8") as f:
        f.write(r_text)
    print("Updated ReflexPromptCard.tsx with UniversalFurigana")

# 2. Update KeigoPromptCard.tsx
keigo_path = r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoPromptCard.tsx"
with open(keigo_path, "r", encoding="utf-8") as f:
    k_text = f.read()

if "UniversalFurigana" not in k_text:
    k_text = 'import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";\n' + k_text
    # Replace plain text in Keigo prompt
    k_text = k_text.replace(
        '"{prompt.targetSentence}"',
        '<UniversalFurigana text={prompt.targetSentence} fontSize="lg" />'
    )
    k_text = k_text.replace(
        '"{prompt.rawText}"',
        '<UniversalFurigana text={prompt.rawText} fontSize="lg" />'
    )
    with open(keigo_path, "w", encoding="utf-8") as f:
        f.write(k_text)
    print("Updated KeigoPromptCard.tsx with UniversalFurigana")

# 3. Update SituationsPromptCard.tsx
sit_path = r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsPromptCard.tsx"
with open(sit_path, "r", encoding="utf-8") as f:
    s_text = f.read()

if "UniversalFurigana" not in s_text:
    s_text = 'import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";\n' + s_text
    s_text = s_text.replace(
        '"{prompt.speakerLine}"',
        '<UniversalFurigana text={prompt.speakerLine} fontSize="lg" />'
    )
    with open(sit_path, "w", encoding="utf-8") as f:
        f.write(s_text)
    print("Updated SituationsPromptCard.tsx with UniversalFurigana")

# 4. Update PitchPromptCard.tsx
pitch_path = r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchPromptCard.tsx"
with open(pitch_path, "r", encoding="utf-8") as f:
    p_text = f.read()

if "UniversalFurigana" not in p_text:
    p_text = 'import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";\n' + p_text
    p_text = p_text.replace(
        '"{prompt.target_word || prompt.word}"',
        '<UniversalFurigana text={prompt.target_word || prompt.word || ""} fontSize="xl" />'
    )
    with open(pitch_path, "w", encoding="utf-8") as f:
        f.write(p_text)
    print("Updated PitchPromptCard.tsx with UniversalFurigana")

# 5. Update DailySenseiBriefingCard.tsx
brief_path = r"E:\SpeakingTraining\apps\web\features\coach\components\DailySenseiBriefingCard.tsx"
with open(brief_path, "r", encoding="utf-8") as f:
    b_text = f.read()

if "UniversalFurigana" not in b_text:
    b_text = 'import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";\n' + b_text
    b_text = b_text.replace(
        '"{briefing.daily_phrase_ja}"',
        '<UniversalFurigana text={briefing.daily_phrase_ja} fontSize="lg" />'
    )
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(b_text)
    print("Updated DailySenseiBriefingCard.tsx with UniversalFurigana")

# 6. Update DojoBossArenaModal.tsx
boss_arena_path = r"E:\SpeakingTraining\apps\web\features\gamification\components\DojoBossArenaModal.tsx"
with open(boss_arena_path, "r", encoding="utf-8") as f:
    ba_text = f.read()

if "UniversalFurigana" not in ba_text:
    ba_text = 'import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";\n' + ba_text
    ba_text = ba_text.replace(
        '"{currentPromptJa}"',
        '<UniversalFurigana text={currentPromptJa} fontSize="lg" />'
    )
    with open(boss_arena_path, "w", encoding="utf-8") as f:
        f.write(ba_text)
    print("Updated DojoBossArenaModal.tsx with UniversalFurigana")

print("All components integrated with UniversalFurigana successfully!")
