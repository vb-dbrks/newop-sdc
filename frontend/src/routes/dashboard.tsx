import { useEffect, useState } from "react";
import { getMe, type Me } from "@/lib/api";
import AppHeader from "@/components/shell/AppHeader";
import AuthoringComposer from "@/components/composer/AuthoringComposer";
import StudyPortfolioTable from "@/components/portfolio/StudyPortfolioTable";

export default function Dashboard() {
  const [me, setMe] = useState<Me | null>(null);
  const [meError, setMeError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then(setMe)
      .catch((e) => setMeError(String(e)));
  }, []);

  const firstName = me?.name?.split(" ")[0] ?? "Author";

  return (
    <div className="min-h-screen bg-white">
      <AppHeader me={me} />

      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(60% 90% at 18% 40%, rgba(165,29,112,0.18), transparent 60%)," +
              "radial-gradient(60% 90% at 82% 50%, rgba(236,72,153,0.18), transparent 60%)," +
              "linear-gradient(180deg, #fff7fb 0%, #fff 100%)",
          }}
        />
        <div className="relative px-6 pt-16 pb-14 flex flex-col items-center text-center">
          <div
            aria-hidden
            className="h-20 w-20 rounded-full mb-5"
            style={{
              background:
                "radial-gradient(circle at 35% 30%, #f0abfc 0%, #a51d70 55%, #4a0e36 100%)",
              boxShadow: "0 18px 40px -12px rgba(165,29,112,0.45)",
            }}
          />
          <h1 className="font-slab text-3xl md:text-4xl font-bold tracking-tight">
            Welcome, {firstName}
          </h1>
          <p className="mt-2 text-sm md:text-base text-muted max-w-2xl">
            Design your next breakthrough clinical trial with{" "}
            <span className="text-velocia font-semibold">AI-powered intelligence</span> and
            real-time simulations.
          </p>
          {meError && (
            <p className="mt-2 text-xs text-red-600">Auth: {meError}</p>
          )}
          <div className="mt-8 w-full">
            <AuthoringComposer />
          </div>
        </div>
      </section>

      <div className="mt-10">
        <StudyPortfolioTable />
      </div>
    </div>
  );
}
