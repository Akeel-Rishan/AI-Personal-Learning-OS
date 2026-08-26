"use client";

import React, { memo, useMemo, useState } from "react";
import type { GoalSkill, Skill } from "@/lib/goals";

interface SkillGraphProps {
  skills: GoalSkill[];
}

interface PositionedSkill {
  skill: Skill;
  x: number;
  y: number;
  width: number;
  height: number;
  layer: number;
}

const categoryColors: Record<string, string> = {
  programming: "#3B82F6",
  mathematics: "#8B5CF6",
  "data-science": "#10B981",
  ml: "#F59E0B",
  devops: "#6B7280",
};

const categoryLabels: Record<string, string> = {
  programming: "Programming",
  mathematics: "Mathematics",
  "data-science": "Data Science",
  ml: "Machine Learning",
  devops: "DevOps",
};

function graphLayout(goalSkills: GoalSkill[]): { nodes: PositionedSkill[]; edges: Array<[string, string]> } {
  const skills = goalSkills.map((item) => item.skill);
  const selectedIds = new Set(skills.map((skill) => skill.id));
  const prerequisites = new Map(
    skills.map((skill) => [skill.id, (skill.prerequisites ?? []).map((item) => item.id).filter((id) => selectedIds.has(id))]),
  );
  const layers = new Map<string, number>();
  let remaining = [...skills];
  let layer = 0;

  while (remaining.length > 0) {
    const ready = remaining.filter((skill) => (prerequisites.get(skill.id) ?? []).every((id) => layers.has(id)));
    const batch = ready.length > 0 ? ready : remaining;
    batch.forEach((skill) => layers.set(skill.id, layer));
    const batchIds = new Set(batch.map((skill) => skill.id));
    remaining = remaining.filter((skill) => !batchIds.has(skill.id));
    layer += 1;
  }

  const byLayer = new Map<number, Skill[]>();
  skills.forEach((skill) => {
    const value = layers.get(skill.id) ?? 0;
    byLayer.set(value, [...(byLayer.get(value) ?? []), skill]);
  });
  const maxLayer = Math.max(0, ...Array.from(byLayer.keys()));
  const nodes: PositionedSkill[] = [];
  byLayer.forEach((items, currentLayer) => {
    items.sort((left, right) => left.name.localeCompare(right.name));
    const x = maxLayer === 0 ? 450 : 65 + currentLayer * (770 / maxLayer);
    const spacing = 430 / (items.length + 1);
    items.forEach((skill, index) => {
      const width = Math.min(190, 142 + Math.sqrt(skill.estimated_hours ?? 10) * 5);
      nodes.push({ skill, x, y: 25 + spacing * (index + 1), width, height: 58, layer: currentLayer });
    });
  });
  const edges: Array<[string, string]> = [];
  prerequisites.forEach((ids, skillId) => ids.forEach((prerequisiteId) => edges.push([prerequisiteId, skillId])));
  return { nodes, edges };
}

