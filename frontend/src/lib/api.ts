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
