import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  FileText,
  Sparkles,
  Upload,
  X,
} from "lucide-react";

export interface AttachedDocument {
  source_document_id: string;
  file_name: string;
  file_size_bytes: number;
  document_type: string;
  document_type_label: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onAttached: (docs: AttachedDocument[]) => void;
}

const ACCEPT = ".pdf,.doc,.docx";
const ACCEPT_MIMES = new Set([
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const MAX_BYTES = 10 * 1024 * 1024; // 10 MB

const DOCUMENT_TYPES = [
  { value: "medical_evidence_plan", label: "Medical Evidence Plan" },
  { value: "global_strategic_plan", label: "Global Strategic Plan" },
  { value: "strategic_plan", label: "Strategic Plan" },
  { value: "indication_strategy", label: "Indication Strategy" },
  { value: "evidence_map", label: "Evidence Map" },
  { value: "strategic_pillar", label: "Strategic Pillar" },
  { value: "portfolio_review", label: "Portfolio Review" },
  { value: "competitive_landscape", label: "Competitive Landscape" },
  { value: "study_report", label: "Study Report" },
  { value: "target_product_profile", label: "Target Product Profile" },
  { value: "integrated_evidence_plan", label: "Integrated Evidence Plan" },
  { value: "protocol_template", label: "Protocol Template" },
  { value: "other", label: "Other" },
];

const HIGHLY_RECOMMENDED = [
  { name: "GSP (Global Strategic Plan)", note: "Aligns study design with commercial objectives." },
  { name: "MEP (Medical Evidence Plan)", note: "Ensures endpoints support required value claims." },
  { name: "IEP (Integrated Evidence Plan)", note: "Harmonizes RWE needs with clinical data generation." },
  { name: "Medical Information (MI) Materials", note: "Identifies common clinician questions to address." },
  { name: "Clinical Guidelines", note: "Ensures alignment with standard of care." },
];

const SUPPORTING_CONTEXT = [
  { name: "Previous Study Protocols", note: "Leverages historical precedents for eligibility criteria." },
  { name: "Clinical Study Reports (CSR)", note: "Uses prior safety signals to optimize monitoring." },
  { name: "Investigator Brochures (IB)", note: "Extracts PK data to refine dosing schedules." },
  { name: "Regulatory Correspondence", note: "Incorporates FDA/EMA feedback to reduce risk." },
];

type StagedFile = {
  id: string;
  file: File;
  document_type: string | null;
  error: string | null;
};

function formatBytes(bytes: number): string {
  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(2)} MB`;
  const kb = bytes / 1024;
  return `${kb.toFixed(0)} KB`;
}

function makeStaged(file: File): StagedFile {
  let error: string | null = null;
  if (file.size > MAX_BYTES) error = "File exceeds 10 MB limit.";
  else if (file.type && !ACCEPT_MIMES.has(file.type) && !/\.(pdf|docx?|DOCX?|PDF)$/.test(file.name))
    error = "Unsupported format. Use PDF, DOC, or DOCX.";
  return {
    id: `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
    file,
    document_type: null,
    error,
  };
}

