import { useState } from "react";
import { ArrowRight, ChevronDown, Paperclip, Sparkles } from "lucide-react";

const TYPES = [
  { value: "new_opportunity", label: "New Opportunity" },
  { value: "sdc", label: "Study Design Concept" },
  { value: "protocol", label: "Protocol" },
] as const;

type DocType = (typeof TYPES)[number]["value"];

export default function AuthoringComposer() {
  const [prompt, setPrompt] = useState("");
  const [docType, setDocType] = useState<DocType | "">("");
  const [typeOpen, setTypeOpen] = useState(false);
  const canGenerate = prompt.trim().length > 0 && docType !== "";

  const selectedLabel = TYPES.find((t) => t.value === docType)?.label ?? "Select type";

  return (
    <div className="mx-auto w-full max-w-3xl rounded-2xl border border-line bg-white shadow-[0_12px_40px_-20px_rgba(15,23,42,0.18)] p-4">
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
            className="h-8 w-8 grid place-items-center rounded-full hover:bg-slate-100 text-ink/60"
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
  );
}
