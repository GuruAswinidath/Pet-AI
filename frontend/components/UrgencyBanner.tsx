import type { Urgency } from "@/lib/types";

const LABELS: Record<Urgency, string> = {
  emergency: "Emergency - see a vet now",
  soon: "See a vet soon (within a day or two)",
  home: "Likely okay to monitor at home",
};

export default function UrgencyBanner({ urgency }: { urgency: Urgency | null }) {
  if (!urgency) return null;
  return (
    <div className={`urgency-banner ${urgency} flex items-center gap-2 px-6 py-2.5 text-[0.88rem] font-semibold border-b border-[var(--border)]`}>
      <span className="urgency-dot w-[9px] h-[9px] rounded-full shrink-0" />
      <span>{LABELS[urgency]}</span>
    </div>
  );
}
