// Authenticated dashboard placeholder personalized with the current learner.
"use client";

import { useAuth } from "@/lib/hooks/useAuth";

function greetingForHour(hour: number): string {
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
}

export default function DashboardPage(): JSX.Element {
  const { user } = useAuth();
  const firstName = user?.full_name.trim().split(/\s+/)[0] || "Learner";
  const greeting = greetingForHour(new Date().getHours());

  return (
    <div className="mx-auto max-w-7xl">
      <div>
        <p className="text-sm font-medium text-sky-400">Your learning command center</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Good {greeting}, {firstName}!</h1>
        <p className="mt-2 text-slate-400">Here&apos;s where your personalized journey will come together.</p>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm text-slate-400">Current Goal</p><p className="mt-3 text-2xl font-semibold">Not set yet</p><button type="button" className="mt-5 text-sm font-semibold text-sky-400">Set Goal →</button>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm text-slate-400">Today&apos;s Tasks</p><p className="mt-3 text-2xl font-semibold">0 tasks</p><button type="button" className="mt-5 text-sm font-semibold text-sky-400">View Plan →</button>
        </article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-sm text-slate-400">Learning Streak</p><p className="mt-3 text-2xl font-semibold">0 days <span aria-label="fire">🔥</span></p><p className="mt-5 text-sm text-slate-500">Your first session starts the streak.</p>
        </article>
      </section>

      <section className="mt-6 rounded-2xl border border-sky-400/20 bg-gradient-to-br from-sky-400/10 via-slate-900/60 to-indigo-500/10 p-8 text-center sm:p-12">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-400/10 text-sky-300">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className="h-8 w-8"><path d="m2 9 10-5 10 5-10 5Z" /><path d="M6 11v5c3 3 9 3 12 0v-5M22 9v6" /></svg>
        </div>
        <h2 className="mt-5 text-2xl font-bold">Let&apos;s set up your learning journey</h2>
        <p className="mx-auto mt-3 max-w-xl leading-7 text-slate-400">Start by telling us what you want to achieve. We&apos;ll build a personalized roadmap just for you.</p>
        <button type="button" className="mt-7 rounded-full bg-sky-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-sky-300">Set My Learning Goal →</button>
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><h2 className="font-semibold">Your Skills</h2><p className="mt-6 text-sm text-slate-500">No skills assessed yet</p></article>
        <article className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"><h2 className="font-semibold">Recent Activity</h2><p className="mt-6 text-sm text-slate-500">No activity yet</p></article>
      </section>
    </div>
  );
}

