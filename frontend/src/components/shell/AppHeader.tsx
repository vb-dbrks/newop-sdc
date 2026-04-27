import { Bell, ChevronDown } from "lucide-react";
import logo from "@/assets/velocia-logo.png";
import type { Me } from "@/lib/api";

interface Props {
  me: Me | null;
}

function initials(name: string | undefined): string {
  if (!name) return "AU";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function AppHeader({ me }: Props) {
  const displayName = me?.name?.split(" ")[0] ?? "Author";
  return (
    <header className="sticky top-0 z-20 bg-white/90 backdrop-blur border-b border-line">
      <div className="flex items-center justify-between h-14 px-6">
        <div className="flex items-center gap-6">
          <img src={logo} alt="Velocia" className="h-7 w-auto" draggable={false} />
          <span className="h-5 w-px bg-line" />
          <span className="text-sm text-ink/80">Home</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Notifications"
            className="relative h-9 w-9 grid place-items-center rounded-full hover:bg-slate-100 transition"
          >
            <Bell size={18} className="text-ink/70" />
            <span className="absolute top-1.5 right-1.5 h-4 min-w-4 px-1 grid place-items-center rounded-full bg-velocia text-white text-[10px] font-semibold">
              1
            </span>
          </button>
          <button
            type="button"
            className="flex items-center gap-2 pr-2 pl-1 py-1 rounded-full hover:bg-slate-100 transition"
          >
            <span className="h-7 w-7 grid place-items-center rounded-full bg-velocia/10 text-velocia text-xs font-semibold">
              {initials(me?.name)}
            </span>
            <span className="text-sm text-ink/80">{displayName}</span>
            <ChevronDown size={14} className="text-ink/50" />
          </button>
        </div>
      </div>
    </header>
  );
}
