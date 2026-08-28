import { VoiceProfile } from "@/types/audio";

export interface VoiceCharacterMeta {
  gender: "female" | "male" | "mascot";
  genderLabel: string;
  vibe: "cute" | "energetic" | "calm" | "cool" | "deep" | "gentle";
  vibeLabel: string;
  avatarLetter: string;
  gradient: string;
  borderAccent: string;
  badgeClass: string;
  recommendedFor: string;
  descriptionVi: string;
}

export interface SamplePhrase {
  id: string;
  category: "daily" | "beginner_n5" | "natural_n3" | "keigo" | "food";
  label: string;
  icon: string;
  text: string;
  romaji: string;
  translationVi: string;
}

export const SAMPLE_PHRASES: SamplePhrase[] = [
  {
    id: "daily",
    category: "daily",
    label: "Chào hỏi",
    icon: "🌸",
    text: "こんにちは！今日も一緒に楽しく日本語を練習しましょう。",
    romaji: "Konnichiwa! Kyou mo issho ni tanoshiku nihongo o renshuu shimashou.",
    translationVi: "Chào bạn! Hôm nay chúng ta hãy cùng vui vẻ luyện tiếng Nhật nhé.",
  },
  {
    id: "beginner_n5",
    category: "beginner_n5",
    label: "N5 Sơ cấp",
    icon: "🐢",
    text: "これは 私の 日本語の ノートです。",
    romaji: "Kore wa watashi no nihongo no nooto desu.",
    translationVi: "Đây là cuốn sổ tay tiếng Nhật của tôi.",
  },
  {
    id: "natural_n3",
    category: "natural_n3",
    label: "Hội thoại N3",
    icon: "💬",
    text: "週末は何をして過ごす予定ですか？",
    romaji: "Shuumatsu wa nani o shite sugosu yotei desu ka?",
    translationVi: "Cuối tuần này bạn dự định làm gì thế?",
  },
  {
    id: "keigo",
    category: "keigo",
    label: "Kính ngữ Keigo",
    icon: "👔",
    text: "お忙しいところ恐れ入りますが、ご確認のほどよろしくお願いいたします。",
    romaji: "Oisogashii tokoro osoreirimasu ga, gokakunin no hodo yoroshiku onegai itashimasu.",
    translationVi: "Xin thứ lỗi vì làm phiền lúc bận rộn, xin vui lòng kiểm tra giúp tôi.",
  },
  {
    id: "food",
    category: "food",
    label: "Quán café / Ăn uống",
    icon: "🍵",
    text: "すみません、アイスコーヒーをひとつお願いできますか？",
    romaji: "Sumimasen, aisu koohii o hitotsu onegai dekimasu ka?",
    translationVi: "Xin lỗi, cho tôi xin một ly cà phê đá được không ạ?",
  },
];

