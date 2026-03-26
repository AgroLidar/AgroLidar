"use client";

import Image from "next/image";
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  Compass,
  Cpu,
  Gauge,
  Radar,
  Shield,
  Sprout,
  Tractor,
  Waves,
  Zap
} from "lucide-react";
import { motion } from "framer-motion";
import logo from "../assets/logo.png";

const navItems = [
  ["Problem", "#problem"],
  ["Solution", "#solution"],
  ["Capabilities", "#capabilities"],
  ["How It Works", "#how-it-works"],
  ["Use Cases", "#use-cases"],
  ["Vision", "#vision"]
];

const capabilities = [
  {
    title: "Obstacle Detection",
    description: "Detects humans, animals, vehicles, equipment, and field-edge objects in real time.",
    icon: AlertTriangle
  },
  {
    title: "Hazard Scoring",
    description: "Prioritizes threats based on distance, trajectory, and operational context.",
    icon: Shield
  },
  {
    title: "Terrain-Aware Perception",
    description: "Understands ruts, slopes, berms, and uneven surfaces for stable machine behavior.",
    icon: Compass
  },
  {
    title: "Temporal Tracking",
    description: "Maintains object continuity through dust plumes, occlusions, and vibration.",
    icon: Waves
  },
  {
    title: "Velocity & Collision Risk",
    description: "Estimates relative velocity and likely impact zones before dangerous events emerge.",
    icon: Gauge
  },
  {
    title: "Harsh-Condition Robustness",
    description: "Built to remain dependable in rain, low visibility, dense vegetation, and debris.",
    icon: Sprout
  }
];

const pipeline = [
  "LiDAR Input",
  "Signal Conditioning",
  "BEV Perception",
  "Neural Inference",
  "Obstacle Understanding",
  "Risk Analysis"
];

const useCases = [
  "Autonomous tractors operating across large, unstructured fields",
  "Driver-assistance systems for hazard alerts and safer maneuvering",
  "Smart obstacle awareness for mixed human-machine environments",
  "Field safety systems for low-visibility and night operations",
  "Perception layer inside precision agriculture autonomy stacks"
];

const sectionReveal = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: 0.2 },
  transition: { duration: 0.7, ease: "easeOut" }
};

