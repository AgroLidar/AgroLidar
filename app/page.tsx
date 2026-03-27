export default function Page() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <section className="w-full max-w-2xl text-center">
        <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
          Perception for the field.
        </h1>
        <p className="mt-4 text-base text-white/75 sm:text-lg">
          LiDAR-based safety perception for agricultural machines.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <a
            href="#"
            className="rounded-md bg-emerald-400 px-5 py-2.5 text-sm font-semibold text-black transition-colors hover:bg-emerald-300"
          >
            Try the Sandbox
          </a>
          <a
            href="#"
            className="rounded-md border border-white/20 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/10"
          >
            View Docs
          </a>
        </div>
      </section>
    </main>
  );
}
