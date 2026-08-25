// Functional login page with validation, feedback, and session redirect behavior.
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/hooks/useAuth";

interface LoginErrors {
  email?: string;
  password?: string;
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage(): JSX.Element {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<LoginErrors>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!banner) return;
    const timeout = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(timeout);
  }, [banner]);

  function validate(): LoginErrors {
    const nextErrors: LoginErrors = {};
    if (!email.trim()) nextErrors.email = "Email is required.";
    else if (!emailPattern.test(email)) nextErrors.email = "Enter a valid email address.";
    if (!password) nextErrors.password = "Password is required.";
    else if (password.length < 8) nextErrors.password = "Password must be at least 8 characters.";
    return nextErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBanner(null);
    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      await login(email.trim().toLowerCase(), password);
      router.replace("/dashboard");
    } catch (error: unknown) {
      setBanner(
        error instanceof ApiError && error.status === 0
          ? error.message
          : "Invalid email or password.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-slate-950 text-slate-100 lg:grid-cols-2">
      <section className="relative hidden overflow-hidden border-r border-slate-800 p-12 lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.18),transparent_35%),radial-gradient(circle_at_80%_80%,rgba(99,102,241,0.16),transparent_35%)]" />
        <Link href="/" className="relative text-xl font-bold tracking-tight">AI Learning OS</Link>
        <div className="relative max-w-lg">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-400">Built for your potential</p>
          <h2 className="mt-5 text-5xl font-bold leading-tight tracking-tight">Your AI-powered path to mastery</h2>
          <ul className="mt-10 space-y-5 text-slate-300">
            {["A roadmap shaped around your goal", "Lessons that adapt as you improve", "A tutor that understands your context"].map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sky-400/10 text-sky-300">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-slate-500">Learn with direction. Grow with confidence.</p>
      </section>

      <section className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <Link href="/" className="mb-10 inline-block text-sm font-semibold text-sky-400 lg:hidden">AI Learning OS</Link>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-7 shadow-2xl shadow-black/20 sm:p-9">
            <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
            <p className="mt-2 text-slate-400">Continue your learning journey</p>

            {banner && (
              <div role="alert" className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                {banner}
              </div>
            )}

            <form className="mt-8 space-y-5" onSubmit={handleSubmit} noValidate>
              <div>
                <label htmlFor="email" className="text-sm font-medium">Email address</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  disabled={isSubmitting}
                  onChange={(event) => setEmail(event.target.value)}
                  className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition placeholder:text-slate-600 focus:border-sky-400 disabled:opacity-60"
                  placeholder="you@example.com"
                  aria-describedby={errors.email ? "email-error" : undefined}
                />
                {errors.email && <p id="email-error" className="mt-1.5 text-sm text-red-400">{errors.email}</p>}
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="text-sm font-medium">Password</label>
                  <button type="button" className="text-xs text-sky-400 hover:text-sky-300">Forgot password?</button>
                </div>
                <div className="relative mt-2">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    disabled={isSubmitting}
                    onChange={(event) => setPassword(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 pr-16 outline-none transition placeholder:text-slate-600 focus:border-sky-400 disabled:opacity-60"
                    placeholder="Enter your password"
                    aria-describedby={errors.password ? "password-error" : undefined}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="absolute inset-y-0 right-3 text-xs font-semibold text-slate-400 hover:text-white"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
                {errors.password && <p id="password-error" className="mt-1.5 text-sm text-red-400">{errors.password}</p>}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-sky-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting && <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />}
                {isSubmitting ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="my-7 flex items-center gap-4 text-xs uppercase tracking-wider text-slate-600">
              <span className="h-px flex-1 bg-slate-800" /> Secure access <span className="h-px flex-1 bg-slate-800" />
            </div>
            <p className="text-center text-sm text-slate-400">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="font-semibold text-sky-400 hover:text-sky-300">Create one</Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