export function getVoiceCharacterMeta(voice: VoiceProfile): VoiceCharacterMeta {
  const name = (voice.name || "").toLowerCase();

  // Zundamon
  if (name.includes("zundamon") || name.includes("ずんだもん")) {
    return {
      gender: "mascot",
      genderLabel: "Linh vật / Anime",
      vibe: "energetic",
      vibeLabel: "Nhí nhảnh · Dễ thương",
      avatarLetter: "ず",
      gradient: "from-emerald-400 to-lime-500",
      borderAccent: "border-emerald-500/40",
      badgeClass: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30",
      recommendedFor: "Luyện phản xạ nhanh, vui vẻ",
      descriptionVi: "Giọng linh vật đậu nành Zundamon đặc trưng, cao vút và tràn đầy năng lượng.",
    };
  }

  // Shikoku Metan
  if (name.includes("metan") || name.includes("めたん")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "calm",
      vibeLabel: "Điềm tĩnh · Trong trẻo",
      avatarLetter: "め",
      gradient: "from-pink-400 to-rose-500",
      borderAccent: "border-pink-500/40",
      badgeClass: "bg-pink-500/15 text-pink-600 dark:text-pink-300 border-pink-500/30",
      recommendedFor: "Luyện phát âm chuẩn N5 - N3",
      descriptionVi: "Giọng nữ thanh lịch, phát âm rõ từng mora, rất thích hợp cho người mới bắt đầu.",
    };
  }

  // Kasukabe Tsumugi
  if (name.includes("tsumugi") || name.includes("つむぎ")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "cute",
      vibeLabel: "Hoạt bát · Tự nhiên",
      avatarLetter: "つ",
      gradient: "from-amber-400 to-orange-500",
      borderAccent: "border-amber-500/40",
      badgeClass: "bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30",
      recommendedFor: "Giao tiếp hàng ngày, ngữ điệu thực tế",
      descriptionVi: "Giọng nữ trẻ trung như bạn bè cùng lớp, ngữ điệu tươi vui và tự nhiên.",
    };
  }

  // Amehare Hau
  if (name.includes("hau") || name.includes("はう")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "gentle",
      vibeLabel: "Dịu dàng · Y tá",
      avatarLetter: "は",
      gradient: "from-teal-400 to-emerald-500",
      borderAccent: "border-teal-500/40",
      badgeClass: "bg-teal-500/15 text-teal-600 dark:text-teal-300 border-teal-500/30",
      recommendedFor: "Ngữ điệu ân cần, hướng dẫn",
      descriptionVi: "Giọng nữ y tá Amehare Hau trong trẻo, ân cần và từ tốn.",
    };
  }

  // Namino Ritsu
  if (name.includes("ritsu") || name.includes("リツ")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "cool",
      vibeLabel: "Cá tính · Rõ ràng",
      avatarLetter: "り",
      gradient: "from-indigo-400 to-purple-500",
      borderAccent: "border-indigo-500/40",
      badgeClass: "bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 border-indigo-500/30",
      recommendedFor: "Shadowing tốc độ cao",
      descriptionVi: "Giọng nữ đĩnh đạc, phát âm sắc nét và dứt khoát.",
    };
  }

  // Kurono Takehiro
  if (name.includes("takehiro") || name.includes("kurono") || name.includes("玄野")) {
    return {
      gender: "male",
      genderLabel: "Nam",
      vibe: "energetic",
      vibeLabel: "Trẻ trung · Thân thiện",
      avatarLetter: "玄",
      gradient: "from-blue-400 to-cyan-500",
      borderAccent: "border-blue-500/40",
      badgeClass: "bg-blue-500/15 text-blue-600 dark:text-blue-300 border-blue-500/30",
      recommendedFor: "Hội thoại bạn bè, đời sống",
      descriptionVi: "Giọng nam thanh niên tươi sáng, lịch sự và gần gũi.",
    };
  }

  // Shirakami Kotaro
  if (name.includes("kotaro") || name.includes("虎太郎") || name.includes("白上")) {
    return {
      gender: "male",
      genderLabel: "Nam",
      vibe: "cute",
      vibeLabel: "Nhí nhảnh · Cậu bé",
      avatarLetter: "虎",
      gradient: "from-amber-500 to-yellow-600",
      borderAccent: "border-amber-500/40",
      badgeClass: "bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30",
      recommendedFor: "Hội thoại đời thường dễ thương",
      descriptionVi: "Giọng bé trai Shirakami Kotaro vui vẻ, hồn nhiên.",
    };
  }

  // Aoyama Ryusei
  if (name.includes("ryusei") || name.includes("aoyama") || name.includes("青山")) {
    return {
      gender: "male",
      genderLabel: "Nam",
      vibe: "deep",
      vibeLabel: "Trầm ấm · Chuẩn mực",
      avatarLetter: "青",
      gradient: "from-slate-600 to-indigo-800",
      borderAccent: "border-slate-500/40",
      badgeClass: "bg-slate-500/15 text-slate-700 dark:text-slate-300 border-slate-500/30",
      recommendedFor: "Kính ngữ, phỏng vấn, tin tức",
      descriptionVi: "Giọng nam trầm ấm, phát âm đĩnh đạc như phát thanh viên đài NHK.",
    };
  }

  // Meimei Himari
  if (name.includes("himari") || name.includes("冥鳴")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "gentle",
      vibeLabel: "Dịu dàng · Thì thầm",
      avatarLetter: "冥",
      gradient: "from-purple-400 to-pink-500",
      borderAccent: "border-purple-500/40",
      badgeClass: "bg-purple-500/15 text-purple-600 dark:text-purple-300 border-purple-500/30",
      recommendedFor: "Luyện nghe ngữ điệu nhẹ nhàng",
      descriptionVi: "Giọng nữ mềm mại, thì thầm ngọt ngào.",
    };
  }

  // Kyushu Sora
  if (name.includes("sora") || name.includes("九州")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "calm",
      vibeLabel: "Cô giáo · Ôn hòa",
      avatarLetter: "空",
      gradient: "from-sky-400 to-blue-500",
      borderAccent: "border-sky-500/40",
      badgeClass: "bg-sky-500/15 text-sky-600 dark:text-sky-300 border-sky-500/30",
      recommendedFor: "Bài giảng, chỉ dẫn ngữ pháp",
      descriptionVi: "Giọng nữ dịu dàng như cô giáo người Nhật hướng dẫn phát âm.",
    };
  }

  // Mochiko-san
  if (name.includes("mochiko") || name.includes("もち子")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "calm",
      vibeLabel: "Chị gái · Trưởng thành",
      avatarLetter: "餅",
      gradient: "from-rose-400 to-amber-500",
      borderAccent: "border-rose-500/40",
      badgeClass: "bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30",
      recommendedFor: "Hội thoại tự nhiên chuẩn mực",
      descriptionVi: "Giọng nữ Mochiko-san trưởng thành, ấm áp và gần gũi.",
    };
  }

  // Kenzaki Mesuo
  if (name.includes("mesuo") || name.includes("剣崎")) {
    return {
      gender: "male",
      genderLabel: "Nam",
      vibe: "energetic",
      vibeLabel: "Bác sĩ · Tri thức",
      avatarLetter: "剣",
      gradient: "from-emerald-600 to-teal-700",
      borderAccent: "border-emerald-500/40",
      badgeClass: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30",
      recommendedFor: "Chuyên môn, đàm thoại",
      descriptionVi: "Giọng Kenzaki Mesuo bác sĩ trí tuệ và linh hoạt.",
    };
  }

  // WhiteCUL
  if (name.includes("whitecul") || name.includes("cul")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "cool",
      vibeLabel: "Lạnh lùng · Trong suốt",
      avatarLetter: "W",
      gradient: "from-slate-300 to-indigo-400",
      borderAccent: "border-indigo-400/40",
      badgeClass: "bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 border-indigo-500/30",
      recommendedFor: "Luyện phát âm rõ ràng",
      descriptionVi: "Giọng nữ WhiteCUL trong trẻo, phong cách anime cuốn hút.",
    };
  }

  // Tohoku Trio: Zunko, Kiritan, Itako
  if (name.includes("ずん子") || name.includes("zunko")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "calm",
      vibeLabel: "Trang nhã · Dịu dàng",
      avatarLetter: "ず",
      gradient: "from-emerald-500 to-green-600",
      borderAccent: "border-emerald-500/40",
      badgeClass: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30",
      recommendedFor: "Phát âm chuẩn tiếng Nhật",
      descriptionVi: "Giọng nữ Tohoku Zunko chuẩn mực, êm dịu.",
    };
  }

  if (name.includes("きりたん") || name.includes("kiritan")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "cute",
      vibeLabel: "Dễ thương · Nhí nhảnh",
      avatarLetter: "き",
      gradient: "from-amber-400 to-rose-400",
      borderAccent: "border-rose-400/40",
      badgeClass: "bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30",
      recommendedFor: "Phản xạ nhanh, vui tươi",
      descriptionVi: "Giọng bé gái Tohoku Kiritan tinh nghịch và đáng yêu.",
    };
  }

  if (name.includes("イタコ") || name.includes("itako")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "gentle",
      vibeLabel: "Trang nghiêm · Kính ngữ",
      avatarLetter: "イ",
      gradient: "from-purple-500 to-indigo-600",
      borderAccent: "border-purple-500/40",
      badgeClass: "bg-purple-500/15 text-purple-600 dark:text-purple-300 border-purple-500/30",
      recommendedFor: "Luyện kính ngữ Keigo",
      descriptionVi: "Giọng chị cả Tohoku Itako thanh nhã, phù hợp đàm thoại lịch thiệp.",
    };
  }

  // Chibi Shikijii
  if (name.includes("式じい") || name.includes("shikijii")) {
    return {
      gender: "male",
      genderLabel: "Nam",
      vibe: "deep",
      vibeLabel: "Cụ già · Uyên bác",
      avatarLetter: "爺",
      gradient: "from-stone-600 to-amber-800",
      borderAccent: "border-amber-700/40",
      badgeClass: "bg-amber-700/15 text-amber-700 dark:text-amber-300 border-amber-700/30",
      recommendedFor: "Truyện kể, phong thái cổ kính",
      descriptionVi: "Giọng ông lão Chibi Shikijii hóm hỉnh và uyên thâm.",
    };
  }

  // Nurse Robot
  if (name.includes("ナースロボ") || name.includes("nurse")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "cool",
      vibeLabel: "Robot · Trong trẻo",
      avatarLetter: "Ｔ",
      gradient: "from-cyan-400 to-blue-500",
      borderAccent: "border-cyan-500/40",
      badgeClass: "bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 border-cyan-500/30",
      recommendedFor: "Luyện nghe ngữ điệu đều đặn",
      descriptionVi: "Giọng y tá robot Type T độc đáo, rành mạch và dễ bắt âm.",
    };
  }

  // Chugoku Usagi
  if (name.includes("うさぎ") || name.includes("usagi")) {
    return {
      gender: "female",
      genderLabel: "Nữ",
      vibe: "cute",
      vibeLabel: "Ngây thơ · Mềm mại",
      avatarLetter: "兎",
      gradient: "from-pink-300 to-rose-400",
      borderAccent: "border-pink-400/40",
      badgeClass: "bg-pink-400/15 text-pink-600 dark:text-pink-300 border-pink-400/30",
      recommendedFor: "Luyện phát âm nhẹ nhàng",
      descriptionVi: "Giọng nữ Chugoku Usagi mềm mại, ngọt ngào như thỏ con.",
    };
  }

  // Male names detection
  const MALE_LOOKUP = [
    "玄野", "虎太郎", "青山", "剣崎", "式じい", "紅桜", "雀松", "麒ヶ島", "まろん", "ナマハゲ"
  ];
  const isMale =
    voice.gender === "male" ||
    MALE_LOOKUP.some((m) => name.includes(m.toLowerCase())) ||
    name.includes("男") ||
    name.includes("male");

  const avatarChar = (voice.name || "V").slice(0, 1).toUpperCase();

  return {
    gender: isMale ? "male" : "female",
    genderLabel: isMale ? "Nam" : "Nữ",
    vibe: isMale ? "deep" : "calm",
    vibeLabel: isMale ? "Nam tính · Rõ ràng" : "Nữ tính · Tự nhiên",
    avatarLetter: avatarChar,
    gradient: isMale ? "from-blue-500 to-indigo-600" : "from-rose-500 to-purple-600",
    borderAccent: isMale ? "border-blue-500/30" : "border-rose-500/30",
    badgeClass: isMale
      ? "bg-blue-500/15 text-blue-600 dark:text-blue-300 border-blue-500/30"
      : "bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30",
    recommendedFor: "Luyện giao tiếp tiếng Nhật",
    descriptionVi: voice.description || `Giọng đọc ${voice.name} tự nhiên từ VOICEVOX.`,
  };
}