export function LandingPage() {
  return (
    <main className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-overlay" />
      <div className="pointer-events-none absolute left-[-10%] top-24 h-80 w-80 rounded-full bg-brand-500/20 blur-3xl" />
      <div className="pointer-events-none absolute right-[-8%] top-[28rem] h-[28rem] w-[28rem] rounded-full bg-emerald-700/20 blur-3xl" />

      <header className="sticky top-0 z-40 border-b border-white/10 bg-[#050b08]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
          <a href="#top" className="flex items-center gap-3">
            <Image src={logo} alt="AgroLidar logo" className="h-12 w-auto" priority />
            <span className="text-sm font-medium tracking-[0.18em] text-brand-200">AGROLIDAR</span>
          </a>
          <nav className="hidden items-center gap-7 text-sm text-white/70 lg:flex">
            {navItems.map(([label, href]) => (
              <a key={label} href={href} className="transition hover:text-white">
                {label}
              </a>
            ))}
          </nav>
          <a
            href="#final-cta"
            className="rounded-full border border-brand-300/30 bg-brand-400/10 px-5 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-brand-100 transition hover:bg-brand-400/20"
          >
            Contact
          </a>
        </div>
      </header>

      <section id="top" className="relative mx-auto max-w-7xl px-6 pb-28 pt-24 lg:px-10 lg:pt-32">
        <motion.div {...sectionReveal} className="max-w-4xl">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.18em] text-white/70">
            <Radar className="h-4 w-4 text-brand-300" />
            Perception for the field
          </div>
          <h1 className="text-4xl font-semibold leading-tight sm:text-6xl lg:text-7xl">
            LiDAR intelligence for the next generation of agricultural machines.
          </h1>
          <p className="mt-8 max-w-2xl text-base leading-relaxed text-white/75 sm:text-xl">
            AgroLidar delivers dependable perception for tractors and agricultural vehicles working in dust,
            rain, low visibility, and uneven terrain—where road-focused autonomy systems fail.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <a
              href="#solution"
              className="inline-flex items-center gap-2 rounded-full bg-brand-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-brand-300"
            >
              Explore Technology <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="#final-cta"
              className="rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              View Project
            </a>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.9, ease: "easeOut" }}
          className="mt-16 grid gap-4 sm:grid-cols-3"
        >
          {[
            ["Built for", "Agricultural environments"],
            ["Latency", "Real-time field response"],
            ["Deployment", "Edge-ready architecture"]
          ].map(([label, value]) => (
            <div key={label} className="glass-panel rounded-2xl p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.14em] text-white/50">{label}</p>
              <p className="mt-2 text-lg font-medium text-white/95">{value}</p>
            </div>
          ))}
        </motion.div>
      </section>

      <div className="section-divider mx-auto max-w-7xl" />

      <Section id="problem" title="The Field Is Not the Road" subtitle="Why traditional autonomy stacks break down in agriculture.">
        <p>
          Most perception systems were engineered for structured roads, lane markings, and predictable traffic
          patterns. Agricultural operations happen in dynamic, unstructured spaces with moving vegetation,
          particulate dust, rain distortion, uneven soil, and irregular terrain geometry.
        </p>
        <p>
          In the field, reliability is safety. AgroLidar is purpose-built for these conditions, not adapted from
          city autonomy assumptions.
        </p>
      </Section>

      <Section id="solution" title="A Perception System Designed for Agriculture" subtitle="Real-time LiDAR intelligence for tractors and agricultural platforms.">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Obstacle Detection", "Reliable identification of critical objects and obstacles in-field.", Radar],
            ["Hazard Analysis", "Continuous scene assessment with confidence-aware risk scoring.", Shield],
            ["Terrain Understanding", "Rich 3D awareness of field geometry and machine-relevant surfaces.", Tractor],
            ["Temporal Tracking", "Persistent object context across changing environmental conditions.", BrainCircuit]
          ].map(([title, desc, Icon]) => (
            <div key={title as string} className="glass-panel rounded-2xl p-5">
              <Icon className="h-5 w-5 text-brand-300" />
              <h3 className="mt-3 text-lg font-medium">{title as string}</h3>
              <p className="mt-2 text-sm text-white/70">{desc as string}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="capabilities" title="Core Capabilities" subtitle="High-confidence perception under harsh real-world constraints.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {capabilities.map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.article
                key={item.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.45, delay: i * 0.05 }}
                className="group glass-panel rounded-2xl p-6 transition hover:-translate-y-1 hover:border-brand-300/40"
              >
                <Icon className="h-5 w-5 text-brand-300" />
                <h3 className="mt-4 text-lg font-medium text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-white/70">{item.description}</p>
              </motion.article>
            );
          })}
        </div>
      </Section>

      <Section id="how-it-works" title="How It Works" subtitle="From raw LiDAR returns to operational safety decisions.">
        <div className="grid gap-3 md:grid-cols-6">
          {pipeline.map((step, i) => (
            <div key={step} className="relative rounded-xl border border-white/15 bg-white/5 p-4 text-center text-sm">
              <span className="text-xs uppercase tracking-[0.12em] text-brand-200/90">0{i + 1}</span>
              <p className="mt-2 text-white/90">{step}</p>
              {i < pipeline.length - 1 && (
                <ArrowRight className="absolute -right-2 top-1/2 hidden h-4 w-4 -translate-y-1/2 text-brand-200 md:block" />
              )}
            </div>
          ))}
        </div>
      </Section>

      <Section id="why-agrolidar" title="Why AgroLidar" subtitle="Built for field autonomy, not repurposed from road autonomy.">
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <div className="grid text-sm md:grid-cols-2">
            <div className="bg-white/5 p-6">
              <p className="mb-4 text-xs uppercase tracking-[0.14em] text-white/55">Road Autonomy Bias</p>
              <ul className="space-y-3 text-white/75">
                <li>Optimized for lanes, signs, and structured traffic rules</li>
                <li>Assumes consistent surfaces and map priors</li>
                <li>Sensitive to dust, occlusion, and non-urban clutter</li>
              </ul>
            </div>
            <div className="bg-brand-500/10 p-6">
              <p className="mb-4 text-xs uppercase tracking-[0.14em] text-brand-100">AgroLidar Advantage</p>
              <ul className="space-y-3 text-white/90">
                <li>Designed for unstructured fields and evolving terrain</li>
                <li>Understands agricultural machine behavior and constraints</li>
                <li>Maintains perception confidence in harsh, noisy environments</li>
              </ul>
            </div>
          </div>
        </div>
      </Section>

      <Section id="use-cases" title="Use Cases" subtitle="Where AgroLidar creates immediate operational value.">
        <div className="grid gap-4 md:grid-cols-2">
          {useCases.map((item) => (
            <div key={item} className="glass-panel flex items-start gap-3 rounded-2xl p-5">
              <Cpu className="mt-0.5 h-5 w-5 shrink-0 text-brand-300" />
              <p className="text-white/85">{item}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="vision" title="Vision" subtitle="The perception layer for next-generation agricultural autonomy.">
        <p>
          AgroLidar is building toward scalable, production-ready perception across machine categories and field
          types. Our roadmap expands into sensor fusion, larger real-world data loops, edge optimization, and
          autonomous farm operations at fleet scale.
        </p>
        <p>
          The mission is clear: accelerate safe, intelligent agriculture by giving machines robust awareness where
          it matters most—the field.
        </p>
      </Section>

      <section id="final-cta" className="mx-auto max-w-7xl px-6 pb-28 pt-10 lg:px-10">
        <motion.div
          {...sectionReveal}
          className="relative overflow-hidden rounded-3xl border border-brand-300/25 bg-gradient-to-br from-brand-500/20 via-[#0d1f15] to-[#06110c] p-8 shadow-glow md:p-12"
        >
          <div className="absolute -right-16 top-0 h-52 w-52 rounded-full bg-brand-300/20 blur-3xl" />
          <Zap className="h-6 w-6 text-brand-200" />
          <h2 className="mt-4 max-w-2xl text-3xl font-semibold sm:text-4xl">
            Building safer, smarter machines for the field.
          </h2>
          <p className="mt-4 max-w-2xl text-white/75">
            Partner with AgroLidar to bring resilient perception into agricultural fleets and future autonomy
            platforms.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a className="rounded-full bg-brand-300 px-5 py-3 text-sm font-semibold text-black" href="#top">
              View Project
            </a>
            <a className="rounded-full border border-white/20 px-5 py-3 text-sm font-semibold" href="mailto:geromendez199@gmail.com">
              Contact
            </a>
            <a className="rounded-full border border-brand-200/35 bg-brand-300/10 px-5 py-3 text-sm font-semibold text-brand-100" href="#solution">
              Explore Technology
            </a>
          </div>
        </motion.div>
      </section>

      <footer className="border-t border-white/10 py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-6 text-sm text-white/55 md:flex-row lg:px-10">
          <p>© {new Date().getFullYear()} AgroLidar. Perception for the field.</p>
          <p>LiDAR intelligence for autonomous and assisted agricultural machines.</p>
        </div>
      </footer>
    </main>
  );
}

function Section({
  id,
  title,
  subtitle,
  children
}: {
  id: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="mx-auto max-w-7xl px-6 py-16 lg:px-10 lg:py-20">
      <motion.div {...sectionReveal} className="mx-auto max-w-4xl">
        <p className="text-xs uppercase tracking-[0.14em] text-brand-200/90">{subtitle}</p>
        <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">{title}</h2>
        <div className="mt-8 space-y-5 text-base leading-relaxed text-white/75">{children}</div>
      </motion.div>
    </section>
  );
}
