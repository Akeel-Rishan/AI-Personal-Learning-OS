"use client";

import { useEffect, useRef, useState } from "react";

export function useChartSize(minWidth = 280): { ref: React.RefObject<HTMLDivElement>; width: number } {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(minWidth);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(minWidth, entry.contentRect.width)));
    observer.observe(element);
    return () => observer.disconnect();
  }, [minWidth]);
  return { ref, width };
}
