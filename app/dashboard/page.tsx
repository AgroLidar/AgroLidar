"use client";

import { motion } from "framer-motion";
import { IBM_Plex_Mono, Oxanium } from "next/font/google";
import { useEffect, useMemo, useState } from "react";

const oxanium = Oxanium({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const ibmPlexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"] });

type RiskLevel = "SAFE" | "CAUTION" | "CRITICAL";

interface Detection {
  id: string;
  className: string;
  confidence: number;
  distanceMeters: number;
  zone: {
    x: number;
    y: number;
    risk: RiskLevel;
  };
}

interface FrameStatsData {
  latencyMs: number;
  totalPoints: number;
  modelVersion: string;
  frameId: number;
  updatedAt: string;
}

interface StatusPayload {
  riskLevel: RiskLevel;
  detections: Detection[];
  frameStats: FrameStatsData;
}

const riskStyles: Record<RiskLevel, string> = {
  SAFE: "border-[#4ADE80]/60 bg-[#4ADE80]/10 text-[#86efac]",
  CAUTION: "border-[#38BDF8]/60 bg-[#38BDF8]/10 text-[#7dd3fc]",
  CRITICAL: "border-[#F59E0B]/80 bg-[#F59E0B]/15 text-[#fbbf24]"
};

const riskPulse: Record<RiskLevel, string> = {
  SAFE: "shadow-[0_0_0_0_rgba(74,222,128,0.25)]",
  CAUTION: "shadow-[0_0_0_0_rgba(56,189,248,0.28)]",
  CRITICAL: "shadow-[0_0_30px_4px_rgba(245,158,11,0.45)]"
};

const mockStatus: StatusPayload = {
  riskLevel: "CAUTION",
  detections: [
    {
      id: "det-01",
      className: "human",
      confidence: 0.92,
      distanceMeters: 11.4,
      zone: { x: 26, y: 74, risk: "CRITICAL" }
    },
    {
      id: "det-02",
      className: "vehicle",
      confidence: 0.88,
      distanceMeters: 19.8,
      zone: { x: 56, y: 44, risk: "CAUTION" }
    },
    {
      id: "det-03",
      className: "animal",
      confidence: 0.71,
      distanceMeters: 31.6,
      zone: { x: 70, y: 60, risk: "SAFE" }
    }
  ],
  frameStats: {
    latencyMs: 46,
    totalPoints: 127420,
    modelVersion: "bevnet-r3.9.2",
    frameId: 4082,
    updatedAt: new Date().toISOString()
  }
};

const asRiskLevel = (value: unknown): RiskLevel | null => {
  if (value === "SAFE" || value === "CAUTION" || value === "CRITICAL") {
    return value;
  }
  return null;
};

const sanitizeStatusPayload = (payload: unknown): StatusPayload | null => {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }

  const candidate = payload as Partial<StatusPayload>;
  const parsedRisk = asRiskLevel(candidate.riskLevel);

  if (!parsedRisk || !Array.isArray(candidate.detections) || typeof candidate.frameStats !== "object" || candidate.frameStats === null) {
    return null;
  }

  const detections: Detection[] = candidate.detections
    .map((item) => {
      if (typeof item !== "object" || item === null) {
        return null;
      }

      const detection = item as Partial<Detection>;
      const risk = asRiskLevel(detection.zone?.risk);

      if (
        typeof detection.id !== "string" ||
        typeof detection.className !== "string" ||
        typeof detection.confidence !== "number" ||
        typeof detection.distanceMeters !== "number" ||
        typeof detection.zone?.x !== "number" ||
        typeof detection.zone?.y !== "number" ||
        !risk
      ) {
        return null;
      }

      return {
        id: detection.id,
        className: detection.className,
        confidence: Math.min(Math.max(detection.confidence, 0), 1),
        distanceMeters: Math.max(detection.distanceMeters, 0),
        zone: {
          x: Math.min(Math.max(detection.zone.x, 0), 100),
          y: Math.min(Math.max(detection.zone.y, 0), 100),
          risk
        }
      };
    })
    .filter((item): item is Detection => item !== null);

  const stats = candidate.frameStats as Partial<FrameStatsData>;

  if (
    typeof stats.latencyMs !== "number" ||
    typeof stats.totalPoints !== "number" ||
    typeof stats.modelVersion !== "string" ||
    typeof stats.frameId !== "number" ||
    typeof stats.updatedAt !== "string"
  ) {
    return null;
  }

  return {
    riskLevel: parsedRisk,
    detections,
    frameStats: {
      latencyMs: Math.max(stats.latencyMs, 0),
      totalPoints: Math.max(stats.totalPoints, 0),
      modelVersion: stats.modelVersion,
      frameId: Math.max(Math.floor(stats.frameId), 0),
      updatedAt: stats.updatedAt
    }
  };
};

function RiskLevelBadge({ riskLevel }: { riskLevel: RiskLevel }) {
  const isCritical = riskLevel === "CRITICAL";

  return (
    <motion.div
      animate={
        isCritical
          ? { scale: [1, 1.04, 1], opacity: [0.85, 1, 0.85] }
          : { scale: 1, opacity: 1 }
      }
      transition={
        isCritical
          ? { duration: 1.1, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }
          : { duration: 0.2 }
      }
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold tracking-[0.12em] ${riskStyles[riskLevel]} ${riskPulse[riskLevel]} ${ibmPlexMono.className}`}
    >
      <span className="h-2.5 w-2.5 rounded-full bg-current" />
      {riskLevel}
    </motion.div>
  );
}

function DetectionCard({ detection }: { detection: Detection }) {
  const confidencePercent = Math.round(detection.confidence * 100);

  return (
    <article className="rounded-lg border border-white/15 bg-black/35 p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className={`text-sm uppercase tracking-[0.16em] text-white/70 ${ibmPlexMono.className}`}>{detection.className}</p>
        <RiskLevelBadge riskLevel={detection.zone.risk} />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-white/70">
          <span className={ibmPlexMono.className}>CONFIDENCE</span>
          <span className={ibmPlexMono.className}>{confidencePercent}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full border border-white/10 bg-[#0f141a]">
          <div
            className="h-full rounded-full bg-[#38BDF8] transition-all duration-500"
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      <div className="mt-3 flex items-end justify-between border-t border-white/10 pt-3">
        <p className={`text-xs text-white/55 ${ibmPlexMono.className}`}>RANGE</p>
        <p className={`text-lg text-white ${ibmPlexMono.className}`}>{detection.distanceMeters.toFixed(1)} m</p>
      </div>
    </article>
  );
}

function FrameStats({ stats }: { stats: FrameStatsData }) {
  return (
    <section className="grid gap-3 sm:grid-cols-3">
      <article className="rounded-lg border border-white/15 bg-black/35 p-4">
        <p className={`text-xs tracking-[0.14em] text-white/60 ${ibmPlexMono.className}`}>LATENCY</p>
        <p className={`mt-2 text-2xl text-[#38BDF8] ${ibmPlexMono.className}`}>{stats.latencyMs} ms</p>
      </article>
      <article className="rounded-lg border border-white/15 bg-black/35 p-4">
        <p className={`text-xs tracking-[0.14em] text-white/60 ${ibmPlexMono.className}`}>POINTS</p>
        <p className={`mt-2 text-2xl text-[#4ADE80] ${ibmPlexMono.className}`}>{stats.totalPoints.toLocaleString()}</p>
      </article>
      <article className="rounded-lg border border-white/15 bg-black/35 p-4">
        <p className={`text-xs tracking-[0.14em] text-white/60 ${ibmPlexMono.className}`}>MODEL</p>
        <p className={`mt-2 text-2xl text-[#F59E0B] ${ibmPlexMono.className}`}>{stats.modelVersion}</p>
      </article>
    </section>
  );
}

function HazardMap({ detections }: { detections: Detection[] }) {
  return (
    <section className="rounded-lg border border-white/15 bg-black/35 p-4">
      <h2 className={`mb-3 text-sm uppercase tracking-[0.14em] text-white/75 ${ibmPlexMono.className}`}>Hazard Map (BEV)</h2>
      <svg viewBox="0 0 100 100" className="h-64 w-full rounded-md border border-white/10 bg-[#090d12]">
        {Array.from({ length: 10 }, (_, idx) => {
          const value = idx * 10;
          return (
            <g key={`grid-${value}`}>
              <line x1={value} y1={0} x2={value} y2={100} stroke="rgba(255,255,255,0.08)" strokeWidth="0.35" />
              <line x1={0} y1={value} x2={100} y2={value} stroke="rgba(255,255,255,0.08)" strokeWidth="0.35" />
            </g>
          );
        })}
        <rect x="35" y="82" width="30" height="12" fill="rgba(56,189,248,0.15)" stroke="rgba(56,189,248,0.9)" strokeWidth="0.8" />
        {detections.map((det) => {
          const color = det.zone.risk === "CRITICAL" ? "#F59E0B" : det.zone.risk === "CAUTION" ? "#38BDF8" : "#4ADE80";
          return (
            <g key={det.id}>
              <circle cx={det.zone.x} cy={det.zone.y} r={3.6} fill={color} fillOpacity="0.22" />
              <circle cx={det.zone.x} cy={det.zone.y} r={1.5} fill={color} />
              <text x={det.zone.x + 2.2} y={det.zone.y - 1.6} fill={color} fontSize="3.2" className={ibmPlexMono.className}>
                {det.className}
              </text>
            </g>
          );
        })}
      </svg>
    </section>
  );
}

function LiveFeed({ data }: { data: StatusPayload }) {
  return (
    <section className="rounded-lg border border-white/15 bg-black/35 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className={`text-sm uppercase tracking-[0.14em] text-white/75 ${ibmPlexMono.className}`}>Live Feed</h2>
        <p className={`text-xs text-white/55 ${ibmPlexMono.className}`}>Frame #{data.frameStats.frameId}</p>
      </div>
      <div className="space-y-3">
        {data.detections.map((det) => (
          <DetectionCard key={det.id} detection={det} />
        ))}
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusPayload>(mockStatus);

  useEffect(() => {
    let mounted = true;

    const refreshStatus = async () => {
      try {
        const response = await fetch("/v1/status", { cache: "no-store" });
        if (!response.ok) {
          throw new Error("Status endpoint unavailable");
        }

        const payload: unknown = await response.json();
        const parsed = sanitizeStatusPayload(payload);

        if (mounted && parsed) {
          setStatus(parsed);
        }
      } catch {
        if (mounted) {
          setStatus((previous) => ({
            ...previous,
            frameStats: {
              ...previous.frameStats,
              frameId: previous.frameStats.frameId + 1,
              updatedAt: new Date().toISOString()
            }
          }));
        }
      }
    };

    refreshStatus();
    const intervalId = window.setInterval(refreshStatus, 500);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const formattedTime = useMemo(() => new Date(status.frameStats.updatedAt).toLocaleTimeString(), [status.frameStats.updatedAt]);

  return (
    <main
      className="min-h-screen bg-[#0a0c0f] px-6 py-8 text-white"
      style={{
        backgroundImage:
          "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
        backgroundSize: "30px 30px"
      }}
    >
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <header className="rounded-xl border border-white/15 bg-black/35 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className={`text-xs uppercase tracking-[0.22em] text-white/60 ${ibmPlexMono.className}`}>AgroLidar · Real-time Monitoring</p>
              <h1 className={`mt-2 text-3xl tracking-wide text-white sm:text-4xl ${oxanium.className}`}>Detection Command Dashboard</h1>
            </div>
            <RiskLevelBadge riskLevel={status.riskLevel} />
          </div>
          <p className={`mt-3 text-xs text-white/55 ${ibmPlexMono.className}`}>Last update: {formattedTime} UTC</p>
        </header>

        <FrameStats stats={status.frameStats} />

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <HazardMap detections={status.detections} />
          <LiveFeed data={status} />
        </section>
      </div>
    </main>
  );
}
