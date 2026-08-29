import glob
import os

files = [
    r"E:\SpeakingTraining\apps\web\features\reflex\components\ReflexPromptCard.tsx",
    r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoPromptCard.tsx",
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsPromptCard.tsx",
    r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchPromptCard.tsx",
    r"E:\SpeakingTraining\apps\web\features\coach\components\DailySenseiBriefingCard.tsx",
    r"E:\SpeakingTraining\apps\web\features\gamification\components\DojoBossArenaModal.tsx",
    r"E:\SpeakingTraining\apps\web\components\japanese\UniversalFurigana.tsx",
    r"E:\SpeakingTraining\apps\web\components\japanese\GlobalFuriganaControl.tsx",
]

# Check all tsx files in features and components
all_tsx = glob.glob(r"E:\SpeakingTraining\apps\web\**\*.tsx", recursive=True)

for path in all_tsx:
    if "node_modules" in path or ".next" in path:
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if '"use client";' in content or "'use client';" in content:
        # Check if it's already on line 1
        lines = content.strip().split("\n")
        first_line = lines[0].strip()
        if first_line not in ('"use client";', "'use client';"):
            # Remove all occurrences of "use client"; and put on line 1
            cleaned = []
            for line in lines:
                if line.strip() in ('"use client";', "'use client';"):
                    continue
                cleaned.append(line)
            new_content = '"use client";\n\n' + "\n".join(cleaned).strip() + "\n"
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed 'use client' at top in: {os.path.basename(path)}")

print("All TSX files checked and fixed!")
