"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import type { TutorMessage } from "@/lib/tutor";

type MarkdownBlock = { type: "code"; language: string; content: string } | { type: "heading"; level: number; content: string } | { type: "quote"; content: string } | { type: "ul"; items: string[] } | { type: "ol"; items: string[] } | { type: "paragraph"; content: string };

export function parseMarkdown(markdown: string): MarkdownBlock[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  for (let index = 0; index < lines.length;) {
    const line = lines[index];
    if (line.startsWith("```")) {
      const language = line.slice(3).trim(); const code: string[] = []; index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) { code.push(lines[index]); index += 1; }
      blocks.push({ type: "code", language, content: code.join("\n") }); index += 1; continue;
    }
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) { blocks.push({ type: "heading", level: heading[1].length, content: heading[2] }); index += 1; continue; }
    if (/^>\s?/.test(line)) { blocks.push({ type: "quote", content: line.replace(/^>\s?/, "") }); index += 1; continue; }
    if (/^-\s+/.test(line)) {
      const items: string[] = []; while (index < lines.length && /^-\s+/.test(lines[index])) { items.push(lines[index].replace(/^-\s+/, "")); index += 1; }
      blocks.push({ type: "ul", items }); continue;
    }
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = []; while (index < lines.length && /^\d+\.\s+/.test(lines[index])) { items.push(lines[index].replace(/^\d+\.\s+/, "")); index += 1; }
      blocks.push({ type: "ol", items }); continue;
    }
    if (!line.trim()) { index += 1; continue; }
    const paragraph = [line]; index += 1;
    while (index < lines.length && lines[index].trim() && !/^(#{1,3})\s|^```|^>\s?|^-\s+|^\d+\.\s+/.test(lines[index])) { paragraph.push(lines[index]); index += 1; }
    blocks.push({ type: "paragraph", content: paragraph.join("\n") });
  }
  return blocks;
}

function inlineMarkdown(content: string): ReactNode[] {
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\$[^$]+\$|https?:\/\/[^\s]+)/g;
  return content.split(pattern).filter(Boolean).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("*") && part.endsWith("*")) return <em key={index}>{part.slice(1, -1)}</em>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index} className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[.9em] text-sky-200">{part.slice(1, -1)}</code>;
    if (part.startsWith("$") && part.endsWith("$")) return <code key={index} className="font-mono italic text-indigo-200">{part.slice(1, -1)}</code>;
    if (part.startsWith("http")) return <a key={index} href={part} target="_blank" rel="noreferrer" className="text-sky-300 underline decoration-sky-400/40">{part}</a>;
    return part.split("\n").flatMap((line, lineIndex, all) => lineIndex < all.length - 1 ? [line, <br key={`${index}-${lineIndex}`} />] : [line]);
  });
}

