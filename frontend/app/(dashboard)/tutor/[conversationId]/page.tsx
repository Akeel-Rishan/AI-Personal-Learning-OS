"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChatInput } from "@/components/tutor/ChatInput";
import { ChatWindow } from "@/components/tutor/ChatWindow";
import { ContextPanel } from "@/components/tutor/ContextPanel";
import { ConversationSidebar } from "@/components/tutor/ConversationSidebar";
import { TutorLayout } from "@/components/tutor/TutorLayout";
import { ApiError, apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import type { Conversation, ConversationDetail, ExplanationStyle, LearnerContext, SendMessageResponse, SuggestedPromptsResponse, TutorMessage } from "@/lib/tutor";

export default function TutorConversationPage(): JSX.Element {
  const params = useParams<{ conversationId: string }>();
  const conversationId = params.conversationId;
  const router = useRouter();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [context, setContext] = useState<LearnerContext | null>(null);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [socratic, setSocratic] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [creating, setCreating] = useState(false);
  const [promptsLoading, setPromptsLoading] = useState(false);
  const [savingStyle, setSavingStyle] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const loadSuggestions = useCallback(async (refresh = false): Promise<void> => {
    setPromptsLoading(true);
    try {
      const result = await apiGet<SuggestedPromptsResponse>(`/api/v1/tutor/suggested-prompts?conversation_id=${conversationId}${refresh ? "&refresh=true" : ""}`);
      setPrompts(result.prompts);
    } catch (reason) { setToast(reason instanceof ApiError ? reason.message : "Suggestions could not be loaded."); }
    finally { setPromptsLoading(false); }
  }, [conversationId]);

  useEffect(() => {
    let active = true; setLoading(true); setInput(""); setToast(null);
    Promise.all([
      apiGet<ConversationDetail>(`/api/v1/tutor/conversations/${conversationId}`),
      apiGet<Conversation[]>("/api/v1/tutor/conversations"),
      apiGet<LearnerContext>("/api/v1/tutor/context"),
    ]).then(([detail, list, learner]) => { if (active) { setConversation(detail); setConversations(list); setContext(learner); } })
      .catch((reason: unknown) => { if (active) { if (reason instanceof ApiError && reason.status === 404) router.replace("/tutor"); else setToast(reason instanceof ApiError ? reason.message : "The conversation could not be loaded."); } })
      .finally(() => { if (active) setLoading(false); });
    void loadSuggestions();
    return () => { active = false; };
  }, [conversationId, loadSuggestions, router]);

  const refreshLists = async (): Promise<void> => {
    const [detail, list] = await Promise.all([apiGet<ConversationDetail>(`/api/v1/tutor/conversations/${conversationId}`), apiGet<Conversation[]>("/api/v1/tutor/conversations")]);
    setConversation(detail); setConversations(list);
  };

  const send = async (override?: string, regenerating = false): Promise<void> => {
    const content = (override ?? input).trim();
    if (!content || sending || !conversation) return;
    const prior = conversation.messages;
    const base = regenerating && prior.at(-1)?.role === "assistant" ? prior.slice(0, -1) : prior;
    const optimistic: TutorMessage = { id: `temp-${Date.now()}`, role: "user", content, metadata: { socratic_mode: socratic }, created_at: new Date().toISOString() };
    setConversation({ ...conversation, messages: regenerating ? base : [...base, optimistic] });
    if (!regenerating) setInput("");
    setSending(true); setToast(null);
    try {
      const response = await apiPost<SendMessageResponse>(`/api/v1/tutor/conversations/${conversationId}/messages`, { content, socratic_mode: socratic, skill_focus: selectedSkill || null, regenerate: regenerating });
      const now = new Date().toISOString();
      const userMessage = { ...optimistic, id: response.user_message_id };
      const assistant: TutorMessage = { id: response.assistant_message_id, role: "assistant", content: response.content, metadata: response.metadata, created_at: now };
      setConversation((current) => current ? { ...current, messages: regenerating ? [...base, assistant] : [...base, userMessage, assistant], message_count: current.message_count + (regenerating ? 0 : 2) } : current);
      await refreshLists();
    } catch (reason) {
      setConversation((current) => current ? { ...current, messages: prior } : current);
      if (!regenerating) setInput(content);
      setToast(reason instanceof ApiError ? reason.message : "Tutor is temporarily unavailable. Your message was restored.");
    } finally { setSending(false); }
  };

  const newConversation = async (): Promise<void> => {
    setCreating(true);
    try { const created = await apiPost<ConversationDetail>("/api/v1/tutor/conversations", selectedSkill ? { skill_id: context?.goal_skills.find((skill) => skill.name === selectedSkill)?.id } : {}); router.push(`/tutor/${created.id}`); }
    catch (reason) { setToast(reason instanceof ApiError ? reason.message : "A new conversation could not be created."); setCreating(false); }
  };

  const deleteConversation = async (target: Conversation): Promise<void> => {
    if (!window.confirm(`Delete “${target.title || "this conversation"}”? This cannot be undone.`)) return;
    const previous = conversations; const remaining = previous.filter((item) => item.id !== target.id); setConversations(remaining);
    try { await apiDelete<{ deleted: boolean }>(`/api/v1/tutor/conversations/${target.id}`); if (target.id === conversationId) router.replace(remaining[0] ? `/tutor/${remaining[0].id}` : "/tutor"); }
    catch (reason) { setConversations(previous); setToast(reason instanceof ApiError ? reason.message : "The conversation could not be deleted."); }
  };

  const changeStyle = async (style: ExplanationStyle): Promise<void> => {
    if (!context) return; const previous = context.preferred_style; setContext({ ...context, preferred_style: style }); setSavingStyle(true);
    try { await apiPut("/api/v1/users/profile", { preferred_explanation_style: style }); }
    catch (reason) { setContext({ ...context, preferred_style: previous }); setToast(reason instanceof ApiError ? reason.message : "Explanation style could not be updated."); }
    finally { setSavingStyle(false); }
  };

  const regenerate = (): void => {
    if (!conversation || sending) return;
    const lastAssistantIndex = [...conversation.messages].map((item) => item.role).lastIndexOf("assistant");
    const userMessage = conversation.messages.slice(0, lastAssistantIndex).reverse().find((item) => item.role === "user");
    if (userMessage) void send(userMessage.content, true);
  };

  if (loading || !conversation || !context) return <div className="flex min-h-[65vh] items-center justify-center"><span className="h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-sky-400" /></div>;
  const sidebar = <ConversationSidebar conversations={conversations} activeId={conversationId} creating={creating} onNew={() => void newConversation()} onDelete={(item) => void deleteConversation(item)} />;
  const contextPanel = <ContextPanel context={context} savingStyle={savingStyle} onStyleChange={(style) => void changeStyle(style)} />;
  return <><TutorLayout title={conversation.title || "Learning conversation"} sidebar={sidebar} contextPanel={contextPanel}><ChatWindow messages={conversation.messages} context={context} loading={sending} prompts={prompts} promptsLoading={promptsLoading} onSelectPrompt={setInput} onRefreshPrompts={() => void loadSuggestions(true)} onRegenerate={regenerate} /><ChatInput value={input} loading={sending} socratic={socratic} selectedSkill={selectedSkill} skills={context.goal_skills} onChange={setInput} onSend={() => void send()} onToggleSocratic={() => setSocratic((value) => !value)} onSkillChange={setSelectedSkill} /></TutorLayout>{toast && <div role="status" className="fixed bottom-5 right-5 z-[80] max-w-sm rounded-xl border border-slate-700 bg-slate-900 px-5 py-3 text-sm text-slate-200 shadow-2xl">{toast}<button type="button" onClick={() => setToast(null)} className="ml-3 text-slate-500">×</button></div>}</>;
}
