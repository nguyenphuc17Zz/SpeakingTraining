"use client";

import React from "react";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { MicOff, AlertCircle, RefreshCw } from "lucide-react";

interface MicrophonePermissionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRetry: () => void;
}

export function MicrophonePermissionModal({
  isOpen,
  onClose,
  onRetry,
}: MicrophonePermissionModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Microphone Access Required (マイクの許可が必要です)"
      description="Real-time Japanese speaking practice requires access to your microphone."
    >
      <div className="space-y-4 pt-2">
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/30 flex items-start gap-3">
          <MicOff className="h-6 w-6 text-destructive shrink-0 mt-0.5" />
          <div className="space-y-1 text-xs">
            <p className="font-bold text-destructive">
              Browser Microphone Permission Denied
            </p>
            <p className="text-foreground leading-relaxed">
              Your browser blocked microphone access. To enable speech conversation:
            </p>
            <ul className="list-disc pl-4 space-y-1 text-muted-foreground mt-2">
              <li>Click the camera/lock icon in your browser address bar.</li>
              <li>Change Microphone permission to <strong>Allow</strong>.</li>
              <li>Click the <strong>Try Again</strong> button below.</li>
            </ul>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-3 border-t border-border">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={onRetry}>
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Try Again (再試行)
          </Button>
        </div>
      </div>
    </Modal>
  );
}
