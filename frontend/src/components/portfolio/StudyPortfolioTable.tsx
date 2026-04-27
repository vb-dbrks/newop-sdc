import { useEffect, useMemo, useState } from "react";
import { Eye, Search, Trash2 } from "lucide-react";
import { getStudyDocuments, type DocumentType, type StudyDocumentSummary } from "@/lib/api";

type Filter = "all" | "new_opportunity" | "sdc" | "protocol";

const FILTERS: { value: Filter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "new_opportunity", label: "New Opportunity" },
  { value: "sdc", label: "SDC" },
  { value: "protocol", label: "Protocol" },
];

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function typeMeta(t: DocumentType): { label: string; subtitleKey: string; chip: string } {
  if (t === "new_opportunity") {
    return {
      label: "New Opportunity",
      subtitleKey: "New Opportunity",
      chip: "bg-amber-100 text-amber-800",
    };
  }
  if (t === "sdc") {
    return {
      label: "SDC/Protocol",
      subtitleKey: "SDC/Protocol",
      chip: "bg-blue-100 text-blue-700",
    };
  }
  return {
    label: "SDC/Protocol",
    subtitleKey: "SDC/Protocol",
    chip: "bg-blue-100 text-blue-700",
  };
}

function studyIdSuffix(id: string | null): string {
  if (!id) return "";
  const m = id.match(/(\d+)$/);
  return m ? m[1] : id;
}

export default function StudyPortfolioTable() {
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState<StudyDocumentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setItems(null);
    getStudyDocuments()
      .then((res) => {
        if (!cancelled) setItems(res.items);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!items) return [];
    return items.filter((d) => {
      if (filter !== "all" && d.document_type !== filter) return false;
      if (q.trim()) {
        const needle = q.toLowerCase();
        const hay = [
          d.study_id ?? "",
          d.study_brief_title ?? "",
          d.study_acronym ?? "",
          d.study_document_id,
        ]
          .join(" ")
          .toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      return true;
    });
  }, [items, filter, q]);

  return (
    <section className="mx-auto w-full max-w-6xl px-6 pb-16">
      <h2 className="font-slab text-xl font-bold text-ink">Study Portfolio</h2>
      <p className="text-sm text-muted mt-1">
        Browse New Opportunity and Study Design Concept (SDC) / Protocol documents across the
        portfolio in a single searchable table.
      </p>

      <div className="mt-5 relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none"
        />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          type="text"
          placeholder="Search by study ID, document title, or linked document ID…"
          className="w-full h-10 pl-9 pr-3 rounded-lg border border-line bg-white text-sm placeholder:text-muted focus:outline-none focus:border-velocia/60 focus:ring-2 focus:ring-velocia/15"
        />
      </div>

      <div className="flex items-center gap-2 mt-4">
        <span className="text-[11px] tracking-wider text-muted uppercase mr-1">Filter</span>
        {FILTERS.map((f) => {
          const active = filter === f.value;
          return (
            <button
              key={f.value}
              type="button"
              onClick={() => setFilter(f.value)}
              className={
                "px-3 py-1.5 rounded-full text-xs font-medium transition " +
                (active
                  ? "bg-velocia text-white"
                  : "bg-white text-ink/70 border border-line hover:bg-slate-50")
              }
            >
              {f.label}
            </button>
          );
        })}
      </div>

      <div className="mt-5 rounded-xl border border-line bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 text-[11px] tracking-wider text-muted uppercase">
              <th className="text-left font-medium px-4 py-3">Study ID</th>
              <th className="text-left font-medium px-4 py-3">Document Name</th>
              <th className="text-left font-medium px-4 py-3">Type</th>
              <th className="text-left font-medium px-4 py-3">Created At</th>
              <th className="text-left font-medium px-4 py-3">Created By</th>
              <th className="text-right font-medium px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {error && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-red-600">
                  Failed to load: {error}
                </td>
              </tr>
            )}
            {!error && items === null && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-muted">
                  Loading…
                </td>
              </tr>
            )}
            {!error && items !== null && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-sm text-muted">
                  No documents match your filters yet.
                </td>
              </tr>
            )}
            {filtered.map((d) => {
              const t = typeMeta(d.document_type);
              const suffix = studyIdSuffix(d.study_id);
              return (
                <tr key={d.study_document_id} className="border-t border-line hover:bg-slate-50/60">
                  <td className="px-4 py-3 align-top">
                    <span className="inline-flex items-center rounded-full border border-line bg-white px-2.5 py-0.5 text-xs font-medium text-ink/80">
                      {d.study_id ?? "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <div className="font-medium text-ink">
                      {d.study_brief_title ?? "Untitled"}
                    </div>
                    <div className="text-xs text-muted mt-0.5">
                      {t.subtitleKey}-{suffix}
                    </div>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <span
                      className={
                        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium " +
                        t.chip
                      }
                    >
                      {t.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 align-top text-ink/80">
                    {formatDate(d.last_modified_at)}
                  </td>
                  <td className="px-4 py-3 align-top text-ink/80">
                    {d.last_modified_by_name ?? "—"}
                  </td>
                  <td className="px-4 py-3 align-top">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        aria-label="View"
                        className="h-8 w-8 grid place-items-center rounded-full hover:bg-slate-100 text-ink/60"
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        type="button"
                        aria-label="Delete"
                        className="h-8 w-8 grid place-items-center rounded-full hover:bg-red-50 text-red-500/80"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
