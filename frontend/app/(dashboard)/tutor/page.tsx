"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import type { Conversation, ConversationDetail } from "@/lib/tutor";

export default function TutorRedirectPage(): JSX.Element {
  const router = useRouter();
  const started = useRef(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    apiGet<Conversation[]>("/api/v1/tutor/conversations")
      .then(async (items) => items[0] ?? apiPost<ConversationDetail>("/api/v1/tutor/conversations", {}))
      .then((conversation) => router.replace(`/tutor/${conversation.id}`))
      .catch(() => setError("The tutor workspace could not be opened. Confirm the backend is running and try again."));
  }, [router]);
  return <div className="flex min-h-[65vh] items-center justify-center"><div className="text-center"><span className="mx-auto block h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /><p className="mt-4 text-slate-400">Opening your tutor...</p>{error && <p className="mt-4 max-w-md rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-200">{error}</p>}</div></div>;
}
