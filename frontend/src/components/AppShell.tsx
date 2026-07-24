import {
  Brain,
  CheckCircle2,
  Compass,
  FileSearch,
} from "lucide-react";
import { motion } from "framer-motion";
import type React from "react";
import { cn } from "../lib/utils";
import { Button } from "./ui";

export type WorkspaceView = "documents";
export type WorkspaceMode = "guided" | "explore";
export type ViewStatus = "current" | "complete" | "available" | "locked";

const navItems: Array<{ id: WorkspaceView; label: string; description: string; icon: React.ElementType }> = [
  {
    id: "documents",
    label: "Evidence Workspace",
    description: "Document review & insights",
    icon: FileSearch
  }
];

export function AppShell({
  children,
  activeView,
  setActiveView,
  workflowMode,
  setWorkflowMode,
  onboardingComplete,
  onStartOver,
  viewStatus,
  onAdvanceStep,
  canAdvanceStep
}: {
  children: React.ReactNode;
  activeView: WorkspaceView;
  setActiveView: (view: WorkspaceView) => void;
  workflowMode: WorkspaceMode;
  setWorkflowMode: (mode: WorkspaceMode) => void;
  onboardingComplete: boolean;
  onStartOver: () => void;
  viewStatus: Record<WorkspaceView, ViewStatus>;
  onAdvanceStep: () => void;
  canAdvanceStep: boolean;
}) {
  const currentNav = navItems.find((item) => item.id === activeView);
  const currentStatus = currentNav ? viewStatus[currentNav.id] : "available";
  const showGuidedBadge = workflowMode === "guided" && currentStatus === "complete";

  return (
    <div className="min-h-screen bg-medical-50 text-medical-900 dark:bg-medical-900 dark:text-white">
      <main>
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/85 px-8 py-4 backdrop-blur-md dark:border-white/10 dark:bg-medical-900/85">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-teal-700 via-teal-600 to-medical-600 text-sm font-bold text-white shadow-md dark:from-white dark:to-slate-200 dark:text-medical-900">
                CI
              </div>
              <div>
                <nav className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                  <span>Clinical Insights AI</span>
                </nav>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                  {workflowMode === "guided" && (
                    <span className="rounded-full bg-teal-50 px-2 py-0.5 text-teal-700 dark:bg-teal-500/10 dark:text-teal-300">
                      Guided mode
                    </span>
                  )}
                  {showGuidedBadge && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
                      <CheckCircle2 className="h-3 w-3" />
                      Query completed
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2">
              <div className="flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 p-1 dark:border-white/10 dark:bg-white/5">
                <Button
                  size="sm"
                  variant={workflowMode === "guided" ? "primary" : "ghost"}
                  onClick={() => setWorkflowMode("guided")}
                  title="Step-by-step guidance"
                  aria-label="Step-by-step mode"
                >
                  <Brain className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant={workflowMode === "explore" ? "primary" : "ghost"}
                  onClick={() => setWorkflowMode("explore")}
                  title="Explore freely"
                  aria-label="Explore mode"
                >
                  <Compass className="h-3.5 w-3.5" />
                </Button>
              </div>
              {workflowMode === "guided" && navItems.length > 1 && (
                <Button variant="primary" size="sm" onClick={onAdvanceStep} disabled={!canAdvanceStep}>
                  Next step
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={onStartOver}
                title="Clear query history and restart this workflow"
                aria-label="Reset"
              >
                Reset
              </Button>
            </div>
          </div>
        </header>

        <div className="px-8 py-8">
          <motion.div
            key={activeView}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22 }}
          >
            {children}
          </motion.div>
        </div>
      </main>
    </div>
  );
}
