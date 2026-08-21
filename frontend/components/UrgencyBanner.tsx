import type { Urgency } from "@/lib/types";
import { AlertTriangleIcon, CheckCircleIcon, ClockIcon } from "./icons";

const LABELS: Record<Urgency, string> = {
  emergency: "Emergency - see a vet now",
  soon: "See a vet soon (within a day or two)",
  home: "Likely okay to monitor at home",
};

const ICONS: Record<Urgency, React.ComponentType<{ className?: string }>> = {
  emergency: AlertTriangleIcon,
  soon: ClockIcon,
  home: CheckCircleIcon,
};

export default function UrgencyBanner({ urgency }: { urgency: Urgency | null }) {
  if (!urgency) return null;
  const Icon = ICONS[urgency];
  return (
    <div className={`urgency-banner ${urgency} px-6 py-2.5`}>
      <div className="max-w-3xl mx-auto flex items-center gap-2.5 text-[0.88rem] font-semibold">
        <span className="urgency-icon w-6 h-6 rounded-full flex items-center justify-center shrink-0">
          <Icon className="w-3.5 h-3.5" />
        </span>
        <span>{LABELS[urgency]}</span>
      </div>
    </div>
  );
}