export const VOICEVOX_FALLBACK_CATALOG: VoiceProfile[] = [
  { id: "1", voice_id: "1", provider: "voicevox", name: "四国めたん (Shikoku Metan - Normal)", style: "Normal", gender: "female", is_default: true },
  { id: "2", voice_id: "2", provider: "voicevox", name: "四国めたん (Shikoku Metan - あまあま)", style: "あまあま", gender: "female" },
  { id: "3", voice_id: "3", provider: "voicevox", name: "四国めたん (Shikoku Metan - ツンツン)", style: "ツンツン", gender: "female" },
  { id: "4", voice_id: "4", provider: "voicevox", name: "四国めたん (Shikoku Metan - セクシー)", style: "セクシー", gender: "female" },
  { id: "5", voice_id: "5", provider: "voicevox", name: "ずんだもん (Zundamon - Normal)", style: "Normal", gender: "female" },
  { id: "6", voice_id: "6", provider: "voicevox", name: "ずんだもん (Zundamon - あまあま)", style: "あまあま", gender: "female" },
  { id: "7", voice_id: "7", provider: "voicevox", name: "ずんだもん (Zundamon - ツンツン)", style: "ツンツン", gender: "female" },
  { id: "8", voice_id: "8", provider: "voicevox", name: "ずんだもん (Zundamon - セクシー)", style: "セクシー", gender: "female" },
  { id: "9", voice_id: "9", provider: "voicevox", name: "ずんだもん (Zundamon - ささやき)", style: "ささやき", gender: "female" },
  { id: "10", voice_id: "10", provider: "voicevox", name: "春日部つむぎ (Kasukabe Tsumugi - Normal)", style: "Normal", gender: "female" },
  { id: "11", voice_id: "11", provider: "voicevox", name: "雨晴はう (Amehare Hau - Normal)", style: "Normal", gender: "female" },
  { id: "12", voice_id: "12", provider: "voicevox", name: "波音リツ (Namino Ritsu - Normal)", style: "Normal", gender: "female" },
  { id: "13", voice_id: "13", provider: "voicevox", name: "波音リツ (Namino Ritsu - クイーン)", style: "クイーン", gender: "female" },
  { id: "14", voice_id: "14", provider: "voicevox", name: "玄野武宏 (Kurono Takehiro - Normal)", style: "Normal", gender: "male" },
  { id: "15", voice_id: "15", provider: "voicevox", name: "玄野武宏 (Kurono Takehiro - 喜び)", style: "喜び", gender: "male" },
  { id: "16", voice_id: "16", provider: "voicevox", name: "玄野武宏 (Kurono Takehiro - ツンツン)", style: "ツンツン", gender: "male" },
  { id: "17", voice_id: "17", provider: "voicevox", name: "白上虎太郎 (Shirakami Kotaro - ふつう)", style: "ふつう", gender: "male" },
  { id: "18", voice_id: "18", provider: "voicevox", name: "白上虎太郎 (Shirakami Kotaro - わーい)", style: "わーい", gender: "male" },
  { id: "19", voice_id: "19", provider: "voicevox", name: "青山龍星 (Aoyama Ryusei - Normal)", style: "Normal", gender: "male" },
  { id: "20", voice_id: "20", provider: "voicevox", name: "青山龍星 (Aoyama Ryusei - 熱血)", style: "熱血", gender: "male" },
  { id: "21", voice_id: "21", provider: "voicevox", name: "冥鳴ひまり (Meimei Himari - Normal)", style: "Normal", gender: "female" },
  { id: "22", voice_id: "22", provider: "voicevox", name: "九州そら (Kyushu Sora - Normal)", style: "Normal", gender: "female" },
  { id: "23", voice_id: "23", provider: "voicevox", name: "九州そら (Kyushu Sora - あまあま)", style: "あまあま", gender: "female" },
  { id: "24", voice_id: "24", provider: "voicevox", name: "九州そら (Kyushu Sora - ツンツン)", style: "ツンツン", gender: "female" },
  { id: "25", voice_id: "25", provider: "voicevox", name: "もち子さん (Mochiko-san - Normal)", style: "Normal", gender: "female" },
  { id: "26", voice_id: "26", provider: "voicevox", name: "剣崎雌雄 (Kenzaki Mesuo - Normal)", style: "Normal", gender: "male" },
  { id: "27", voice_id: "27", provider: "voicevox", name: "WhiteCUL (WhiteCUL - Normal)", style: "Normal", gender: "female" },
  { id: "28", voice_id: "28", provider: "voicevox", name: "WhiteCUL (WhiteCUL - たのしい)", style: "たのしい", gender: "female" },
  { id: "29", voice_id: "29", provider: "voicevox", name: "WhiteCUL (WhiteCUL - かなしい)", style: "かなしい", gender: "female" },
  { id: "30", voice_id: "30", provider: "voicevox", name: "後鬼 (Goki - 人間ver.)", style: "人間ver.", gender: "female" },
  { id: "31", voice_id: "31", provider: "voicevox", name: "後鬼 (Goki - 鬼ver.)", style: "鬼ver.", gender: "female" },
  { id: "32", voice_id: "32", provider: "voicevox", name: "No.7 (Seven - Normal)", style: "Normal", gender: "female" },
  { id: "33", voice_id: "33", provider: "voicevox", name: "No.7 (Seven - アナウンス)", style: "アナウンス", gender: "female" },
  { id: "34", voice_id: "34", provider: "voicevox", name: "ちび式じい (Chibi Shikijii - Normal)", style: "Normal", gender: "male" },
  { id: "35", voice_id: "35", provider: "voicevox", name: "小夜/SORYU (Sayo - Normal)", style: "Normal", gender: "female" },
  { id: "36", voice_id: "36", provider: "voicevox", name: "ナースロボ＿タイプＴ (Nurse Robot Type T - Normal)", style: "Normal", gender: "female" },
  { id: "37", voice_id: "37", provider: "voicevox", name: "ナースロボ＿タイプＴ (Nurse Robot Type T - 楽々)", style: "楽々", gender: "female" },
  { id: "38", voice_id: "38", provider: "voicevox", name: "東北ずん子 (Tohoku Zunko - Normal)", style: "Normal", gender: "female" },
  { id: "39", voice_id: "39", provider: "voicevox", name: "東北きりたん (Tohoku Kiritan - Normal)", style: "Normal", gender: "female" },
  { id: "40", voice_id: "40", provider: "voicevox", name: "東北イタコ (Tohoku Itako - Normal)", style: "Normal", gender: "female" },
  { id: "41", voice_id: "41", provider: "voicevox", name: "中国うさぎ (Chugoku Usagi - Normal)", style: "Normal", gender: "female" },
  { id: "42", voice_id: "42", provider: "voicevox", name: "中国うさぎ (Chugoku Usagi - おどろき)", style: "おどろき", gender: "female" },
  { id: "43", voice_id: "43", provider: "voicevox", name: "栗田まろん (Kurita Maron - Normal)", style: "Normal", gender: "male" },
  { id: "44", voice_id: "44", provider: "voicevox", name: "あいえるたん (Aiel Tan - Normal)", style: "Normal", gender: "female" },
  { id: "45", voice_id: "45", provider: "voicevox", name: "満別花丸 (Manbetsu Hanamaru - Normal)", style: "Normal", gender: "female" },
  { id: "46", voice_id: "46", provider: "voicevox", name: "琴詠ニア (Kotoyomi Nia - Normal)", style: "Normal", gender: "female" },
];