export default function AttachDocumentsModal({ open, onClose, onAttached }: Props) {
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [openTypeFor, setOpenTypeFor] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset state every time the modal opens.
  useEffect(() => {
    if (open) {
      setStaged([]);
      setUploading(false);
      setOpenTypeFor(null);
    }
  }, [open]);

  // ESC closes the modal.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !uploading) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, uploading, onClose]);

  const acceptFiles = useCallback((list: FileList | null) => {
    if (!list) return;
    const additions = Array.from(list).map(makeStaged);
    setStaged((prev) => [...prev, ...additions]);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      acceptFiles(e.dataTransfer.files);
    },
    [acceptFiles],
  );

  const removeStaged = (id: string) => {
    setStaged((prev) => prev.filter((f) => f.id !== id));
  };

  const setStagedType = (id: string, value: string) => {
    setStaged((prev) =>
      prev.map((f) => (f.id === id ? { ...f, document_type: value } : f)),
    );
    setOpenTypeFor(null);
  };

  const allTyped = staged.length > 0 && staged.every((f) => f.document_type && !f.error);
  const buttonLabel =
    staged.length === 0
      ? "Upload Documents"
      : `Attach ${staged.length} ${staged.length === 1 ? "File" : "Files"}`;

  const onAttach = async () => {
    if (staged.length === 0) {
      // Empty state: same button just opens the file picker.
      fileInputRef.current?.click();
      return;
    }
    if (!allTyped) return;

    setUploading(true);
    // Mock upload — replace with fetch('/api/uploads', {method:'POST', body: FormData}) when backend is ready.
    await new Promise((r) => setTimeout(r, 350));
    const docs: AttachedDocument[] = staged.map((s) => {
      const label =
        DOCUMENT_TYPES.find((t) => t.value === s.document_type)?.label ?? s.document_type ?? "";
      return {
        source_document_id: `mock-${crypto.randomUUID()}`,
        file_name: s.file.name,
        file_size_bytes: s.file.size,
        document_type: s.document_type ?? "",
        document_type_label: label,
      };
    });
    setUploading(false);
    onAttached(docs);
    onClose();
  };

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="attach-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !uploading) onClose();
      }}
    >
      <div className="w-full max-w-5xl max-h-[90vh] overflow-hidden rounded-2xl bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div
          className="px-7 py-5 text-white relative"
          style={{
            background:
              "linear-gradient(120deg, #5b1147 0%, #7d1f50 45%, #a51d70 100%)",
          }}
        >
          <button
            type="button"
            aria-label="Close"
            className="absolute right-5 top-5 h-8 w-8 grid place-items-center rounded-full text-white/80 hover:text-white hover:bg-white/10 transition"
            onClick={onClose}
            disabled={uploading}
          >
            <X size={18} />
          </button>
          <div className="flex items-center gap-3">
            <span className="h-9 w-9 grid place-items-center rounded-lg bg-white/15">
              <Sparkles size={18} />
            </span>
            <h2 id="attach-modal-title" className="font-slab text-2xl font-bold">
              Attach Documents
            </h2>
          </div>
          <p className="mt-2 text-sm text-white/85 max-w-3xl">
            Enhance your New Opportunity concepts by uploading relevant documents. This allows the
            AI to assess market opportunities more accurately, though you can proceed without these
            inputs.
          </p>
        </div>

        {/* Body */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 px-7 py-6 overflow-y-auto">
          {/* LEFT: guidance */}
          <section>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles size={16} className="text-velocia" />
              <h3 className="font-slab text-base font-bold text-ink">Maximize AI Performance</h3>
            </div>
            <p className="text-sm text-muted mb-4">
              While not mandatory, providing these documents allows the agent to deeply analyze
              your strategic goals and auto-populate study parameters.
            </p>

            <GuidanceGroup
              label="Highly Recommended"
              accent="bg-amber-50 border-amber-200"
              labelColor="text-amber-700"
              items={HIGHLY_RECOMMENDED}
              dotColor="text-amber-500"
            />

            <div className="h-3" />

            <GuidanceGroup
              label="Supporting Context"
              accent="bg-blue-50 border-blue-200"
              labelColor="text-blue-700"
              items={SUPPORTING_CONTEXT}
              dotColor="text-blue-500"
              icon="file"
            />
          </section>

          {/* RIGHT: upload */}
          <section className="flex flex-col">
            <div className="flex items-center gap-2 mb-1">
              <Upload size={16} className="text-velocia" />
              <h3 className="font-slab text-base font-bold text-ink">Attach Document</h3>
            </div>
            <p className="text-sm text-muted mb-4">
              Upload your strategic documents to enhance AI recommendations
            </p>

            {/* Staged files list */}
            <div className="space-y-3 mb-3">
              {staged.map((s) => (
                <StagedFileCard
                  key={s.id}
                  staged={s}
                  open={openTypeFor === s.id}
                  onToggle={() => setOpenTypeFor((cur) => (cur === s.id ? null : s.id))}
                  onPickType={(value) => setStagedType(s.id, value)}
                  onRemove={() => removeStaged(s.id)}
                />
              ))}
            </div>

            {/* Drop zone — large when empty, compact when files are staged */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={
                "flex-1 min-h-[140px] rounded-xl border-2 border-dashed text-center transition " +
                (dragOver
                  ? "border-velocia bg-velocia/5"
                  : "border-line bg-slate-50/40 hover:bg-slate-50") +
                (staged.length === 0 ? " p-10" : " p-6")
              }
            >
              {staged.length === 0 ? (
                <div className="flex flex-col items-center gap-3">
                  <span className="h-12 w-12 grid place-items-center rounded-full bg-white border border-line">
                    <Upload size={20} className="text-ink/60" />
                  </span>
                  <div>
                    <div className="font-slab text-lg font-bold text-ink">Upload documents</div>
                    <div className="text-sm text-muted mt-1">
                      Drag and drop your files here, or click to browse
                    </div>
                  </div>
                  <span className="pill-primary mt-2">Browse Files</span>
                  <div className="text-xs text-muted">
                    Supported formats: PDF, DOC, DOCX (Max 10MB)
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted">
                  Drag more files or{" "}
                  <span className="text-velocia font-semibold underline-offset-2 hover:underline">
                    browse
                  </span>
                </div>
              )}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT}
              multiple
              className="sr-only"
              onChange={(e) => {
                acceptFiles(e.target.files);
                e.target.value = "";
              }}
            />
          </section>
        </div>

        {/* Footer */}
        <div className="border-t border-line px-7 py-4 flex items-center justify-between">
          <button
            type="button"
            className="text-sm text-ink/70 hover:text-ink"
            onClick={onClose}
            disabled={uploading}
          >
            Cancel
          </button>
          <div className="flex items-center gap-4">
            {staged.length > 0 && !allTyped && (
              <span className="inline-flex items-center gap-1.5 text-sm text-amber-700">
                <AlertCircle size={14} />
                Assign document types to attach
              </span>
            )}
            <button
              type="button"
              onClick={onAttach}
              disabled={uploading || (staged.length > 0 && !allTyped)}
              className={
                "inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition " +
                (uploading || (staged.length > 0 && !allTyped)
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-velocia text-white hover:bg-velocia-hover")
              }
            >
              <Upload size={14} />
              {uploading ? "Attaching…" : buttonLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- internal sub-components ----------

interface GuidanceItem {
  name: string;
  note: string;
}

function GuidanceGroup({
  label,
  accent,
  labelColor,
  items,
  dotColor,
  icon,
}: {
  label: string;
  accent: string;
  labelColor: string;
  items: GuidanceItem[];
  dotColor: string;
  icon?: "dot" | "file";
}) {
  return (
    <div className={`rounded-xl border ${accent} px-4 py-3`}>
      <div className={`text-[11px] tracking-wider uppercase font-semibold mb-2 ${labelColor}`}>
        {label}
      </div>
      <ul className="space-y-2.5">
        {items.map((it) => (
          <li key={it.name} className="flex gap-2.5">
            {icon === "file" ? (
              <FileText size={15} className={`mt-0.5 shrink-0 ${dotColor}`} />
            ) : (
              <span
                className={`mt-1 h-3.5 w-3.5 shrink-0 rounded-full border-2 ${dotColor.replace("text-", "border-")}`}
              />
            )}
            <div>
              <div className="text-sm font-semibold text-ink">{it.name}</div>
              <div className={`text-xs ${labelColor}/80`}>{it.note}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StagedFileCard({
  staged,
  open,
  onToggle,
  onPickType,
  onRemove,
}: {
  staged: StagedFile;
  open: boolean;
  onToggle: () => void;
  onPickType: (value: string) => void;
  onRemove: () => void;
}) {
  const selectedLabel =
    DOCUMENT_TYPES.find((t) => t.value === staged.document_type)?.label ??
    "Select document type…";

  const needsType = !staged.document_type;
  const cardBorder = staged.error
    ? "border-red-300 bg-red-50/50"
    : needsType
      ? "border-amber-300 bg-amber-50/50"
      : "border-line bg-white";

  return (
    <div className={`rounded-xl border ${cardBorder} p-4`}>
      <div className="flex items-start gap-3">
        <span className="h-9 w-9 grid place-items-center rounded-lg bg-blue-50 text-blue-600 shrink-0">
          <FileText size={18} />
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="font-medium text-ink truncate">{staged.file.name}</div>
            <button
              type="button"
              aria-label="Remove file"
              onClick={onRemove}
              className="h-7 w-7 grid place-items-center rounded-full text-ink/50 hover:bg-slate-100 hover:text-ink/70 shrink-0"
            >
              <X size={14} />
            </button>
          </div>
          <div className="text-xs text-muted">{formatBytes(staged.file.size)}</div>
          {staged.error && (
            <div className="text-xs text-red-600 mt-1">{staged.error}</div>
          )}
        </div>
      </div>

      {/* Document Type dropdown — required */}
      {!staged.error && (
        <div className="mt-3">
          <label className="block text-xs font-medium text-ink mb-1.5">
            Document Type <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <button
              type="button"
              onClick={onToggle}
              className={
                "w-full flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm bg-white transition " +
                (needsType
                  ? "border-amber-300 text-amber-700"
                  : "border-line text-ink hover:bg-slate-50")
              }
            >
              <span className="flex items-center gap-2 truncate">
                {needsType && <AlertCircle size={14} />}
                <span className="truncate">{selectedLabel}</span>
              </span>
              <ChevronDown size={14} className="text-ink/50" />
            </button>
            {open && (
              <div className="absolute z-20 mt-1 w-full max-h-60 overflow-y-auto rounded-lg border border-line bg-white shadow-lg py-1">
                {DOCUMENT_TYPES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    className={
                      "w-full text-left px-3 py-2 text-sm hover:bg-slate-50 " +
                      (staged.document_type === t.value ? "bg-slate-50 font-medium" : "")
                    }
                    onClick={() => onPickType(t.value)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
