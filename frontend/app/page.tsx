// Public landing page introducing the platform and its workflow.
import Link from "next/link";

const features = [
  {
    title: "Personalized Roadmap",
    description:
      "AI builds your exact learning path based on your goal and existing skills.",
    icon: "01",
  },
  {
    title: "Adaptive Learning",
    description:
      "The system detects weaknesses and adjusts your curriculum in real time.",
    icon: "02",
  },
  {
    title: "AI Tutor",
    description:
      "A context-aware tutor that knows your level and adapts explanations accordingly.",
    icon: "03",
  },
] as const;

const steps = [
  ["Set Your Goal", "Tell us what you want to achieve and why it matters."],
  ["Get Assessed", "Show us what you already know through a focused assessment."],
  ["Follow Your Plan", "Work through a clear curriculum built around your schedule."],
  ["The AI Adapts", "Your path evolves continuously as your skills and needs change."],
] as const;

export default function HomePage(): JSX.Element {
  return (
    <main className="overflow-hidden bg-slate-950 text-slate-100">
      <section className="relative isolate min-h-screen px-6">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,rgba(14,165,233,0.16),transparent_32%),radial-gradient(circle_at_20%_40%,rgba(99,102,241,0.13),transparent_30%),linear-gradient(to_bottom,#020617,#0f172a)]" />
        <nav className="mx-auto flex max-w-6xl items-center justify-between py-7">
          <Link href="/" className="text-lg font-semibold tracking-tight">
            AI Learning OS
          </Link>
          <div className="flex items-center gap-3 text-sm">
            <Link href="/login" className="px-4 py-2 text-slate-300 transition hover:text-white">
              Log in
            </Link>
            <Link href="/signup" className="rounded-full border border-sky-400/40 bg-sky-400/10 px-4 py-2 font-medium text-sky-200 transition hover:bg-sky-400/20">
              Get started
            </Link>
          </div>
        </nav>

        <div className="mx-auto flex max-w-5xl flex-col items-center py-28 text-center sm:py-40">
          <p className="mb-6 rounded-full border border-sky-400/20 bg-sky-400/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-300">
            Your path. Your pace. Your potential.
          </p>
          <h1 className="max-w-4xl text-5xl font-bold tracking-[-0.04em] text-white sm:text-7xl lg:text-8xl">
            Learn Anything. <span className="bg-gradient-to-r from-sky-300 to-indigo-400 bg-clip-text text-transparent">Become Anyone.</span>
          </h1>
          <p className="mt-8 max-w-2xl text-lg leading-8 text-slate-300 sm:text-xl">
            An AI that understands you, builds your curriculum, teaches you, and adapts until you reach your goal.
          </p>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row">
            <Link href="/signup" className="rounded-full bg-sky-400 px-7 py-3.5 font-semibold text-slate-950 shadow-lg shadow-sky-500/20 transition hover:bg-sky-300">
              Start Learning Free
            </Link>
            <a href="#how-it-works" className="rounded-full border border-slate-700 bg-slate-900/60 px-7 py-3.5 font-semibold text-slate-100 transition hover:border-slate-500 hover:bg-slate-800">
              See How It Works
            </a>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-800/80 bg-slate-900/40 px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-sky-400">Built around you</p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-5xl">A learning system that never stops listening.</h2>
          </div>
          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {features.map((feature) => (
              <article key={feature.title} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-7 transition hover:-translate-y-1 hover:border-sky-500/30">
                <span className="text-sm font-bold text-sky-400">{feature.icon}</span>
                <h3 className="mt-8 text-xl font-semibold">{feature.title}</h3>
                <p className="mt-3 leading-7 text-slate-400">{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="px-6 py-24 sm:py-32">
        <div className="mx-auto max-w-6xl">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-400">How it works</p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-5xl">From ambition to ability.</h2>
          </div>
          <ol className="mt-16 grid gap-10 md:grid-cols-4">
            {steps.map(([title, description], index) => (
              <li key={title} className="relative border-l border-slate-700 pl-6">
                <span className="text-sm font-semibold text-indigo-400">Step {index + 1}</span>
                <h3 className="mt-3 text-xl font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <footer className="border-t border-slate-800 px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-medium text-slate-300">AI Personal Learning OS</p>
          <p>&copy; {new Date().getFullYear()} AI Personal Learning OS. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
}

