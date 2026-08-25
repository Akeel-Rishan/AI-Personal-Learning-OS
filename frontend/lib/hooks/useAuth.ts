// Checked hook for consuming the application authentication context.
"use client";

import { useContext } from "react";
import { AuthContext, type AuthContextType } from "@/app/providers";

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}

