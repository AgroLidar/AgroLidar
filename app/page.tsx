import Image from "next/image";
import { Badge } from "@/components/Badge";
import { CodeBlock } from "@/components/CodeBlock";
import { SectionTitle } from "@/components/SectionTitle";

const detectionTargets = ["human", "animal", "rock", "post", "vehicle"];

const problemCards = [
  "🌾 Unstructured terrain",
  "🌫️ Dust, rain, and low visibility",
  "🐄 Dynamic mixed environments"
];

const pipeline = ["LiDAR", "BEV", "Inference", "Hazard", "Alert"];

export default function Page() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-black px-6 py-16 text-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-20">
        <section className="w-full text-center">
          <div className="mx-auto mb-8 flex h-16 w-16 items-center justify-center rounded-2xl border border-emerald-300/30 bg-white/5 shadow-lg shadow-emerald-900/20">
            <Image src="/logo.svg" alt="AgroLidar logo" width={36} height={36} priority />
          </div>

          <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2">
            <Badge variant="success">Field-first autonomy</Badge>
            <Badge variant="default">LiDAR safety layer</Badge>
            <Badge variant="warning">Built for harsh conditions</Badge>
          </div>

          <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl">Perception for the field.</h1>
          <p className="mt-4 text-base text-white/75 sm:text-lg">
            LiDAR-based safety perception for agricultural machines.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#sandbox"
              className="rounded-md bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-black transition duration-300 hover:-translate-y-0.5 hover:bg-emerald-300"
            >
              Try the Sandbox
            </a>
            <a
              href="/docs"
              className="rounded-md border border-white/20 px-5 py-2.5 text-sm font-semibold text-white transition duration-300 hover:bg-white/10"
            >
              View Docs
            </a>
          </div>
        </section>

        <section className="space-y-8">
          <SectionTitle
            align="center"
            title="Most autonomous systems are built for cities."
            subtitle="Agricultural autonomy requires robust perception in environments that are noisy, irregular, and continuously changing."
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {problemCards.map((card) => (
              <article
                key={card}
                className="rounded-xl border border-white/10 bg-white/5 p-5 text-sm text-white/90 backdrop-blur transition duration-300 hover:-translate-y-0.5 hover:border-white/20"
              >
                {card}
              </article>
            ))}
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-2 lg:items-start">
          <div className="space-y-4">
            <SectionTitle title="What AgroLidar does" subtitle="Reliable object detection and scene understanding, designed for the field." />
            <ul className="grid grid-cols-2 gap-3 text-sm text-white/85 sm:grid-cols-3">
              {detectionTargets.map((target) => (
                <li
                  key={target}
                  className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-center capitalize transition duration-300 hover:border-emerald-300/30 hover:text-emerald-100"
                >
                  {target}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/5 p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-white/70">Pipeline</h3>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm font-medium text-emerald-200">
              {pipeline.map((step, index) => (
                <span key={step} className="flex items-center gap-2">
                  <span className="rounded-md border border-emerald-300/30 bg-emerald-300/10 px-2.5 py-1">{step}</span>
                  {index < pipeline.length - 1 ? <span className="text-white/40">→</span> : null}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-rose-300/20 bg-rose-300/5 p-6">
          <SectionTitle
            title="Safety is enforced, not assumed."
            subtitle="No online self-training in production; deterministic behavior where it matters most."
          />
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-white/10 bg-black/20 p-4">
              <p className="text-xs uppercase tracking-wide text-white/60">dangerous_fnr</p>
              <p className="mt-1 text-2xl font-semibold text-rose-200">10%</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-black/20 p-4">
              <p className="text-xs uppercase tracking-wide text-white/60">human recall</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-200">90%</p>
            </div>
          </div>
        </section>

        <section
          id="sandbox"
          className="scroll-mt-24 rounded-2xl border border-white/10 bg-white/5 p-6"
        >
          <SectionTitle
            title="Sandbox"
            subtitle="Run the full local workflow and test the landing stack quickly."
          />
          <div className="mt-4">
            <CodeBlock>{`git clone https://github.com/AgroLidar/AgroLidar
make setup
make generate-data && make train && make serve`}</CodeBlock>
          </div>
        </section>
      </div>
    </main>
  );
}