function SkillGraphComponent({ skills }: SkillGraphProps): JSX.Element {
  const { nodes, edges } = useMemo(() => graphLayout(skills), [skills]);
  const nodeMap = useMemo(() => new Map(nodes.map((node) => [node.skill.id, node])), [nodes]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });
  const [drag, setDrag] = useState<{ x: number; y: number; originX: number; originY: number } | null>(null);

  const relatedIds = useMemo(() => {
    if (!selectedId) return new Set<string>();
    const related = new Set([selectedId]);
    edges.forEach(([from, to]) => {
      if (from === selectedId) related.add(to);
      if (to === selectedId) related.add(from);
    });
    return related;
  }, [edges, selectedId]);

  function handleWheel(event: React.WheelEvent<SVGSVGElement>): void {
    event.preventDefault();
    const nextScale = Math.min(2.2, Math.max(0.65, view.scale * (event.deltaY > 0 ? 0.9 : 1.1)));
    setView((current) => ({ ...current, scale: nextScale }));
  }

  return (
    <div>
      <div className="md:hidden">
        <div className="space-y-3">
          {[...skills].sort((left, right) => left.priority_order - right.priority_order).map((item) => (
            <article key={item.skill.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
              <div className="flex items-start gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white" style={{ backgroundColor: categoryColors[item.skill.category] ?? categoryColors.devops }}>{item.priority_order}</span>
                <div><h3 className="font-semibold">{item.skill.name}</h3><p className="mt-1 text-xs text-slate-500">{categoryLabels[item.skill.category] ?? item.skill.category} · {item.skill.estimated_hours ?? 0} hours · Level {item.skill.difficulty_level}</p></div>
              </div>
              {(item.skill.prerequisites?.length ?? 0) > 0 && <p className="mt-3 text-xs leading-5 text-slate-400">Prerequisites: {item.skill.prerequisites?.map((skill) => skill.name).join(", ")}</p>}
            </article>
          ))}
        </div>
      </div>

      <div className="hidden overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/70 md:block">
        <svg
          viewBox="0 0 900 500"
          className="h-[500px] w-full touch-none cursor-grab active:cursor-grabbing"
          role="img"
          aria-label="Interactive skill dependency graph"
          onWheel={handleWheel}
          onPointerDown={(event) => {
            if (event.target !== event.currentTarget) return;
            event.currentTarget.setPointerCapture(event.pointerId);
            setSelectedId(null);
            setDrag({ x: event.clientX, y: event.clientY, originX: view.x, originY: view.y });
          }}
          onPointerMove={(event) => {
            if (!drag) return;
            setView((current) => ({ ...current, x: drag.originX + event.clientX - drag.x, y: drag.originY + event.clientY - drag.y }));
          }}
          onPointerUp={() => setDrag(null)}
          onPointerCancel={() => setDrag(null)}
        >
          <defs>
            <pattern id="skill-grid" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#1e293b" /></pattern>
            <marker id="skill-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" /></marker>
          </defs>
          <rect width="900" height="500" fill="url(#skill-grid)" pointerEvents="none" />
          <g transform={`translate(${view.x} ${view.y}) scale(${view.scale})`}>
            {edges.map(([fromId, toId]) => {
              const from = nodeMap.get(fromId);
              const to = nodeMap.get(toId);
              if (!from || !to) return null;
              const x1 = from.x + from.width / 2;
              const y1 = from.y;
              const x2 = to.x - to.width / 2 - 7;
              const y2 = to.y;
              const middle = (x1 + x2) / 2;
              const highlighted = selectedId === fromId || selectedId === toId;
              return <path key={`${fromId}-${toId}`} d={`M ${x1} ${y1} C ${middle} ${y1}, ${middle} ${y2}, ${x2} ${y2}`} fill="none" stroke={highlighted ? "#38bdf8" : "#475569"} strokeWidth={highlighted ? 2.5 : 1.5} opacity={selectedId && !highlighted ? 0.15 : 0.8} markerEnd="url(#skill-arrow)" />;
            })}

            {nodes.map((node) => {
              const color = categoryColors[node.skill.category] ?? categoryColors.devops;
              const dimmed = selectedId !== null && !relatedIds.has(node.skill.id);
              const selected = selectedId === node.skill.id;
              return (
                <g
                  key={node.skill.id}
                  transform={`translate(${node.x - node.width / 2} ${node.y - node.height / 2})`}
                  opacity={dimmed ? 0.2 : 1}
                  className="cursor-pointer transition-opacity"
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={(event) => { event.stopPropagation(); setSelectedId((current) => current === node.skill.id ? null : node.skill.id); }}
                  onMouseEnter={() => setHoveredId(node.skill.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  <rect width={node.width} height={node.height} rx="12" fill="#0f172a" stroke={selected ? "#f8fafc" : color} strokeWidth={selected ? 3 : 2} />
                  <rect width="7" height={node.height} rx="4" fill={color} />
                  <text x="18" y="25" fill="#f8fafc" fontSize="13" fontWeight="600">{node.skill.name.length > 22 ? `${node.skill.name.slice(0, 21)}…` : node.skill.name}</text>
                  <text x="18" y="43" fill="#94a3b8" fontSize="10">{node.skill.estimated_hours ?? 0}h · Level {node.skill.difficulty_level}</text>
                  {hoveredId === node.skill.id && (
                    <g transform={`translate(${Math.max(0, node.width / 2 - 105)} -76)`} pointerEvents="none">
                      <rect width="210" height="66" rx="9" fill="#020617" stroke="#334155" />
                      <text x="12" y="20" fill="#f8fafc" fontSize="11" fontWeight="600">{node.skill.name}</text>
                      <text x="12" y="38" fill={color} fontSize="10">{categoryLabels[node.skill.category] ?? node.skill.category}</text>
                      <text x="12" y="54" fill="#94a3b8" fontSize="10">{node.skill.estimated_hours ?? 0} hours · Difficulty {node.skill.difficulty_level}/4</text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      <div className="mt-4 hidden flex-wrap items-center justify-between gap-4 md:flex">
        <div className="flex flex-wrap gap-4">
          {Object.entries(categoryColors).map(([category, color]) => <span key={category} className="flex items-center gap-2 text-xs text-slate-400"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{categoryLabels[category]}</span>)}
        </div>
        <p className="text-xs text-slate-500">Click a skill to see its dependencies · Scroll to zoom · Drag to pan</p>
      </div>
    </div>
  );
}

export const SkillGraph = memo(SkillGraphComponent);