function highlightedLine(line: string): ReactNode[] {
  const pattern = /("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#.*$|\/\/.*$|\b(?:def|class|return|if|else|elif|for|while|in|import|from|as|try|except|async|await|const|let|function|true|false|True|False|None)\b|\b\d+(?:\.\d+)?\b)/g;
  return line.split(pattern).filter((part) => part !== "").map((part, index) => {
    const style = /^(#|\/\/)/.test(part) ? "text-slate-500" : /^("|')/.test(part) ? "text-emerald-300" : /^\d/.test(part) ? "text-amber-300" : /^(def|class|return|if|else|elif|for|while|in|import|from|as|try|except|async|await|const|let|function|true|false|True|False|None)$/.test(part) ? "text-purple-300" : "text-slate-200";
    return <span key={index} className={style}>{part}</span>;
  });
}

function CodeBlock({ language, content }: { language: string; content: string }): JSX.Element {
  const [copied, setCopied] = useState(false);
  const copy = async (): Promise<void> => { await navigator.clipboard.writeText(content); setCopied(true); window.setTimeout(() => setCopied(false), 2000); };
  return <div className="my-4 overflow-hidden rounded-xl border border-slate-700 bg-[#1e1e1e]"><div className="flex items-center justify-between border-b border-slate-700 px-4 py-2 text-xs text-slate-400"><span>{language || "code"}</span><button type="button" onClick={() => void copy()} className="font-semibold text-sky-300">{copied ? "Copied!" : "Copy"}</button></div><pre className="overflow-x-auto p-4 text-sm leading-6"><code>{content.split("\n").map((line, index) => <span key={index} className="table-row"><span aria-hidden="true" className="table-cell select-none pr-4 text-right text-slate-600">{index + 1}</span><span className="table-cell whitespace-pre">{highlightedLine(line)}</span></span>)}</code></pre></div>;
}

export function MarkdownContent({ content }: { content: string }): JSX.Element {
  return <div className="space-y-3 leading-7">{parseMarkdown(content).map((block, index) => {
    if (block.type === "code") return <CodeBlock key={index} language={block.language} content={block.content} />;
    if (block.type === "heading") { const className = block.level === 1 ? "text-xl" : block.level === 2 ? "text-lg" : "text-base"; return <h3 key={index} className={`${className} font-bold text-white`}>{inlineMarkdown(block.content)}</h3>; }
    if (block.type === "quote") return <blockquote key={index} className="border-l-2 border-indigo-400 pl-4 italic text-slate-400">{inlineMarkdown(block.content)}</blockquote>;
    if (block.type === "ul") return <ul key={index} className="list-disc space-y-1 pl-5">{block.items.map((item) => <li key={item}>{inlineMarkdown(item)}</li>)}</ul>;
    if (block.type === "ol") return <ol key={index} className="list-decimal space-y-1 pl-5">{block.items.map((item) => <li key={item}>{inlineMarkdown(item)}</li>)}</ol>;
    return <p key={index}>{inlineMarkdown(block.content)}</p>;
  })}</div>;
}

export function MessageBubble({ message, userInitials, isLastAssistant, onRegenerate }: { message: TutorMessage; userInitials: string; isLastAssistant: boolean; onRegenerate: () => void }): JSX.Element {
  const [reaction, setReaction] = useState<"up" | "down" | null>(null);
  const [copied, setCopied] = useState(false);
  const user = message.role === "user";
  const time = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(message.created_at));
  const copy = async (): Promise<void> => { await navigator.clipboard.writeText(message.content); setCopied(true); window.setTimeout(() => setCopied(false), 2000); };
  return <article className={`group flex items-start gap-3 ${user ? "flex-row-reverse" : ""}`}><span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold ${user ? "bg-indigo-500 text-white" : "bg-sky-400/15 text-sky-300"}`}>{user ? userInitials : "AI"}</span><div className={`max-w-[85%] sm:max-w-[78%] ${user ? "text-right" : ""}`}><div className={`rounded-2xl px-4 py-3 text-left text-sm ${user ? "rounded-tr-sm bg-indigo-500 text-white" : "rounded-tl-sm border border-slate-800 bg-slate-900 text-slate-200"}`}>{user ? <p className="whitespace-pre-wrap leading-6">{message.content}</p> : <MarkdownContent content={message.content} />}</div><div className={`mt-1 flex items-center gap-2 text-[11px] text-slate-600 ${user ? "justify-end" : ""}`}><span>{user ? "You" : "AI Tutor"} · {time}</span>{!user && <span className="flex gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100"><button type="button" aria-label="Helpful" onClick={() => setReaction(reaction === "up" ? null : "up")} className={reaction === "up" ? "text-emerald-300" : "hover:text-slate-300"}>👍</button><button type="button" aria-label="Not helpful" onClick={() => setReaction(reaction === "down" ? null : "down")} className={reaction === "down" ? "text-red-300" : "hover:text-slate-300"}>👎</button><button type="button" onClick={() => void copy()} className="hover:text-slate-300">{copied ? "Copied!" : "Copy"}</button>{isLastAssistant && <button type="button" onClick={onRegenerate} className="hover:text-slate-300">↻ Regenerate</button>}</span>}</div></div></article>;
}
