"use client";

import { useState, useEffect, useMemo, useRef, useCallback } from "react";

export function useReflexFilters() {
  const [selectedForms, setSelectedForms] = useState<string[]>([]);
  const [showFormFilterModal, setShowFormFilterModal] = useState(false);

  const [selectedQnaTopics, setSelectedQnaTopics] = useState<string[]>([]);
  const [showQnaTopicFilterModal, setShowQnaTopicFilterModal] = useState(false);
  const [customKeywords, setCustomKeywords] = useState<string>("");

  const [selectedTransformCategories, setSelectedTransformCategories] = useState<string[]>([]);
  const [showTransformFilterModal, setShowTransformFilterModal] = useState(false);
  const [customTransformKeywords, setCustomTransformKeywords] = useState<string>("");

  const [selectedContextCategories, setSelectedContextCategories] = useState<string[]>([]);
  const [showContextFilterModal, setShowContextFilterModal] = useState(false);
  const [customContextKeywords, setCustomContextKeywords] = useState<string>("");

  const [selectedVocabCategories, setSelectedVocabCategories] = useState<string[]>([]);
  const [showVocabFilterModal, setShowVocabFilterModal] = useState(false);
  const [customVocabKeywords, setCustomVocabKeywords] = useState<string>("");

  const [selectedKeigoCategories, setSelectedKeigoCategories] = useState<string[]>([]);
  const [showKeigoFilterModal, setShowKeigoFilterModal] = useState(false);
  const [customKeigoKeywords, setCustomKeigoKeywords] = useState<string>("");

  const isLoadedRef = useRef(false);

  // Load saved preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedForms = localStorage.getItem("speaking_training_reflex_selected_forms");
      if (savedForms) {
        const parsed = JSON.parse(savedForms);
        if (Array.isArray(parsed)) setSelectedForms(parsed);
      }

      const savedQna = localStorage.getItem("speaking_training_reflex_selected_qna_topics");
      if (savedQna) {
        const parsed = JSON.parse(savedQna);
        if (Array.isArray(parsed)) setSelectedQnaTopics(parsed);
      }

      const savedKeywords = localStorage.getItem("speaking_training_reflex_qna_custom_keywords");
      if (savedKeywords) setCustomKeywords(savedKeywords);

      const savedTransform = localStorage.getItem("speaking_training_reflex_selected_transform_categories");
      if (savedTransform) {
        const parsed = JSON.parse(savedTransform);
        if (Array.isArray(parsed)) setSelectedTransformCategories(parsed);
      }

      const savedTransformKeywords = localStorage.getItem("speaking_training_reflex_transform_custom_keywords");
      if (savedTransformKeywords) setCustomTransformKeywords(savedTransformKeywords);

      const savedContext = localStorage.getItem("speaking_training_reflex_selected_context_categories");
      if (savedContext) {
        const parsed = JSON.parse(savedContext);
        if (Array.isArray(parsed)) setSelectedContextCategories(parsed);
      }

      const savedContextKeywords = localStorage.getItem("speaking_training_reflex_context_custom_keywords");
      if (savedContextKeywords) setCustomContextKeywords(savedContextKeywords);

      const savedVocab = localStorage.getItem("speaking_training_reflex_selected_vocab_categories");
      if (savedVocab) {
        const parsed = JSON.parse(savedVocab);
        if (Array.isArray(parsed)) setSelectedVocabCategories(parsed);
      }

      const savedVocabKeywords = localStorage.getItem("speaking_training_reflex_vocab_custom_keywords");
      if (savedVocabKeywords) setCustomVocabKeywords(savedVocabKeywords);

      const savedKeigo = localStorage.getItem("speaking_training_reflex_selected_keigo_categories");
      if (savedKeigo) {
        const parsed = JSON.parse(savedKeigo);
        if (Array.isArray(parsed)) setSelectedKeigoCategories(parsed);
      }

      const savedKeigoKeywords = localStorage.getItem("speaking_training_reflex_keigo_custom_keywords");
      if (savedKeigoKeywords) setCustomKeigoKeywords(savedKeigoKeywords);
    } catch (e) {
      console.warn("[useReflexFilters] Failed to load filters from localStorage:", e);
    } finally {
      isLoadedRef.current = true;
    }
  }, []);

  const handleSelectedFormsChange = useCallback((forms: string[]) => {
    setSelectedForms(forms);
    try {
      localStorage.setItem("speaking_training_reflex_selected_forms", JSON.stringify(forms));
    } catch {}
  }, []);

  const handleSelectedQnaTopicsChange = useCallback((topics: string[]) => {
    setSelectedQnaTopics(topics);
    try {
      localStorage.setItem("speaking_training_reflex_selected_qna_topics", JSON.stringify(topics));
    } catch {}
  }, []);

  const handleCustomKeywordsChange = useCallback((val: string) => {
    setCustomKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_qna_custom_keywords", val);
    } catch {}
  }, []);

  const handleSelectedTransformCategoriesChange = useCallback((cats: string[]) => {
    setSelectedTransformCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_transform_categories", JSON.stringify(cats));
    } catch {}
  }, []);

  const handleCustomTransformKeywordsChange = useCallback((val: string) => {
    setCustomTransformKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_transform_custom_keywords", val);
    } catch {}
  }, []);

  const handleSelectedContextCategoriesChange = useCallback((cats: string[]) => {
    setSelectedContextCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_context_categories", JSON.stringify(cats));
    } catch {}
  }, []);

  const handleCustomContextKeywordsChange = useCallback((val: string) => {
    setCustomContextKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_context_custom_keywords", val);
    } catch {}
  }, []);

  const handleSelectedVocabCategoriesChange = useCallback((cats: string[]) => {
    setSelectedVocabCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_vocab_categories", JSON.stringify(cats));
    } catch {}
  }, []);

  const handleCustomVocabKeywordsChange = useCallback((val: string) => {
    setCustomVocabKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_vocab_custom_keywords", val);
    } catch {}
  }, []);

  const handleSelectedKeigoCategoriesChange = useCallback((cats: string[]) => {
    setSelectedKeigoCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_keigo_categories", JSON.stringify(cats));
    } catch {}
  }, []);

  const handleCustomKeigoKeywordsChange = useCallback((val: string) => {
    setCustomKeigoKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_keigo_custom_keywords", val);
    } catch {}
  }, []);

  const conjugationTarget = useMemo(() => {
    if (selectedForms.length === 0) return undefined;
    return selectedForms.join(",");
  }, [selectedForms]);

  const qnaTopic = useMemo(() => {
    if (customKeywords && customKeywords.trim()) {
      return customKeywords.trim();
    }
    if (selectedQnaTopics.length === 0) return undefined;
    return selectedQnaTopics.join(",");
  }, [customKeywords, selectedQnaTopics]);

  const transformationCategory = useMemo(() => {
    if (customTransformKeywords && customTransformKeywords.trim()) {
      return customTransformKeywords.trim();
    }
    if (selectedTransformCategories.length === 0) return undefined;
    return selectedTransformCategories.join(",");
  }, [customTransformKeywords, selectedTransformCategories]);

  const contextCategory = useMemo(() => {
    if (customContextKeywords && customContextKeywords.trim()) {
      return customContextKeywords.trim();
    }
    if (selectedContextCategories.length === 0) return undefined;
    return selectedContextCategories.join(",");
  }, [customContextKeywords, selectedContextCategories]);

  const vocabCategory = useMemo(() => {
    if (customVocabKeywords && customVocabKeywords.trim()) {
      return customVocabKeywords.trim();
    }
    if (selectedVocabCategories.length === 0) return undefined;
    return selectedVocabCategories.join(",");
  }, [customVocabKeywords, selectedVocabCategories]);

  const keigoCategory = useMemo(() => {
    if (customKeigoKeywords && customKeigoKeywords.trim()) {
      return customKeigoKeywords.trim();
    }
    if (selectedKeigoCategories.length === 0) return undefined;
    return selectedKeigoCategories.join(",");
  }, [customKeigoKeywords, selectedKeigoCategories]);

  return {
    // Conjugation
    selectedForms,
    setSelectedForms: handleSelectedFormsChange,
    showFormFilterModal,
    setShowFormFilterModal,
    conjugationTarget,

    // QnA
    selectedQnaTopics,
    setSelectedQnaTopics: handleSelectedQnaTopicsChange,
    customKeywords,
    setCustomKeywords: handleCustomKeywordsChange,
    showQnaTopicFilterModal,
    setShowQnaTopicFilterModal,
    qnaTopic,

    // Transformation
    selectedTransformCategories,
    setSelectedTransformCategories: handleSelectedTransformCategoriesChange,
    customTransformKeywords,
    setCustomTransformKeywords: handleCustomTransformKeywordsChange,
    showTransformFilterModal,
    setShowTransformFilterModal,
    transformationCategory,

    // Context
    selectedContextCategories,
    setSelectedContextCategories: handleSelectedContextCategoriesChange,
    customContextKeywords,
    setCustomContextKeywords: handleCustomContextKeywordsChange,
    showContextFilterModal,
    setShowContextFilterModal,
    contextCategory,

    // Vocab
    selectedVocabCategories,
    setSelectedVocabCategories: handleSelectedVocabCategoriesChange,
    customVocabKeywords,
    setCustomVocabKeywords: handleCustomVocabKeywordsChange,
    showVocabFilterModal,
    setShowVocabFilterModal,
    vocabCategory,

    // Keigo
    selectedKeigoCategories,
    setSelectedKeigoCategories: handleSelectedKeigoCategoriesChange,
    customKeigoKeywords,
    setCustomKeigoKeywords: handleCustomKeigoKeywordsChange,
    showKeigoFilterModal,
    setShowKeigoFilterModal,
    keigoCategory,
  };
}
