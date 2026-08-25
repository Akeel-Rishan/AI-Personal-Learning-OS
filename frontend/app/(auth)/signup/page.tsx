// Functional registration page with validation and live password strength.
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/hooks/useAuth";

interface SignupErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const strengthLabels = ["Weak", "Weak", "Fair", "Good", "Strong"] as const;
const strengthColors = ["bg-slate-700", "bg-red-500", "bg-amber-400", "bg-sky-400", "bg-emerald-400"] as const;

export default function SignupPage(): JSX.Element {
  const router = useRouter();
  const { register, isAuthenticated, isLoading } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<SignupErrors>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const passwordStrength = useMemo(() => [
    password.length >= 8,
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ].filter(Boolean).length, [password]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!banner) return;
    const timeout = window.setTimeout(() => setBanner(null), 4000);
    return () => window.clearTimeout(timeout);
  }, [banner]);

  function validate(): SignupErrors {
    const nextErrors: SignupErrors = {};
    if (fullName.trim().length < 2) nextErrors.fullName = "Enter at least 2 characters.";
    if (!email.trim()) nextErrors.email = "Email is required.";
    else if (!emailPattern.test(email)) nextErrors.email = "Enter a valid email address.";
    if (password.length < 8) nextErrors.password = "Use at least 8 characters.";
    else if (!/[A-Z]/.test(password)) nextErrors.password = "Add at least one uppercase letter.";
    else if (!/\d/.test(password)) nextErrors.password = "Add at least one number.";
    if (!confirmPassword) nextErrors.confirmPassword = "Confirm your password.";
    else if (confirmPassword !== password) nextErrors.confirmPassword = "Passwords do not match.";
    if (!acceptedTerms) nextErrors.terms = "You must accept the terms to continue.";
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
      await register(fullName.trim(), email.trim().toLowerCase(), password);
      router.replace("/dashboard");
    } catch (error: unknown) {
      setBanner(error instanceof ApiError ? error.message : "We could not create your account. Please try again.");
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
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-sky-400">Start your transformation</p>
          <h2 className="mt-5 text-5xl font-bold leading-tight tracking-tight">A learning system designed around you</h2>
          <ul className="mt-10 space-y-5 text-slate-300">
            {["Define the future you want", "Discover exactly what to learn", "Adapt your plan with every session"].map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-sky-400/10 text-sky-300">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-sm text-slate-500">Your first personalized roadmap starts here.</p>
      </section>

      <section className="flex items-center justify-center px-6 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <Link href="/" className="mb-8 inline-block text-sm font-semibold text-sky-400 lg:hidden">AI Learning OS</Link>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-7 shadow-2xl shadow-black/20 sm:p-9">
            <h1 className="text-3xl font-bold tracking-tight">Create your account</h1>
            <p className="mt-2 text-slate-400">Build a learning journey that evolves with you</p>

            {banner && <div role="alert" className="mt-5 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">{banner}</div>}

            <form className="mt-7 space-y-4" onSubmit={handleSubmit} noValidate>
              <div>
                <label htmlFor="fullName" className="text-sm font-medium">Full name</label>
                <input id="fullName" value={fullName} disabled={isSubmitting} onChange={(event) => setFullName(event.target.value)} autoComplete="name" placeholder="Your name" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-sky-400 disabled:opacity-60" />
                {errors.fullName && <p className="mt-1.5 text-sm text-red-400">{errors.fullName}</p>}
              </div>

              <div>
                <label htmlFor="email" className="text-sm font-medium">Email address</label>
                <input id="email" type="email" value={email} disabled={isSubmitting} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="you@example.com" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-sky-400 disabled:opacity-60" />
                {errors.email && <p className="mt-1.5 text-sm text-red-400">{errors.email}</p>}
              </div>

              <div>
                <label htmlFor="password" className="text-sm font-medium">Password</label>
                <div className="relative mt-2">
                  <input id="password" type={showPassword ? "text" : "password"} value={password} disabled={isSubmitting} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" placeholder="Create a strong password" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 pr-16 outline-none focus:border-sky-400 disabled:opacity-60" />
                  <button type="button" onClick={() => setShowPassword((current) => !current)} className="absolute inset-y-0 right-3 text-xs font-semibold text-slate-400 hover:text-white">{showPassword ? "Hide" : "Show"}</button>
                </div>
                <div className="mt-2.5 flex gap-1.5" aria-label={`Password strength: ${strengthLabels[passwordStrength]}`}>
                  {[0, 1, 2, 3].map((index) => (
                    <span key={index} className={`h-1.5 flex-1 rounded-full ${index < passwordStrength ? strengthColors[passwordStrength] : "bg-slate-700"}`} />
                  ))}
                </div>
                <p className="mt-1.5 text-xs text-slate-400">{strengthLabels[passwordStrength]} · Use 8+ characters, uppercase, a number, and a symbol.</p>
                {errors.password && <p className="mt-1.5 text-sm text-red-400">{errors.password}</p>}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="text-sm font-medium">Confirm password</label>
                <input id="confirmPassword" type="password" value={confirmPassword} disabled={isSubmitting} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" placeholder="Repeat your password" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-sky-400 disabled:opacity-60" />
                {errors.confirmPassword && <p className="mt-1.5 text-sm text-red-400">{errors.confirmPassword}</p>}
              </div>

              <div>
                <label className="flex items-start gap-3 text-sm text-slate-400">
                  <input type="checkbox" checked={acceptedTerms} disabled={isSubmitting} onChange={(event) => setAcceptedTerms(event.target.checked)} className="mt-1 h-4 w-4 rounded border-slate-600 bg-slate-950 accent-sky-400" />
                  <span>I agree to the <button type="button" className="text-sky-400">Terms of Service</button> and <button type="button" className="text-sky-400">Privacy Policy</button>.</span>
                </label>
                {errors.terms && <p className="mt-1.5 text-sm text-red-400">{errors.terms}</p>}
              </div>

              <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-lg bg-sky-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60">
                {isSubmitting && <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />}
                {isSubmitting ? "Creating account..." : "Create Account"}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-400">Already have an account? <Link href="/login" className="font-semibold text-sky-400 hover:text-sky-300">Sign in</Link></p>
          </div>
        </div>
      </section>
    </main>
  );
}

