"use client";

import { useMemo, useRef, useState } from "react";

function escapeHtml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function tokenName(index: number): string {
  let value = index + 1; let name = "";
  while (value > 0) { value -= 1; name = String.fromCharCode(65 + value % 26) + name; value = Math.floor(value / 26); }
  return `\uE000${name}\uE001`;
}

export function highlightPython(code: string): string {
  const tokens: string[] = [];
  const protect = (html: string): string => { const token = tokenName(tokens.length); tokens.push(html); return token; };
  let output = code.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, (match) => protect(`<span class="text-emerald-300">${escapeHtml(match)}</span>`));
  output = output.replace(/#.*$/gm, (match) => protect(`<span class="italic text-slate-500">${escapeHtml(match)}</span>`));
  output = escapeHtml(output);
  output = output.replace(/\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|finally|with|lambda|yield|async|await|in|is|not|and|or|pass|break|continue|True|False|None)\b/g, '<span class="text-sky-300">$1</span>');
  output = output.replace(/\b(print|len|range|enumerate|zip|map|filter|sum|min|max|list|dict|set|tuple|str|int|float|bool|open|super)\b/g, '<span class="text-purple-300">$1</span>');
  output = output.replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="text-orange-300">$1</span>');
  tokens.forEach((html, index) => { output = output.replaceAll(escapeHtml(tokenName(index)), html); });
  return output;
}

export function CodeEditor({ value, onChange, starterCode, disabled = false, minHeight = 320 }: { value: string; onChange: (value: string) => void; starterCode?: string | null; disabled?: boolean; minHeight?: number }): JSX.Element {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const preRef = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);
  const [currentLine, setCurrentLine] = useState(1);
  const [scrollTop, setScrollTop] = useState(0);
  const lines = Math.max(1, value.split("\n").length);
  const highlighted = useMemo(() => highlightPython(value) + (value.endsWith("\n") ? " " : ""), [value]);
  const updateLine = (): void => { const input = textareaRef.current; if (input) setCurrentLine(value.slice(0, input.selectionStart).split("\n").length); };
  const keyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (event.key === "Tab") {
      event.preventDefault(); const input = event.currentTarget; const start = input.selectionStart; const end = input.selectionEnd;
      onChange(`${value.slice(0, start)}    ${value.slice(end)}`); window.requestAnimationFrame(() => { input.selectionStart = input.selectionEnd = start + 4; });
    } else if (event.key === "Enter") {
      const input = event.currentTarget; const before = value.slice(0, input.selectionStart); const line = before.split("\n").at(-1) ?? "";
      const indentation = /^\s*/.exec(line)?.[0] ?? ""; const extra = line.trimEnd().endsWith(":") ? "    " : "";
      if (indentation || extra) { event.preventDefault(); const insertion = `\n${indentation}${extra}`; const start = input.selectionStart; onChange(`${value.slice(0, start)}${insertion}${value.slice(input.selectionEnd)}`); window.requestAnimationFrame(() => { input.selectionStart = input.selectionEnd = start + insertion.length; }); }
    }
  };
  const copy = async (): Promise<void> => { await navigator.clipboard.writeText(value); setCopied(true); window.setTimeout(() => setCopied(false), 2000); };
  return <div className="overflow-hidden rounded-xl border border-slate-700 bg-[#1e1e1e]"><div className="flex items-center justify-between border-b border-slate-700 px-4 py-2 text-xs"><span className="font-semibold text-slate-500">Python</span><div className="flex gap-3"><button type="button" onClick={() => void copy()} className="text-sky-300">{copied ? "Copied!" : "Copy all"}</button>{starterCode != null && <button type="button" disabled={disabled || value === starterCode} onClick={() => onChange(starterCode)} className="text-slate-400 disabled:opacity-40">Reset</button>}</div></div><div className="relative overflow-hidden" style={{ minHeight }}><div aria-hidden="true" className="pointer-events-none absolute inset-x-0 h-7 bg-white/[.035]" style={{ top: 16 + (currentLine - 1) * 28 - scrollTop }} /><div aria-hidden="true" className="pointer-events-none absolute left-0 top-0 z-10 w-12 select-none border-r border-slate-700/60 bg-[#1e1e1e] py-4 text-right font-mono text-sm leading-7 text-slate-600">{Array.from({ length: lines }, (_, index) => <div key={index} className="pr-3">{index + 1}</div>)}</div><pre ref={preRef} aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-auto whitespace-pre p-4 pl-14 font-mono text-sm leading-7 text-[#d4d4d4]" dangerouslySetInnerHTML={{ __html: highlighted }} /><textarea ref={textareaRef} value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} onKeyDown={keyDown} onClick={updateLine} onKeyUp={updateLine} onScroll={(event) => { const target = event.currentTarget; if (preRef.current) { preRef.current.scrollTop = target.scrollTop; preRef.current.scrollLeft = target.scrollLeft; } setScrollTop(target.scrollTop); }} spellCheck={false} aria-label="Python code editor" className="absolute inset-0 h-full w-full resize-none overflow-auto whitespace-pre bg-transparent p-4 pl-14 font-mono text-sm leading-7 text-transparent caret-white outline-none selection:bg-sky-400/30 disabled:cursor-not-allowed" /></div></div>;
}
