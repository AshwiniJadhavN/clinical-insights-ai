import { useEffect, useMemo, useState } from "react";
import { AppShell, WorkspaceMode, ViewStatus, WorkspaceView } from "./components/AppShell";
import { getDocuments, getHealth, DocumentSummary, HealthResponse } from "./lib/api";
import { DocumentWorkspace } from "./views/DocumentWorkspace";

type QueryHistoryItem = {
  question: string;
  confidenceScore: number;
  evidenceStatus: string;
  timestamp: number;
};

type WorkflowSessionState = {
  activeView: WorkspaceView;
  completedViews: Partial<Record<WorkspaceView, boolean>>;
  queryHistory: QueryHistoryItem[];
};

type WorkflowPreferenceState = {
  onboardingComplete: boolean;
  preferredMode: WorkspaceMode;
};

const PREFERENCE_STORAGE_KEY = "ci-frontend-workflow-preferences-v1";
const SESSION_STORAGE_KEY = "ci-frontend-workflow-session-v1";

const WORKFLOW_ORDER: WorkspaceView[] = ["documents"];

function parseStoredJson<T>(value: string | null): T | null {
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

function getInitialPreferences(): WorkflowPreferenceState {
  if (typeof window === "undefined") {
    return {
      onboardingComplete: false,
      preferredMode: "guided"
    };
  }

  const parsed = parseStoredJson<WorkflowPreferenceState>(window.localStorage.getItem(PREFERENCE_STORAGE_KEY));
  if (!parsed) {
    return {
      onboardingComplete: false,
      preferredMode: "guided"
    };
  }

  return {
    onboardingComplete: Boolean(parsed.onboardingComplete),
    preferredMode: parsed.preferredMode === "explore" ? "explore" : "guided"
  };
}

function getInitialSession(): WorkflowSessionState {
  if (typeof window === "undefined") {
    return {
      activeView: "documents",
      completedViews: {},
      queryHistory: []
    };
  }

  const parsed = parseStoredJson<WorkflowSessionState>(window.sessionStorage.getItem(SESSION_STORAGE_KEY));
  if (!parsed) {
    return {
      activeView: "documents",
      completedViews: {},
      queryHistory: []
    };
  }

  const activeView = WORKFLOW_ORDER.includes(parsed.activeView) ? parsed.activeView : "documents";
  const queryHistory = Array.isArray(parsed.queryHistory)
    ? parsed.queryHistory.filter((item): item is QueryHistoryItem => {
        return (
          typeof item.question === "string" &&
          typeof item.confidenceScore === "number" &&
          typeof item.evidenceStatus === "string" &&
          typeof item.timestamp === "number"
        );
      })
    : [];

  return {
    activeView,
    completedViews: parsed.completedViews ?? {},
    queryHistory
  };
}

export function App() {
  const initialPreferences = getInitialPreferences();
  const initialSession = getInitialSession();

  const [activeView, setActiveView] = useState<WorkspaceView>(initialSession.activeView);
  const [health, setHealth] = useState<HealthResponse>();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [completedViews, setCompletedViews] = useState<Partial<Record<WorkspaceView, boolean>>>(
    initialSession.completedViews
  );
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>(initialSession.queryHistory);
  const [hasSuccessfulQuery, setHasSuccessfulQuery] = useState(initialSession.queryHistory.length > 0);
  const [hasFreshQueryInCurrentSession, setHasFreshQueryInCurrentSession] = useState(false);
  const [onboardingComplete, setOnboardingComplete] = useState(initialPreferences.onboardingComplete);
  const [preferredMode, setPreferredMode] = useState<WorkspaceMode>(initialPreferences.preferredMode);
  const [workflowMode, setWorkflowMode] = useState<WorkspaceMode>(
    initialPreferences.onboardingComplete ? initialPreferences.preferredMode : "guided"
  );

  async function refreshDocuments() {
    const documentResult = await getDocuments();
    setDocuments(documentResult);
  }

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [healthResult, documentResult] = await Promise.allSettled([
        getHealth(),
        getDocuments()
      ]);

      if (cancelled) {
        return;
      }

      if (healthResult.status === "fulfilled") {
        setHealth(healthResult.value);
      }
      if (documentResult.status === "fulfilled") {
        setDocuments(documentResult.value);
      }
    }

    load();
    const id = window.setInterval(load, 30000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const payload: WorkflowPreferenceState = {
      onboardingComplete,
      preferredMode
    };

    window.localStorage.setItem(PREFERENCE_STORAGE_KEY, JSON.stringify(payload));
  }, [onboardingComplete, preferredMode]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const payload: WorkflowSessionState = {
      activeView,
      completedViews,
      queryHistory
    };

    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(payload));
  }, [activeView, completedViews, queryHistory]);

  const canAccessView = useMemo(() => {
    if (workflowMode === "explore") {
      return (view: WorkspaceView) => WORKFLOW_ORDER.includes(view);
    }

    return (view: WorkspaceView) => WORKFLOW_ORDER.includes(view);
  }, [completedViews, workflowMode]);

  useEffect(() => {
    if (!canAccessView(activeView)) {
      setActiveView("documents");
    }
  }, [activeView, canAccessView]);

  function completeView(view: WorkspaceView) {
    setCompletedViews((previous) => ({ ...previous, [view]: true }));
  }

  function handleSetActiveView(view: WorkspaceView) {
    if (!canAccessView(view)) {
      return;
    }
    setActiveView(view);
  }

  function handleQuerySuccess(summary: Omit<QueryHistoryItem, "timestamp">) {
    const entry: QueryHistoryItem = {
      ...summary,
      timestamp: Date.now()
    };

    setHasSuccessfulQuery(true);
    setHasFreshQueryInCurrentSession(true);
    setQueryHistory((previous) => [entry, ...previous].slice(0, 8));
    completeView("documents");
  }

  function handleClearSession() {
    setQueryHistory([]);
    setHasSuccessfulQuery(false);
    setHasFreshQueryInCurrentSession(false);
    setCompletedViews({});
    setActiveView("documents");
  }

  function handleRestartGuidedFlow() {
    setWorkflowMode("guided");
    setPreferredMode("guided");
    setCompletedViews({});
    setActiveView("documents");
  }

  function handleStartOver() {
    const confirmed = window.confirm("Start over? This will clear query history and reset workflow progress.");
    if (!confirmed) {
      return;
    }

    handleClearSession();
    if (workflowMode === "guided") {
      handleRestartGuidedFlow();
    }
  }

  function handleSetWorkflowMode(mode: WorkspaceMode) {
    setWorkflowMode(mode);
    setPreferredMode(mode);
  }

  const canAdvanceStep = useMemo(() => {
    if (workflowMode !== "guided") {
      return false;
    }

    switch (activeView) {
      case "documents":
        return documents.length > 0 && hasSuccessfulQuery;
      default:
        return false;
    }
  }, [activeView, documents.length, hasSuccessfulQuery, workflowMode]);

  function handleAdvanceStep() {
    if (workflowMode !== "guided") {
      return;
    }

    if (!canAdvanceStep) {
      return;
    }

    completeView(activeView);
    const index = WORKFLOW_ORDER.indexOf(activeView);
    const isFinal = index === WORKFLOW_ORDER.length - 1;

    if (isFinal) {
      setOnboardingComplete(true);
      handleSetWorkflowMode("explore");
      setActiveView("documents");
      return;
    }

    setActiveView(WORKFLOW_ORDER[index + 1]);
  }

  const viewStatus = useMemo<Record<WorkspaceView, ViewStatus>>(() => {
    if (activeView === "documents") {
      return { documents: "current" };
    }

    if (completedViews.documents) {
      return { documents: "complete" };
    }

    return {
      documents: canAccessView("documents") ? "available" : "locked"
    };
  }, [activeView, canAccessView, completedViews]);

  const view = useMemo(() => {
    switch (activeView) {
      case "documents":
        return (
          <DocumentWorkspace
            documents={documents}
            guidedMode={workflowMode === "guided"}
            queryHistory={queryHistory}
            revealHistoryConfidence={hasFreshQueryInCurrentSession}
            onQuerySuccess={handleQuerySuccess}
            onDocumentsChanged={refreshDocuments}
            onClearHistory={() => {
              setQueryHistory([]);
              setHasFreshQueryInCurrentSession(false);
            }}
          />
        );
      default:
        return (
          <DocumentWorkspace
            documents={documents}
            guidedMode={workflowMode === "guided"}
            queryHistory={queryHistory}
            revealHistoryConfidence={hasFreshQueryInCurrentSession}
            onQuerySuccess={handleQuerySuccess}
            onDocumentsChanged={refreshDocuments}
            onClearHistory={() => {
              setQueryHistory([]);
              setHasFreshQueryInCurrentSession(false);
            }}
          />
        );
    }
  }, [activeView, documents, hasFreshQueryInCurrentSession, queryHistory, workflowMode]);

  return (
    <AppShell
      activeView={activeView}
      setActiveView={handleSetActiveView}
      workflowMode={workflowMode}
      setWorkflowMode={handleSetWorkflowMode}
      onboardingComplete={onboardingComplete}
      onStartOver={handleStartOver}
      viewStatus={viewStatus}
      onAdvanceStep={handleAdvanceStep}
      canAdvanceStep={canAdvanceStep}
    >
      {view}
    </AppShell>
  );
}
