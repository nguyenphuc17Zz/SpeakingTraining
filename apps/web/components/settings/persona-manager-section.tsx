"use client";

import React, { useState } from "react";
import { usePersonas } from "@/hooks/use-personas";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import {
  Users,
  Plus,
  Sparkles,
  Trash2,
  Lock,
  Wand2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { PersonaCreateInput, Persona } from "@/types/persona";

export function PersonaManagerSection() {
  const {
    personas,
    loading,
    actionLoading,
    generating,
    createPersona,
    deletePersona,
    generateRandomPersona,
  } = usePersonas();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<PersonaCreateInput>({
    name: "",
    role: "",
    description: "",
    personality: "",
    speaking_style: "",
    difficulty: "N3",
    system_prompt: "",
  });
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Persona | null>(null);

  const resetForm = () =>
    setFormData({
      name: "",
      role: "",
      description: "",
      personality: "",
      speaking_style: "",
      difficulty: "N3",
      system_prompt: "",
    });

  const handleCreate = async () => {
    if (!formData.name.trim() || !formData.role.trim()) return;
    const ok = await createPersona(formData);
    if (ok) {
      setIsModalOpen(false);
      resetForm();
      setFeedback({ type: "success", msg: `Đã tạo persona “${formData.name}” thành công.` });
      setTimeout(() => setFeedback(null), 3000);
    } else {
      setFeedback({ type: "error", msg: "Không thể tạo persona. Kiểm tra lại thông tin." });
    }
  };

  const handleRandom = async () => {
    setFeedback(null);
    const { data, error: genError } = await generateRandomPersona({});
    if (data) {
      setFormData({
        name: data.name,
        role: data.role,
        description: data.description,
        personality: data.personality,
        speaking_style: data.speaking_style,
        difficulty: data.difficulty || "N3",
        system_prompt: data.system_prompt || "",
      });
      setIsModalOpen(true);
      setFeedback({
        type: "success",
        msg: `AI đã tạo nháp “${data.name}” — kiểm tra rồi bấm Lưu nhé${data.reasoning ? ` (${data.reasoning})` : ""}.`,
      });
    } else {
      setFeedback({
        type: "error",
        msg: genError || "Không thể tạo persona bằng AI. Vui lòng kiểm tra API Key trong Cài đặt.",
      });
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const ok = await deletePersona(deleteTarget.id);
    if (ok) {
      setFeedback({ type: "success", msg: `Đã xóa persona “${deleteTarget.name}”.` });
      setTimeout(() => setFeedback(null), 3000);
    } else {
      setFeedback({ type: "error", msg: "Không thể xóa. Persona hệ thống không được xóa." });
    }
    setDeleteTarget(null);
  };

  return (
    <div className="space-y-5">
      {/* Header washi */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card washi-texture shadow-washi p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="absolute -top-10 -right-10 h-32 w-32 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
        <div className="relative flex items-center gap-3">
          <span className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0">
            <Users className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-base font-bold text-foreground">
              Đối tác hội thoại <span className="font-jp text-xs font-normal text-muted-foreground">ペルソナ</span>
            </h2>
            <p className="text-sm text-muted-foreground">Chọn persona hệ thống hoặc tự tạo kịch bản riêng. Persona tự tạo có thể xóa.</p>
          </div>
        </div>
        <div className="relative flex items-center gap-2 shrink-0 flex-wrap">
          <Button variant="outline" size="sm" onClick={handleRandom} isLoading={generating} className="text-xs">
            <Wand2 className="h-4 w-4" />
            Tạo ngẫu nhiên bằng AI
          </Button>
          <Button variant="akane" size="sm" onClick={() => { resetForm(); setIsModalOpen(true); }} className="text-xs">
            <Plus className="h-4 w-4" />
            Tạo thủ công
          </Button>
        </div>
      </div>

      {feedback && (
        <div
          className={`p-3 rounded-xl border text-sm flex items-center gap-2 ${
            feedback.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300"
              : "bg-destructive/10 border-destructive/20 text-destructive"
          }`}
        >
          {feedback.type === "success" ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertCircle className="h-4 w-4 shrink-0" />}
          <span className="flex-1">{feedback.msg}</span>
          <button onClick={() => setFeedback(null)} className="font-bold px-2 hover:opacity-70">✕</button>
        </div>
      )}

      {loading ? (
        <div className="p-10 text-center text-sm text-muted-foreground flex items-center justify-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin" /> Đang tải personas…
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {personas.map((p) => (
            <Card key={p.id} variant="washi" className="p-4 flex flex-col justify-between hover:shadow-washi transition-shadow">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="flex items-center gap-3 min-w-0">
                    <span className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-aizome-600 flex items-center justify-center text-primary-foreground font-bold text-sm shadow-md shrink-0">
                      {p.name.charAt(0)}
                    </span>
                    <span className="min-w-0">
                      <span className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-bold text-foreground truncate">{p.name}</span>
                        {p.is_system && (
                          <Badge variant="fuji" size="sm" className="text-[10px]">
                            <Lock className="h-2.5 w-2.5" /> Hệ thống
                          </Badge>
                        )}
                      </span>
                      <span className="text-xs text-primary font-medium truncate block">{p.role}</span>
                    </span>
                  </span>
                  <Badge variant="jlpt" size="sm" className="shrink-0">
                    {p.difficulty}
                  </Badge>
                </div>

                <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">{p.description}</p>

                <div className="space-y-1 pt-1 text-xs">
                  <span className="flex items-start gap-1.5">
                    <span className="font-semibold text-foreground shrink-0">Phong cách:</span>
                    <span className="text-muted-foreground">{p.speaking_style}</span>
                  </span>
                  <span className="flex items-start gap-1.5">
                    <span className="font-semibold text-foreground shrink-0">Tính cách:</span>
                    <span className="text-muted-foreground line-clamp-2">{p.personality}</span>
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 mt-3 border-t border-border">
                <span className="text-xs text-muted-foreground font-mono truncate">ID: {p.id.slice(0, 8)}…</span>
                {!p.is_system ? (
                  <Button variant="ghost" size="sm" className="h-8 text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={() => setDeleteTarget(p)}>
                    <Trash2 className="h-3.5 w-3.5" />
                    Xóa
                  </Button>
                ) : (
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Lock className="h-3 w-3" /> Không thể xóa
                  </span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Tạo persona mới"
        description="Điền thông tin hoặc dùng nút Tạo ngẫu nhiên AI để điền tự động, rồi kiểm tra trước khi lưu."
      >
        <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-primary/5 border border-primary/10">
            <span className="text-xs text-muted-foreground flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-primary" /> Mẹo: bấm Tạo ngẫu nhiên AI để AI tự nghĩ giúp bạn
            </span>
            <Button variant="ghost" size="sm" onClick={handleRandom} isLoading={generating} className="h-7 text-xs">
              <Wand2 className="h-3.5 w-3.5" /> Tạo ngẫu nhiên
            </Button>
          </div>

          <Input label="Tên persona" placeholder="VD: Haru — Chủ quán café" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          <Input label="Vai trò" placeholder="VD: Chủ quán café ở Harajuku" value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })} />
          <span className="grid grid-cols-2 gap-3">
            <label className="space-y-1.5">
              <span className="text-xs font-semibold text-foreground">Độ khó</span>
              <select
                value={formData.difficulty}
                onChange={(e) => setFormData({ ...formData, difficulty: e.target.value })}
                className="w-full h-9 bg-background border border-border rounded-lg px-3 text-sm text-foreground focus:outline-none focus:border-ring"
              >
                {["N5", "N4", "N3", "N2", "N1"].map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="Phong cách nói"
              placeholder="VD: Lịch sự pha casual"
              value={formData.speaking_style}
              onChange={(e) => setFormData({ ...formData, speaking_style: e.target.value })}
            />
          </span>
          <label className="space-y-1.5 block">
            <span className="text-xs font-semibold text-foreground">Mô tả & Tính cách</span>
            <textarea
              rows={2}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-ring resize-none"
              placeholder="VD: Nhiệt tình, nói nhiều về café, hay đùa nhẹ"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value, personality: e.target.value })}
            />
          </label>
          <label className="space-y-1.5 block">
            <span className="text-xs font-semibold text-foreground">System Prompt (tùy chọn)</span>
            <textarea
              rows={3}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-ring resize-none"
              placeholder="You are Haru, a café owner in Harajuku… Keep replies 1-3 sentences."
              value={formData.system_prompt || ""}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
            />
          </label>

          <span className="flex justify-end gap-2 pt-3 border-t border-border sticky bottom-0 bg-card">
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)} disabled={actionLoading}>
              Hủy
            </Button>
            <Button variant="akane" size="sm" onClick={handleCreate} isLoading={actionLoading} disabled={!formData.name.trim() || !formData.role.trim()}>
              <Plus className="h-4 w-4" /> Lưu persona
            </Button>
          </span>
        </div>
      </Modal>

      {/* Delete confirm modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Xóa persona?"
        description={`Bạn có chắc muốn xóa “${deleteTarget?.name || ""}”? Hành động này không thể hoàn tác.`}
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-sm text-destructive flex items-start gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              Persona tự tạo sẽ bị xóa vĩnh viễn. Persona hệ thống không thể xóa.
            </span>
          </div>
          <span className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={() => setDeleteTarget(null)} disabled={actionLoading}>
              Hủy
            </Button>
            <Button variant="danger" size="sm" onClick={confirmDelete} isLoading={actionLoading}>
              <Trash2 className="h-4 w-4" /> Xóa
            </Button>
          </span>
        </div>
      </Modal>
    </div>
  );
}
