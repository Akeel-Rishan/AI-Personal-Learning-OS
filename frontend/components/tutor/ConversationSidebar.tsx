"use client";

import Link from "next/link";
import type { Conversation } from "@/lib/tutor";

function relativeTime(value: string): string {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "Just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 172800) return "Yesterday";
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function ConversationSidebar({ conversations, activeId, creating, onNew, onDelete, onNavigate }: { conversations: Conversation[]; activeId: string; creating: boolean; onNew: () => void; onDelete: (conversation: Conversation) => void; onNavigate?: () => void }): JSX.Element {
  return <aside className="flex h-full flex-col bg-slate-950"><div className="border-b border-slate-800 p-4"><h2 className="text-lg font-bold">AI Tutor</h2><button type="button" disabled={creating} onClick={onNew} className="mt-4 w-full rounded-xl bg-sky-400 px-4 py-3 text-sm font-bold text-slate-950 disabled:opacity-50">{creating ? "Creating..." : "+ New Conversation"}</button></div><div className="min-h-0 flex-1 overflow-y-auto p-3"><p className="px-2 py-2 text-xs font-bold uppercase tracking-wider text-slate-600">Recent</p>{conversations.length === 0 && <p className="px-2 py-6 text-sm leading-6 text-slate-500">No previous conversations yet.</p>}<div className="space-y-1">{conversations.map((conversation) => <div key={conversation.id} className={`group relative rounded-xl border-l-2 ${conversation.id === activeId ? "border-sky-400 bg-sky-400/10" : "border-transparent hover:bg-slate-900"}`}><Link href={`/tutor/${conversation.id}`} onClick={onNavigate} className="block px-3 py-3 pr-10"><p className="truncate text-sm font-semibold text-slate-200">{conversation.title || "Learning conversation"}</p><p className="mt-1 text-[11px] text-slate-500">{relativeTime(conversation.updated_at)} · {conversation.message_count} msgs</p></Link><button type="button" title="Delete conversation" aria-label={`Delete ${conversation.title || "conversation"}`} onClick={() => onDelete(conversation)} className="absolute right-2 top-3 rounded p-1.5 text-slate-600 opacity-0 transition hover:bg-red-500/10 hover:text-red-300 group-hover:opacity-100 focus:opacity-100">⌫</button></div>)}</div></div></aside>;
}
