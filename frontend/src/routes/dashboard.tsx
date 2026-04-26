import { useEffect, useState } from "react";
import { getMe, type Me } from "@/lib/api";

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then(setMe)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="min-h-screen px-8 py-10">
      <header className="flex items-center justify-between border-b border-line pb-4 mb-10">
        <span className="font-slab text-2xl font-bold">Velocia</span>
        <span className="text-sm text-muted">
          {error ? "auth error" : me ? me.display_name : "…"}
        </span>
      </header>

      <section className="max-w-4xl mx-auto text-center">
        <h1 className="font-slab text-4xl font-bold mb-3">
          Welcome{me ? `, ${me.display_name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-muted">
          Design your next breakthrough clinical trial with{" "}
          <span className="text-velocia font-semibold">AI-powered intelligence</span> and real-time
          simulations.
        </p>
        <p className="text-xs text-muted mt-12">
          Composer + portfolio + document views — coming next.
        </p>
      </section>
    </main>
  );
}
