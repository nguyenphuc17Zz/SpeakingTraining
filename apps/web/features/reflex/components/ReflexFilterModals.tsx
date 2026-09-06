"use client";

import React from "react";
import { ConjugationFilterModal } from "./ConjugationFilterModal";
import { QnaTopicFilterModal } from "./QnaTopicFilterModal";
import { TransformationFilterModal } from "./TransformationFilterModal";
import { ContextFilterModal } from "./ContextFilterModal";
import { VocabFilterModal } from "./VocabFilterModal";
import { KeigoFilterModal } from "./KeigoFilterModal";
import { useReflexFilters } from "../hooks/useReflexFilters";

export interface ReflexFilterModalsProps {
  filters: ReturnType<typeof useReflexFilters>;
}

export const ReflexFilterModals = React.memo(function ReflexFilterModals({
  filters,
}: ReflexFilterModalsProps) {
  return (
    <>
      {/* 1. Conjugation Form Filter Modal */}
      <ConjugationFilterModal
        open={filters.showFormFilterModal}
        onClose={() => filters.setShowFormFilterModal(false)}
        selectedForms={filters.selectedForms}
        onChangeSelectedForms={filters.setSelectedForms}
      />

      {/* 2. Q&A Topic Filter Modal */}
      <QnaTopicFilterModal
        open={filters.showQnaTopicFilterModal}
        onClose={() => filters.setShowQnaTopicFilterModal(false)}
        selectedTopics={filters.selectedQnaTopics}
        onChangeSelectedTopics={filters.setSelectedQnaTopics}
        customKeywords={filters.customKeywords}
        onChangeCustomKeywords={filters.setCustomKeywords}
      />

      {/* 3. Transformation Category Filter Modal */}
      <TransformationFilterModal
        isOpen={filters.showTransformFilterModal}
        onClose={() => filters.setShowTransformFilterModal(false)}
        selectedCategories={filters.selectedTransformCategories}
        onChange={filters.setSelectedTransformCategories}
        customKeywords={filters.customTransformKeywords}
        onChangeCustomKeywords={filters.setCustomTransformKeywords}
      />

      {/* 4. Context Category Filter Modal */}
      <ContextFilterModal
        isOpen={filters.showContextFilterModal}
        onClose={() => filters.setShowContextFilterModal(false)}
        selectedCategories={filters.selectedContextCategories}
        onChange={filters.setSelectedContextCategories}
        customKeywords={filters.customContextKeywords}
        onChangeCustomKeywords={filters.setCustomContextKeywords}
      />

      {/* 5. Vocab Category Filter Modal */}
      <VocabFilterModal
        isOpen={filters.showVocabFilterModal}
        onClose={() => filters.setShowVocabFilterModal(false)}
        selectedCategories={filters.selectedVocabCategories}
        onChange={filters.setSelectedVocabCategories}
        customKeywords={filters.customVocabKeywords}
        onChangeCustomKeywords={filters.setCustomVocabKeywords}
      />

      {/* 6. Keigo Filter Modal */}
      <KeigoFilterModal
        isOpen={filters.showKeigoFilterModal}
        onClose={() => filters.setShowKeigoFilterModal(false)}
        selectedCategories={filters.selectedKeigoCategories}
        onChange={filters.setSelectedKeigoCategories}
        customKeywords={filters.customKeigoKeywords}
        onChangeCustomKeywords={filters.setCustomKeigoKeywords}
      />
    </>
  );
});
