import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import GradientBadge from "@/design/GradientBadge";

export default function Landing() {
  const nav = useNavigate();
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-6">
      <GradientBadge size={200} />
      <h1 className="font-slab text-5xl font-bold tracking-tight">Velocia</h1>
      <p className="text-muted text-center max-w-xl">
        Automate Clinical Study Authoring — Orchestrated by Intelligent Agents.
      </p>
      <button onClick={() => nav("/dashboard")} className="pill-primary mt-2">
        Enter Velocia
        <ArrowRight size={18} />
      </button>
    </main>
  );
}
