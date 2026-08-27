"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MessageBubble } from "@/components/tutor/MessageBubble";
import { SuggestedPrompts } from "@/components/tutor/SuggestedPrompts";
import { TypingIndicator } from "@/components/tutor/TypingIndicator";
import type { LearnerContext, TutorMessage } from "@/lib/tutor";

function dayLabel(value: string): string {
  const date = new Date(value); const today = new Date();
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  if (date.toDateString() === today.toDateString()) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date);
}

export function ChatWindow({ messages, context, loading, prompts, promptsLoading, onSelectPrompt, onRefreshPrompts, onRegenerate }: { messages: TutorMessage[]; context: LearnerContext; loading: boolean; prompts: string[]; promptsLoading: boolean; onSelectPrompt: (prompt: string) => void; onRefreshPrompts: () => void; onRegenerate: () => void }): JSX.Element {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const previousCount = useRef(messages.length);
  const [showNewMessage, setShowNewMessage] = useState(false);
  const initials = context.user_name.slice(0, 2).toUpperCase();
  const lastAssistantId = useMemo(() => [...messages].reverse().find((item) => item.role === "assistant")?.id, [messages]);
  useEffect(() => {
    const added = messages.length > previousCount.current || loading;
    if (added && nearBottom.current) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    else if (added) setShowNewMessage(true);
    previousCount.current = messages.length;
  }, [messages.length, loading]);
  const scrollToBottom = (): void => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); setShowNewMessage(false); };
  return <div className="relative min-h-0 flex-1"><div ref={scrollRef} onScroll={(event) => { const element = event.currentTarget; nearBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 100; if (nearBottom.current) setShowNewMessage(false); }} className="absolute inset-0 overflow-y-auto px-4 py-6 sm:px-6"><div className="mx-auto max-w-4xl">{messages.length === 0 && !loading ? <div className="flex min-h-[55vh] flex-col items-center justify-center text-center"><span className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400/20 to-indigo-400/20 text-2xl font-black text-sky-300">AI</span><h1 className="mt-6 text-3xl font-black">Hi {context.user_name}! I&apos;m your AI tutor.</h1><p className="mt-3 max-w-xl leading-7 text-slate-400">I know you&apos;re working toward {context.goal_title}. I&apos;m here to help with anything you&apos;re learning.</p><div className="mt-8 w-full"><SuggestedPrompts prompts={prompts} loading={promptsLoading} onSelect={onSelectPrompt} onRefresh={onRefreshPrompts} /></div></div> : <div className="space-y-6">{messages.map((message, index) => { const previous = messages[index - 1]; const separator = !previous || new Date(previous.created_at).toDateString() !== new Date(message.created_at).toDateString(); return <div key={message.id}>{separator && <div className="my-6 flex items-center gap-3"><span className="h-px flex-1 bg-slate-800" /><span className="text-[11px] font-bold uppercase tracking-wider text-slate-600">{dayLabel(message.created_at)}</span><span className="h-px flex-1 bg-slate-800" /></div>}<MessageBubble message={message} userInitials={initials} isLastAssistant={message.id === lastAssistantId} onRegenerate={onRegenerate} /></div>; })}{loading && <TypingIndicator />}</div>}<div ref={bottomRef} /></div></div>{showNewMessage && <button type="button" onClick={scrollToBottom} className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full border border-sky-400/30 bg-slate-900 px-4 py-2 text-xs font-bold text-sky-300 shadow-xl">↓ New message</button>}</div>;
}
