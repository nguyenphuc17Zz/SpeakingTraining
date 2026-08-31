export interface ExampleSentence {
  ja: string;
  vi: string;
  situation?: string;
}

export interface AlternativeItem {
  expression: string;
  reading: string;
  meaning_vi: string;
  difference_explanation: string;
}

export interface BestMatch {
  expression: string;
  reading: string;
  meaning_vi: string;
  part_of_speech: string;
  jlpt_level: string;
  register: string;
  naturalness_score: number;
  nuance_explanation: string;
  usage_collocation: string;
  examples: ExampleSentence[];
}

export interface VocabularyLookupRequest {
  query: string;
  context?: string;
  target_level?: string;
  register_preference?: string;
}

export interface VocabularyLookupResponse {
  best_match: BestMatch;
  alternatives: AlternativeItem[];
  original_query: string;
  context?: string;
  searched_at?: string;
}

export interface SaveVocabularyNotebookRequest {
  expression: string;
  reading?: string;
  meaning_vi: string;
  nuance_explanation?: string;
  context?: string;
  jlpt_level?: string;
  part_of_speech?: string;
  register?: string;
  tags?: string[];
}

export interface SaveVocabularyNotebookResponse {
  success: boolean;
  item_id: string;
  message: string;
  created_at?: string;
}

export interface BubbleSelectionState {
  text: string;
  context: string;
  rect: {
    top: number;
    bottom: number;
    left: number;
    right: number;
    width: number;
    height: number;
  };
  inputElement?: HTMLInputElement | HTMLTextAreaElement | null;
  selectionStart?: number;
  selectionEnd?: number;
}
