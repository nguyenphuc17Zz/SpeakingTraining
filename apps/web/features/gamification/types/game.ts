export interface LevelProgressInfo {
  level: number;
  total_xp: number;
  current_level_xp: number;
  next_level_xp: number;
  progress_ratio: number;
  is_max_level: boolean;
}

export interface GameProfileDTO {
  user_id: string;
  total_xp: number;
  level: number;
  rank: string;
  current_streak: number;
  longest_streak: number;
  skill_points: number;
  streak_freezes_available: number;
  current_title?: string | null;
  level_progress: LevelProgressInfo;
  today_xp: number;
  today_completed_quests: number;
  total_unlocked_achievements: number;
  last_active_date?: string | null;
}

export interface XPTransactionDTO {
  id: string;
  amount: number;
  category: string;
  reason: string;
  source_type: string;
  source_id: string;
  created_at: string;
  reward_policy_version: string;
}

export interface XPOverviewDTO {
  total_xp: number;
  level: number;
  today_xp: number;
  week_xp: number;
  category_breakdown: Record<string, number>;
  recent_transactions: XPTransactionDTO[];
}

export interface QuestDTO {
  id: string;
  quest_key: string;
  title: string;
  description: string;
  frequency: "daily" | "weekly" | "milestone" | "challenge";
  target_count: number;
  current_count: number;
  progress_ratio: number;
  xp_reward: number;
  status: "active" | "completed" | "claimed" | "expired";
  is_completed: boolean;
  expires_at?: string | null;
  category: string;
}

export interface AchievementDTO {
  id: string;
  key: string;
  title: string;
  description: string;
  rarity: "common" | "rare" | "epic" | "legendary";
  category: string;
  icon: string;
  xp_reward: number;
  is_unlocked: boolean;
  unlocked_at?: string | null;
  current_value: number;
  target_value: number;
  progress_ratio: number;
  is_hidden: boolean;
}

export interface SkillNodeDTO {
  key: string;
  name: string;
  description: string;
  category: "fluency" | "naturalness" | "grammar" | "pronunciation";
  icon: string;
  status: "locked" | "available" | "developing" | "strong" | "mastered";
  current_mastery: number;
  attempt_count: number;
  prerequisites: string[];
  linked_learning_items: Array<{
    key: string;
    title: string;
    mastery: number;
    lifecycle: string;
  }>;
  recommended_exercise_type?: string | null;
}

export interface SkillTreeOverviewDTO {
  categories: string[];
  nodes: SkillNodeDTO[];
  overall_mastery_average: number;
  mastered_count: number;
  total_nodes: number;
}

export interface UnlockableDTO {
  id: string;
  key: string;
  unlock_type: "persona" | "voice_profile" | "scenario" | "title" | "avatar_cosmetic" | "theme";
  title: string;
  description: string;
  level_required: number;
  is_unlocked: boolean;
  unlocked_at?: string | null;
  is_equipped: boolean;
  asset_reference?: string | null;
}

export interface BossDTO {
  id: string;
  key: string;
  name: string;
  subtitle: string;
  description: string;
  difficulty: "easy" | "normal" | "hard" | "extreme";
  required_level: number;
  is_unlocked: boolean;
  pass_score_threshold: number;
  xp_reward: number;
  title_reward?: string | null;
  objectives: string[];
  personal_best_score?: number | null;
  cleared: boolean;
  total_attempts: number;
}

export interface BossStartResponseDTO {
  boss_id: string;
  boss_name: string;
  exercise_id: string;
  session_id?: string | null;
  persona_key: string;
  instructions: string;
  objectives: string[];
}

export interface BossAttemptResultDTO {
  attempt_id: string;
  boss_id: string;
  score: number;
  passed: boolean;
  xp_awarded: number;
  title_awarded?: string | null;
  metrics: Record<string, any>;
  feedback?: string | null;
  weak_points: string[];
  recommended_training?: string | null;
}

export interface RewardNotificationDTO {
  id: string;
  notification_type: string;
  priority: "low" | "normal" | "high";
  title: string;
  message: string;
  xp_amount?: number | null;
  payload: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export interface StreakOverviewDTO {
  current_streak: number;
  longest_streak: number;
  streak_freezes_available: number;
  is_qualified_today: boolean;
  today_activities_count: number;
  qualifying_threshold_met: boolean;
  last_active_date?: string | null;
  activity_history_last_7_days: Array<{
    date: string;
    day_name: string;
    is_active: boolean;
    activity_count: number;
  }>;
}

export interface GameSettingsDTO {
  gamification_enabled: boolean;
  sound_enabled: boolean;
  animations_enabled: boolean;
  quest_intensity: string;
  difficulty_preference: string;
  show_xp_popups: boolean;
}
