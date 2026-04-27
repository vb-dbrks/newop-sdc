export interface Me {
  user_id: string;
  sso_subject: string;
  email: string;
  name: string;
  onboarded_at: string;
}

export type DocumentType = "new_opportunity" | "sdc" | "protocol";
export type StudyStatus = "draft" | "in_review" | "approved";

export interface StudyDocumentSummary {
  study_document_id: string;
  document_type: DocumentType;
  study_status: StudyStatus;
  study_brief_title: string | null;
  study_acronym: string | null;
  study_id: string | null;
  last_modified_at: string;
  last_modified_by_name: string | null;
}

export interface StudyDocumentList {
  items: StudyDocumentSummary[];
  next_page: string | null;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} — ${text}`);
  }
  return res.json() as Promise<T>;
}

export const getMe = () => request<Me>("/api/me");

/**
 * Display-name fallback for users whose `name` was stored as their email
 * (typically when the SSO proxy didn't carry a preferred-username header).
 * "alice.smith@customer.com" → "Alice Smith".
 *
 * The backend now does the same derivation at bootstrap time and self-heals
 * existing email-shaped rows on next login (see backend/auth/sso.py and
 * backend/db/repositories/users.py). This is defense-in-depth so the UI
 * never renders "Welcome, alice@customer.com" even if a request lands on
 * an old row before the backend redeploy completes.
 */
export function displayNameOf(name: string | undefined | null): string {
  if (!name) return "";
  if (!name.includes("@")) return name;
  const local = name.split("@")[0];
  const parts = local.split(/[._\-+]/).filter(Boolean);
  if (parts.length === 0) return name;
  return parts.map((p) => p[0].toUpperCase() + p.slice(1)).join(" ");
}

export const getStudyDocuments = (params: {
  document_type?: DocumentType;
  q?: string;
} = {}) => {
  const search = new URLSearchParams();
  if (params.document_type) search.set("document_type", params.document_type);
  if (params.q) search.set("q", params.q);
  const qs = search.toString();
  return request<StudyDocumentList>(
    `/api/study-documents${qs ? `?${qs}` : ""}`,
  );
};
