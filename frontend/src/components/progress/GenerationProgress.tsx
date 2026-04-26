// TODO: render named-step checklist driven by agent_runs.step_history.
// STEP_LABELS dictionary maps machine names → friendly copy. See ADR 0013.

export const STEP_LABELS: Record<string, string> = {
  analyzing_internal_assets: "Analyzing Internal Assets",
  cross_referencing_trials: "Cross-referencing Reference Trials",
  simulating_feasibility: "Simulating Feasibility",
  drafting_concepts: "Drafting Concepts",
};

export default function GenerationProgress() {
  return null;
}
