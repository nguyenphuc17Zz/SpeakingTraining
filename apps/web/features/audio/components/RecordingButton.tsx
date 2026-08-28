"use client";

import React from "react";
import { Mic, Square, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RecordingState } from "@/types/audio";

interface RecordingButtonProps {
  state: RecordingState;
  onStart: () => void;
  onStop: () => void;
  onRequestPermission?: () => void;
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
  disabled?: boolean;
}

export function RecordingButton({
  state,
  onStart,
  onStop,
  onRequestPermission,
  size = "lg",
  className = "",
  label,
  disabled = false,
}: RecordingButtonProps) {
  const isRecording = state === "recording";
  const isStopping = state === "stopping";
  const isProcessing = state === "processing";
  const isDenied = state === "permission_denied";
  const isRequesting = state === "requesting_permission";

  const handleClick = () => {
    if (isRecording) {
      onStop();
    } else if (isDenied && onRequestPermission) {
      onRequestPermission();
    } else {
      onStart();
    }
  };

  const getButtonText = () => {
    if (label) return label;
    if (isRecording) return "Dừng ghi âm (完了)";
    if (isStopping) return "Đang dừng...";
    if (isProcessing) return "Đang xử lý...";
    if (isRequesting) return "Đang xin quyền micro...";
    if (isDenied) return "Cấp quyền Micro";
    return "Bắt đầu nói (録音)";
  };

  return (
    <Button
      variant={isRecording ? "danger" : isDenied ? "outline" : "primary"}
      size={size}
      onClick={handleClick}
      disabled={disabled || isStopping || isProcessing || isRequesting}
      className={`relative transition-all duration-200 ${
        isRecording
          ? "animate-pulse shadow-lg shadow-destructive/30 bg-destructive hover:bg-destructive/90 text-destructive-foreground"
          : "shadow-md shadow-primary/20"
      } ${className}`}
    >
      {isStopping || isProcessing || isRequesting ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : isRecording ? (
        <Square className="h-4 w-4 mr-2 fill-current" />
      ) : isDenied ? (
        <AlertCircle className="h-4 w-4 mr-2 text-destructive" />
      ) : (
        <Mic className="h-4 w-4 mr-2" />
      )}
      <span>{getButtonText()}</span>
    </Button>
  );
}
