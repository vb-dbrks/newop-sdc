import { useState } from "react";
import {
  ArrowRight,
  ChevronDown,
  FileText,
  Paperclip,
  Sparkles,
  X,
} from "lucide-react";
import AttachDocumentsModal, {
  type AttachedDocument,
} from "@/components/upload/AttachDocumentsModal";

const TYPES = [
  { value: "new_opportunity", label: "New Opportunity" },
  { value: "sdc", label: "Study Design Concept" },
  { value: "protocol", label: "Protocol" },
] as const;

type DocType = (typeof TYPES)[number]["value"];

function truncateFilename(name: string, maxLen = 18): string {
  if (name.length <= maxLen) return name;
  const dot = name.lastIndexOf(".");
  if (dot < 0 || dot >= name.length - 1) return `${name.slice(0, maxLen - 1)}…`;
  const ext = name.slice(dot);
  const head = name.slice(0, Math.max(1, maxLen - ext.length - 1));
  return `${head}…${ext}`;
}

export default function AuthoringComposer() {
  const [prompt, setPrompt] = useState("");
  const [docType, setDocType] = useState<DocType | "">("");
  const [typeOpen, setTypeOpen] = useState(false);
  const [attachOpen, setAttachOpen] = useState(false);
  const [attached, setAttached] = useState<AttachedDocument[]>([]);
  const canGenerate = prompt.trim().length > 0 && docType !== "";

  const selectedLabel = TYPES.find((t) => t.value === docType)?.label ?? "Select type";

  const onAttached = (docs: AttachedDocument[]) => {
    setAttached((prev) => {
      const existing = new Set(prev.map((d) => d.source_document_id));
      return [...prev, ...docs.filter((d) => !existing.has(d.source_document_id))];
    });
  };

  const removeAttached = (id: string) => {
    setAttached((prev) => prev.filter((d) => d.source_document_id !== id));
  };

  return (
    <>
      <div className="mx-auto w-full max-w-3xl rounded-2xl border border-line bg-white shadow-[0_12px_40px_-20px_rgba(15,23,42,0.18)] p-4">
        {/* Attached document chips — above the textarea */}
        {attached.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {attached.map((d) => (
              <span
                key={d.source_document_id}
                className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 border border-line pl-2 pr-1 py-1 text-xs text-ink/80"
                title={`${d.file_name} · ${d.document_type_label}`}
              >
                <FileText size={12} className="text-blue-500 shrink-0" />
                <span className="font-medium">{truncateFilename(d.file_name)}</span>
                <button
                  type="button"
                  aria-label={`Remove ${d.file_name}`}
                  onClick={() => removeAttached(d.source_document_id)}
                  className="h-5 w-5 grid place-items-center rounded-full hover:bg-slate-200 text-ink/50 hover:text-ink/80"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}

        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          placeholder="Describe the opportunity to assess — e.g., 'Compare competitor trials in EoE and highlight differentiation opportunities…'"
          className="w-full resize-none border-0 bg-transparent text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-0"
        />
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            <div className="relative">
              <button
                type="button"
                onClick={() => setTypeOpen((v) => !v)}
                className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1.5 text-xs text-ink/80 hover:bg-slate-50"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-velocia/70" />
                {selectedLabel}
                <ChevronDown size={14} className="text-ink/50" />
              </button>
              {typeOpen && (
                <div className="absolute z-10 mt-2 w-56 rounded-lg border border-line bg-white shadow-lg py-1">
                  {TYPES.map((t) => (
                    <button
                      key={t.value}
                      type="button"
                      className="w-full text-left px-3 py-1.5 text-sm hover:bg-slate-50"
                      onClick={() => {
                        setDocType(t.value);
                        setTypeOpen(false);
                      }}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              type="button"
              aria-label="Attach"
              onClick={() => setAttachOpen(true)}
              className={
                "h-8 w-8 grid place-items-center rounded-full transition " +
                (attached.length > 0
                  ? "bg-velocia/10 text-velocia hover:bg-velocia/15"
                  : "text-ink/60 hover:bg-slate-100")
              }
            >
              <Paperclip size={16} />
            </button>
            <button
              type="button"
              aria-label="Enhance"
              className="h-8 w-8 grid place-items-center rounded-full hover:bg-slate-100 text-ink/60"
            >
              <Sparkles size={16} />
            </button>
          </div>
          <button
            type="button"
            disabled={!canGenerate}
            className="inline-flex items-center gap-1.5 rounded-full bg-velocia px-4 py-2 text-sm font-semibold text-white transition hover:bg-velocia-hover disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Generate
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      <AttachDocumentsModal
        open={attachOpen}
        onClose={() => setAttachOpen(false)}
        onAttached={onAttached}
      />
    </>
  );
}
