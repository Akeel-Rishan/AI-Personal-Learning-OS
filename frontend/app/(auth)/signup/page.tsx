// Placeholder signup screen; account creation behavior will be added later.
import Link from "next/link";

export default function SignupPage(): JSX.Element {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 text-slate-100">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl shadow-black/20">
        <Link href="/" className="text-sm font-medium text-sky-400">&larr; AI Learning OS</Link>
        <h1 className="mt-8 text-3xl font-bold tracking-tight">Create Account</h1>
        <p className="mt-2 text-slate-400">Start a learning path designed around you.</p>
        <form className="mt-8 space-y-5">
          <label className="block text-sm font-medium">
            Name
            <input type="text" name="name" autoComplete="name" placeholder="Your name" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition placeholder:text-slate-600 focus:border-sky-400" />
          </label>
          <label className="block text-sm font-medium">
            Email
            <input type="email" name="email" autoComplete="email" placeholder="you@example.com" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition placeholder:text-slate-600 focus:border-sky-400" />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input type="password" name="password" autoComplete="new-password" placeholder="Create a password" className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition placeholder:text-slate-600 focus:border-sky-400" />
          </label>
          <button type="submit" className="w-full rounded-lg bg-sky-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-300">Create Account</button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-400">
          Already have an account? <Link href="/login" className="font-medium text-sky-400 hover:text-sky-300">Log in</Link>
        </p>
      </div>
    </main>
  );
}

