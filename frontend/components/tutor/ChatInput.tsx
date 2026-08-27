"use client";

import { useEffect, useRef } from "react";
import type { GoalSkillOption } from "@/lib/tutor";

export function ChatInput({ value, loading, socratic, selectedSkill, skills, onChange, onSend, onToggleSocratic, onSkillChange }: { value: string; loading: boolean; socratic: boolean; selectedSkill: string; skills: GoalSkillOption[]; onChange: (value: string) => void; onSend: () => void; onToggleSocratic: () => void; onSkillChange: (value: string) => void }): JSX.Element {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { if (!loading) inputRef.current?.focus(); }, [loading]);
  useEffect(() => {
    const handler = (event: KeyboardEvent): void => {
      if (event.ctrlKey && event.key === "/") { event.preventDefault(); onToggleSocratic(); }
    };
    window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler);
  }, [onToggleSocratic]);
  const resize = (): void => {
    const input = inputRef.current;
    if (!input) return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 144)}px`;
  };
  useEffect(resize, [value]);
  return <div className="border-t border-slate-800 bg-slate-950/95 p-3 sm:p-4"><div className="mx-auto max-w-4xl rounded-2xl border border-slate-700 bg-slate-900 shadow-xl shadow-slate-950/30"><div className="flex flex-wrap gap-2 border-b border-slate-800 px-3 py-2"><button type="button" title="In Socratic mode, the tutor guides you to answers instead of giving them directly" onClick={onToggleSocratic} className={`rounded-full px-3 py-1.5 text-xs font-bold transition ${socratic ? "bg-sky-400/15 text-sky-300 ring-1 ring-sky-400/30" : "bg-slate-800 text-slate-400"}`}>Socratic Mode: {socratic ? "ON 🧠" : "OFF"}</button><select aria-label="Focus skill" value={selectedSkill} onChange={(event) => onSkillChange(event.target.value)} className="max-w-[220px] rounded-full border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300"><option value="">📎 Skill: –</option>{skills.map((skill) => <option key={skill.id} value={skill.name}>📎 Skill: {skill.name}</option>)}</select></div><textarea ref={inputRef} rows={1} maxLength={4000} disabled={loading} value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); onSend(); } }} placeholder="Ask me anything about your learning..." className="block max-h-36 min-h-12 w-full resize-none bg-transparent px-4 py-3 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-600 disabled:opacity-60" /><div className="flex items-center justify-between px-4 pb-3"><span className={`text-xs ${value.length > 3500 ? "text-red-300" : "text-slate-600"}`}>{value.length > 200 ? `${value.length}/4000` : "Enter to send · Shift+Enter for a new line"}</span><button type="button" disabled={loading || !value.trim()} onClick={onSend} className="rounded-lg bg-sky-400 px-4 py-2 text-sm font-bold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40">Send →</button></div></div></div>;
}
