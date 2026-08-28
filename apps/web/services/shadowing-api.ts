import { apiClient } from "@/services/api-client";
import {
  Bookmark,
  PracticeAttemptFeedback,
  SegmentTranslation,
  ShadowingCandidate,
  ShadowingJobStatus,
  ShadowingLesson,
  ShadowingVideo,
  ShadowingVideoDetail,
  VideoImportResult,
} from "@/types/shadowing";

export const shadowingApi = {
  /**
   * Imports a YouTube video for transcription, segmentation, and shadowing analysis.
   */
  async importVideo(url: string, customWhisperModel?: string): Promise<VideoImportResult> {
    return apiClient.post<VideoImportResult>(
      "/shadowing/videos/import",
      {
        url,
        custom_whisper_model: customWhisperModel || null,
      },
      { timeoutMs: 180000 }
    );
  },

  /**
   * Lists recently imported YouTube videos.
   */
  async listVideos(limit = 20, offset = 0): Promise<{ videos: ShadowingVideo[]; total: number }> {
    return apiClient.get<{ videos: ShadowingVideo[]; total: number }>(
      `/shadowing/videos?limit=${limit}&offset=${offset}`
    );
  },

  /**
   * Fetches full video detail, segmented transcript, and personalized candidate recommendations.
   */
  async getVideo(videoId: string): Promise<ShadowingVideoDetail> {
    return apiClient.get<ShadowingVideoDetail>(`/shadowing/videos/${videoId}`);
  },

  /**
   * Deletes a shadowing video along with its transcripts, segments, and progress records.
   */
  async deleteVideo(videoId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete<{ success: boolean; message: string }>(`/shadowing/videos/${videoId}`);
  },

  /**
   * Retrieves top recommended clips for a specific video based on learner profile.
   */
  async getRecommendations(videoId: string): Promise<ShadowingCandidate[]> {
    return apiClient.get<ShadowingCandidate[]>(`/shadowing/videos/${videoId}/recommendations`);
  },

  /**
   * Generates a time-bounded shadowing lesson from a video.
   */
  async createLesson(
    videoId: string,
    timeBudgetMinutes = 15,
    mode = "quick_shadow"
  ): Promise<ShadowingLesson> {
    return apiClient.post<ShadowingLesson>(`/shadowing/videos/${videoId}/lesson`, {
      time_budget_minutes: timeBudgetMinutes,
      mode,
    });
  },

  /**
   * Starts a shadowing attempt for a segment, creating a formal Exercise in the Learning Engine.
   */
  async startPractice(
    segmentId: string,
    shadowingMode = "shadow"
  ): Promise<{
    exercise_id: string;
    attempt_id: string;
    segment_id: string;
    video_id: string;
    reference_text: string;
    expected_reading?: string;
    start_time: number;
    end_time: number;
    speaker_id: string;
  }> {
    return apiClient.post(`/shadowing/segments/${segmentId}/practice/start`, {
      shadowing_mode: shadowingMode,
    });
  },

  /**
   * Submits user speech recording for Phase 6 Pronunciation analysis and Phase 7 Mastery updates.
   */
  async completePractice(
    segmentId: string,
    exerciseId: string,
    attemptId: string,
    audioBase64: string,
    shadowingMode = "shadow",
    playbackSpeed = 1.0,
    clientTranscript?: string
  ): Promise<PracticeAttemptFeedback> {
    return apiClient.post<PracticeAttemptFeedback>(
      `/shadowing/segments/${segmentId}/practice/complete`,
      {
        exercise_id: exerciseId,
        attempt_id: attemptId,
        audio_base64: audioBase64,
        shadowing_mode: shadowingMode,
        playback_speed: playbackSpeed,
        client_transcript: clientTranscript,
      },
      { timeoutMs: 120000 }
    );
  },

  /**
   * Bookmarks a segment with an optional personal study note.
   */
  async bookmarkSegment(segmentId: string, note?: string): Promise<Bookmark> {
    return apiClient.post<Bookmark>(`/shadowing/segments/${segmentId}/bookmark`, {
      note,
    });
  },

  /**
   * Deletes a segment bookmark.
   */
  async removeBookmark(segmentId: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(`/shadowing/segments/${segmentId}/bookmark`);
  },

  /**
   * Nuanced AI translation of spoken sentence into Vietnamese/English with tone explanations.
   */
  async translateSegment(
    segmentId: string,
    targetLanguage = "vi"
  ): Promise<SegmentTranslation> {
    return apiClient.post<SegmentTranslation>(`/shadowing/segments/${segmentId}/translate`, {
      target_language: targetLanguage,
    });
  },

  /**
   * Checks real-time multi-stage status of an active YouTube import job.
   */
  async getJobStatus(jobId: string): Promise<ShadowingJobStatus> {
    return apiClient.get<ShadowingJobStatus>(`/shadowing/jobs/${jobId}`);
  },
};
