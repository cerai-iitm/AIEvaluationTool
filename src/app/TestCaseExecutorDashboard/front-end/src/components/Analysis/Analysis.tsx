import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { API_ENDPOINTS, WS_BASE_URL } from "../../config/api";
import { getAuthHeaders, redirectToLogin } from "../../utils/auth";
import styles from "./Analysis.module.css";

interface RunDetail {
  detail_id: number;
  testcase_name: string;
  metric_name: string;
  strategy_name?: string;
  status: string;
  score?: number | null;
  error?: string | null;
  evaluation_reason?: string | null;  // ← add this
}

interface RunSummary {
  run_name: string;
  status: string;
  start_ts: string;
  end_ts: string | null;
}

interface TestRunResponse {
  summary: RunSummary;
  details: RunDetail[];
}

interface AnalyseStatusResponse {
  run_name: string;
  status: string;
  current?: number;
  total?: number;
  analysis_start_ts?: string;
  analysis_end_ts?: string;
  analysis_duration_seconds?: number;
  error?: string;
}

interface AnalysisProgressMessage {
  type: string;
  runName: string;
  current?: number;
  total?: number;
  testcaseName?: string;
  metricName?: string;
  strategyName?: string;
  detailId?: number;
  status?: string;
  score?: number | null;
  analysisStartTs?: string;
  analysisEndTs?: string;
  error?: string;
}

interface AccordionProps {
  details: RunDetail[];
  runningDetailId: number | null;
  isAnalysing: boolean;
}

// ─── STATUS ICON ─────────────────────────────────────────────────────────────

const statusIcon = (status: string) => {
  const size = 16;

  if (status === "COMPLETED")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-label="Completed" style={{ flexShrink: 0 }}>
        <circle cx="8" cy="8" r="8" fill="#22c55e" />
        <path d="M4.5 8.5l2.5 2.5 4.5-5" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );

  if (status === "RUNNING")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" aria-label="Running" style={{ flexShrink: 0 }}>
        <circle cx="8" cy="8" r="6.5" stroke="#2563eb" strokeWidth="2" fill="none" strokeDasharray="10 10">
          <animateTransform attributeName="transform" type="rotate" from="0 8 8" to="360 8 8" dur="0.9s" repeatCount="indefinite" />
        </circle>
      </svg>
    );

  if (status === "FAILED")
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-label="Failed" style={{ flexShrink: 0 }}>
        <circle cx="8" cy="8" r="8" fill="#ef4444" />
        <path d="M5 5l6 6M11 5l-6 6" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    );

  // PENDING
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" aria-label="Pending" style={{ flexShrink: 0 }}>
      <circle cx="8" cy="8" r="6.5" stroke="#94a3b8" strokeWidth="2" fill="none" />
    </svg>
  );
};

// ─── NESTED METRIC → STRATEGY ACCORDION ──────────────────────────────────────

const MetricStrategyAccordion: React.FC<AccordionProps> = ({
  details,
  runningDetailId,
  isAnalysing,
}) => {
  const grouped = useMemo(() => {
    const map: Record<string, RunDetail[]> = {};
    details.forEach((d) => {
      const metric = d.metric_name || "Unknown";
      if (!map[metric]) map[metric] = [];
      map[metric].push(d);
    });
    return map;
  }, [details]);

  const [openMetrics, setOpenMetrics] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const metricKeys = Object.keys(grouped);
    setOpenMetrics((prev) => {
      const next: Record<string, boolean> = {};
      metricKeys.forEach((m) => {
        next[m] = m in prev ? prev[m] : metricKeys.length <= 4;
      });
      return next;
    });
  }, [grouped]);

  useEffect(() => {
    if (runningDetailId == null) return;
    for (const [metric, items] of Object.entries(grouped)) {
      if (items.some((d) => d.detail_id === runningDetailId)) {
        setOpenMetrics((prev) => ({ ...prev, [metric]: true }));
        return;
      }
    }
  }, [runningDetailId, grouped]);

  const sortedMetricEntries = Object.entries(grouped).sort(([, aItems], [, bItems]) => {
    const aRunning = aItems.some(
      (d) => d.status === "RUNNING" || d.detail_id === runningDetailId
    );
    const bRunning = bItems.some(
      (d) => d.status === "RUNNING" || d.detail_id === runningDetailId
    );
    return aRunning === bRunning ? 0 : aRunning ? -1 : 1;
  });

  return (
    <div>
      {sortedMetricEntries.map(([metric, metricItems]) => {
        const metricDone = metricItems.filter(
          (d) => d.status === "COMPLETED" || d.status === "FAILED"
        ).length;
        const metricRunning = metricItems.some(
          (d) => d.status === "RUNNING" || d.detail_id === runningDetailId
        );
        const metricTotal = metricItems.length;
        const isMetricOpen = openMetrics[metric] ?? false;

        const metricStatusText =
          isAnalysing && metricRunning
            ? `${metricDone} / ${metricTotal} — running…`
            : `${metricDone} / ${metricTotal} done`;

        return (
          <div
            key={metric}
            style={{
              marginBottom: 12,
              borderRadius: 10,
              border: `1px solid ${metricRunning && isAnalysing ? "#93c5fd" : "#cbd5e1"}`,
              background: isMetricOpen ? "#f8fafc" : "#fff",
              boxShadow: metricRunning && isAnalysing ? "0 0 0 2px #bfdbfe" : "none",
              transition: "box-shadow 300ms ease, border-color 300ms ease",
            }}
          >
            <button
              type="button"
              onClick={() => setOpenMetrics((p) => ({ ...p, [metric]: !p[metric] }))}
              style={{
                width: "100%",
                textAlign: "left",
                padding: "12px 16px",
                background: "none",
                border: "none",
                fontWeight: 700,
                fontSize: "1.05rem",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                color: "#1e293b",
                borderBottom: isMetricOpen ? "1px solid #cbd5e1" : "none",
              }}
            >
              <span>
                {metric}{" "}
                <span
                  style={{
                    fontWeight: 400,
                    fontSize: "0.9rem",
                    color: metricRunning && isAnalysing ? "#2563eb" : "#64748b",
                  }}
                >
                  {metricStatusText}
                </span>
              </span>
              <span>{isMetricOpen ? "▼" : "▶"}</span>
            </button>

            {isMetricOpen && (
              <div style={{ padding: "8px 12px" }}>
                {metricItems.map((tc, idx) => {
                  const isRunning =
                    tc.status === "RUNNING" || tc.detail_id === runningDetailId;

                  return (
                    <div
                      key={tc.detail_id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        padding: "7px 6px",
                        borderBottom: idx < metricItems.length - 1 ? "1px solid #e2e8f0" : "none",
                        background: isRunning ? "#eff6ff" : "transparent",
                        fontWeight: isRunning ? 600 : 400,
                        boxShadow: isRunning ? "0 0 0 2px #bfdbfe" : "none",
                        borderRadius: isRunning ? 6 : 0,
                        transition: "background 300ms ease, box-shadow 300ms ease",
                      }}
                    >
                      {statusIcon(tc.status)}
                      <span
                        style={{
                          minWidth: 80,
                          fontFamily: "monospace",
                          fontSize: "0.88rem",
                          color: "#334155",
                        }}
                      >
                        {tc.testcase_name}
                      </span>
                      <span style={{ minWidth: 80, fontSize: "0.88rem", color: "#475569" }}>
                        Status: {tc.status}
                      </span>
                      <span style={{ minWidth: 60, fontSize: "0.88rem", color: "#0f172a" }}>
                        Score: {typeof tc.score === "number" ? tc.score.toFixed(2) : "0"}
                      </span>
                      {tc.status === "FAILED" && tc.error && (
                        <span
                          title={tc.error}
                          style={{
                            fontSize: "0.85rem",
                            color: "#b91c1c",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            maxWidth: 420,
                          }}
                        >
                          Error: {tc.error}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ─── HELPERS ──────────────────────────────────────────────────────────────────

const toFiniteNumber = (value: unknown): number | null => {
  if (value === null || value === undefined || value === "") return null;
  const numeric = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numeric) ? numeric : null;
};

const formatDuration = (start: string, end: string | null): string => {
  if (!start || !end) return "-";
  const startMs = new Date(start).getTime();
  const endMs = new Date(end).getTime();
  if (Number.isNaN(startMs) || Number.isNaN(endMs) || endMs < startMs) return "-";
  const totalSeconds = Math.floor((endMs - startMs) / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
};

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

const Analysis: React.FC = () => {
  const { runName } = useParams<{ runName: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const mode = searchParams.get("mode") ?? "rerun_all";
  const selectedDetailIdsParam = searchParams.get("detail_ids") ?? "";
  const selectedDetailIds = useMemo(
    () =>
      selectedDetailIdsParam
        .split(",")
        .filter((value) => value.trim() !== "")
        .map(Number)
        .filter(Number.isInteger),
    [selectedDetailIdsParam]
  );

  const [loading, setLoading] = useState(true);
  const [isAnalysing, setIsAnalysing] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isStopped, setIsStopped] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [details, setDetails] = useState<RunDetail[]>([]);
  const [analysisStartTs, setAnalysisStartTs] = useState<string | null>(null);
  const [analysisEndTs, setAnalysisEndTs] = useState<string | null>(null);
  const [analysisCurrent, setAnalysisCurrent] = useState(0);
  const [analysisTotal, setAnalysisTotal] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(null);
  const [runningDetailId, setRunningDetailId] = useState<number | null>(null);

  const orderedDetails = useMemo(
    () => [...details].sort((a, b) => a.detail_id - b.detail_id),
    [details]
  );
  const orderedDetailsRef = useRef<RunDetail[]>([]);
  useEffect(() => {
    orderedDetailsRef.current = orderedDetails;
  }, [orderedDetails]);

  // ── Fetch details
  // filterToProcessed: only keep items that were actually touched by analysis (have score or error)
  // keepOnlyCompleted: only keep items with server status COMPLETED (used before analysis starts)
  const fetchDetails = useCallback(
    async (
      targetRunName: string,
      silent = false,
      keepOnlyCompleted = false,
      filterToProcessed = false
    ) => {
      const res = await fetch(API_ENDPOINTS.ANALYSE_DETAILS(targetRunName, mode), {
        headers: getAuthHeaders(),
        credentials: "include",
      });
      if (res.status === 401) {
        redirectToLogin();
        throw new Error("Unauthorized");
      }
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Failed to load run details (${res.status})`);
      }
      const data: TestRunResponse = await res.json();
      setSummary(data.summary);
      let serverDetails = data.details || [];

      if (keepOnlyCompleted) {
        if (mode === "retry_failed") {
          serverDetails = serverDetails.filter(
            (d) => d.status === "COMPLETED" && (d.evaluation_reason ?? "").trim() === ""
          );
        }
        // Before analysis: only show COMPLETED test cases, reset to PENDING
        serverDetails = serverDetails.filter((d) => d.status === "COMPLETED");
        if (mode === "selected") {
          const selectedIds = new Set(selectedDetailIds);
          serverDetails = serverDetails.filter((d) => selectedIds.has(d.detail_id));
        }
        setDetails(serverDetails.map((d) => ({ ...d, status: "PENDING", score: null })));
      } else if (filterToProcessed) {
        // After analysis: only show items the backend actually processed
        const processed = serverDetails.filter(
          (d) => d.score !== null || d.error !== null
        );
        setDetails(processed.length > 0 ? processed : serverDetails);
      } else {
        setDetails(serverDetails);
      }

      if (!silent) setLoading(false);
    },
    [mode, selectedDetailIds]
  );

  // ── Apply a WS progress message ──────────────────────────────────────────
  const applyProgress = useCallback((payload: AnalysisProgressMessage) => {
    if (payload.analysisStartTs) setAnalysisStartTs(payload.analysisStartTs);
    if (payload.analysisEndTs) setAnalysisEndTs(payload.analysisEndTs);

    const current = toFiniteNumber(payload.current);
    const total = toFiniteNumber(payload.total);
    if (current !== null) setAnalysisCurrent(current);
    if (total !== null) setAnalysisTotal(total);

    const detailId = toFiniteNumber(payload.detailId);
    if (detailId === null) return;

    const finalStatus = payload.status === "FAILED" ? "FAILED" : "COMPLETED";

    setDetails((prev) => {
      const sorted = [...prev].sort((a, b) => a.detail_id - b.detail_id);
      const completedIdx = sorted.findIndex((d) => d.detail_id === detailId);
      if (completedIdx === -1) return prev;

      const sortedIdxMap = new Map(sorted.map((d, i) => [d.detail_id, i]));
      const nextDetail = sorted[completedIdx + 1] ?? null;

      if (nextDetail) {
        setRunningDetailId(nextDetail.detail_id);
      } else {
        setRunningDetailId(null);
      }

      return prev.map((d) => {
        const idx = sortedIdxMap.get(d.detail_id) ?? -1;

        if (d.detail_id === detailId) {
          return {
            ...d,
            status: finalStatus,
            score: payload.score !== undefined ? payload.score : d.score,
            error: payload.error ?? d.error ?? null,
          };
        }
        if (idx === completedIdx + 1) {
          return { ...d, status: "RUNNING" };
        }
        if (idx < completedIdx && (d.status === "PENDING" || d.status === "RUNNING")) {
          return { ...d, status: "COMPLETED" };
        }
        if (idx > completedIdx + 1 && d.status === "RUNNING") {
          return { ...d, status: "PENDING" };
        }
        return d;
      });
    });

    const sorted = orderedDetailsRef.current;
    const idx = sorted.findIndex((d) => d.detail_id === detailId);
    if (idx !== -1) setCurrentStepIndex(idx);
  }, []);

  // ── Main effect ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!runName) {
      setError("Run name is missing in the URL.");
      setLoading(false);
      return;
    }

    let isMounted = true;
    let ws: WebSocket | null = null;
    let statusTimer: number | null = null;
    let keepAliveTimer: number | null = null;

    const pollStatus = async () => {
      try {
        const res = await fetch(API_ENDPOINTS.ANALYSE_RUN_STATUS(runName), {
          headers: getAuthHeaders(),
          credentials: "include",
        });
        if (res.status === 401) {
          redirectToLogin();
          return;
        }
        if (!res.ok || !isMounted) return;
        const data: AnalyseStatusResponse = await res.json();
        if (data.current !== undefined) setAnalysisCurrent(data.current);
        if (data.total !== undefined) setAnalysisTotal(data.total);
        if (data.analysis_start_ts) setAnalysisStartTs(data.analysis_start_ts);
        if (data.analysis_end_ts) setAnalysisEndTs(data.analysis_end_ts);
        if (data.status === "STOPPING") setIsStopping(true);
        if (data.status === "STOPPED") {
          setIsAnalysing(false);
          setIsStopping(false);
          setIsStopped(true);
          setRunningDetailId(null);
        }
      } catch {
        // silent
      }
    };

    const startAnalysis = async () => {
      try {
        setError(null);

        // Fetch details — only keep COMPLETED ones, reset to PENDING for fresh start
        await fetchDetails(runName, false, true, false);
        if (!isMounted) return;

        const analyseRes = await fetch(
          API_ENDPOINTS.ANALYSE_RUN(runName, mode, selectedDetailIds),
          {
          headers: getAuthHeaders(),
          credentials: "include",
          }
        );
        if (analyseRes.status === 401) {
          redirectToLogin();
          return;
        }
        if (!analyseRes.ok) {
          const body = await analyseRes.json().catch(() => null);
          throw new Error(body?.detail || `Analysis request failed (${analyseRes.status})`);
        }

        const analyseData = (await analyseRes.json().catch(() => null)) as Partial<AnalyseStatusResponse> | null;
        if (!isMounted) return;

        const analyseStatus = analyseData?.status ?? "started";
        setIsAnalysing(
          analyseStatus === "started" || analyseStatus === "running"
        );
        setIsCompleted(false);
        setLoading(false);

        ws = new WebSocket(`${WS_BASE_URL}/ws/test-run`);

        ws.onopen = () => {
          ws?.send(JSON.stringify({ type: "ANALYSIS_SUBSCRIBE", runName }));
          keepAliveTimer = window.setInterval(() => ws?.send("ping"), 15_000);
        };

        ws.onmessage = async (event: MessageEvent) => {
          if (!isMounted) return;
          let payload: AnalysisProgressMessage | null = null;
          try {
            payload = JSON.parse(event.data);
          } catch {
            return;
          }
          if (!payload || payload.runName !== runName) return;

          if (payload.type === "ANALYSIS_STARTED") {
            setIsAnalysing(true);
            setIsStopping(false);
            setIsStopped(false);
            setIsCompleted(false);
            // Mark first detail as running
            setDetails((prev) => {
              const sorted = [...prev].sort((a, b) => a.detail_id - b.detail_id);
              if (sorted.length === 0) return prev;
              setRunningDetailId(sorted[0].detail_id);
              return prev.map((d, _, arr) => {
                const firstId = [...arr].sort((a, b) => a.detail_id - b.detail_id)[0].detail_id;
                return d.detail_id === firstId ? { ...d, status: "RUNNING" } : d;
              });
            });
            return;
          }

          if (payload.type === "ANALYSIS_PROGRESS") {
            applyProgress(payload);
            return;
          }

          if (payload.type === "ANALYSIS_FINISHED") {
            setIsAnalysing(false);
            setIsStopping(false);
            setIsCompleted(true);
            setRunningDetailId(null);
            applyProgress(payload);
            // Don't refresh - keep the current filtered view
            if (orderedDetailsRef.current.length > 0) {
              const last = orderedDetailsRef.current.length - 1;
              setCurrentStepIndex(last);
              setSelectedStepIndex(last);
            }
            if (statusTimer) {
              window.clearInterval(statusTimer);
              statusTimer = null;
            }
            return;
          }

          if (payload.type === "ANALYSIS_STOPPED") {
            setIsAnalysing(false);
            setIsStopping(false);
            setIsStopped(true);
            setRunningDetailId(null);
            if (payload.analysisEndTs) setAnalysisEndTs(payload.analysisEndTs);
            if (payload.current !== undefined) setAnalysisCurrent(payload.current);
            if (statusTimer) {
              window.clearInterval(statusTimer);
              statusTimer = null;
            }
            return;
          }

          if (payload.type === "ANALYSIS_FAILED") {
            setIsAnalysing(false);
            setRunningDetailId(null);
            setError(payload.error || "Analysis failed.");
            if (statusTimer) {
              window.clearInterval(statusTimer);
              statusTimer = null;
            }
          }
        };
      } catch (e) {
        if (isMounted) {
          setError(
            e instanceof Error
              ? e.message
              : "Something went wrong while analysing this run."
          );
          setLoading(false);
          setIsAnalysing(false);
        }
      }
    };

    startAnalysis();
    pollStatus();
    statusTimer = window.setInterval(pollStatus, 2_000);

    return () => {
      isMounted = false;
      if (statusTimer) window.clearInterval(statusTimer);
      if (keepAliveTimer) window.clearInterval(keepAliveTimer);
      if (ws) ws.close();
    };
  }, [runName, mode, selectedDetailIds, applyProgress, fetchDetails]);

  useEffect(() => {
    if (!isCompleted) {
      setSelectedStepIndex(currentStepIndex);
      return;
    }
    if (orderedDetails.length === 0) {
      setSelectedStepIndex(null);
      return;
    }
    setSelectedStepIndex((prev) => {
      if (prev === null) return orderedDetails.length - 1;
      return Math.min(prev, orderedDetails.length - 1);
    });
  }, [isCompleted, orderedDetails.length, currentStepIndex]);

  const handleStopAnalysis = async () => {
    if (!runName || isStopping) return;
    if (!window.confirm("Are you sure you want to cancel the analysis?")) return;

    setIsStopping(true);
    try {
      const res = await fetch(API_ENDPOINTS.STOP_ANALYSIS(runName), {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include",
      });
      if (res.status === 401) {
        redirectToLogin();
        return;
      }
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Failed to stop analysis (${res.status})`);
      }
      navigate(`/test-runs/${encodeURIComponent(runName)}`);
    } catch (e) {
      setIsStopping(false);
      alert(e instanceof Error ? e.message : "Failed to stop analysis");
    }
  };

  const stats = useMemo(() => {
    const scoredItems = orderedDetails.filter(
      (d) => typeof d.score === "number"
    ) as Array<RunDetail & { score: number }>;
    const totalScore = scoredItems.reduce((sum, d) => sum + d.score, 0);
    const overallScore = scoredItems.length > 0 ? totalScore / scoredItems.length : null;
    const totalCases = analysisTotal > 0 ? analysisTotal : orderedDetails.length;
    const completed = Math.max(0, Math.min(analysisCurrent, totalCases));
    return { totalCases, completedCases: completed, overallScore };
  }, [orderedDetails, analysisCurrent, analysisTotal]);

  const displayedStepIndex = isCompleted
    ? (selectedStepIndex ?? Math.max(orderedDetails.length - 1, 0))
    : currentStepIndex;

  const progressPercent =
    orderedDetails.length > 0
      ? Math.round(
          (Math.min(currentStepIndex + 1, orderedDetails.length) / orderedDetails.length) * 100
        )
      : 0;

  if (loading)
    return <div className={styles.state}>Running analysis for this run...</div>;
  if (error)
    return <div className={`${styles.state} ${styles.error}`}>{error}</div>;
  if (!summary)
    return <div className={styles.state}>No analysis data found.</div>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.headerRow}>
          <h2>Run Analysis</h2>
          {isAnalysing && (
            <button
              type="button"
              className={styles.stopButton}
              onClick={handleStopAnalysis}
              disabled={isStopping}
            >
              {isStopping ? "Stopping…" : "Stop Analysis"}
            </button>
          )}
        </div>
        {orderedDetails.length > 0 && isAnalysing && (
  <p>Analysis is running. Live execution loop is updating...</p>
)}
        {isCompleted && <p className={styles.success}>Completed successfully.</p>}
        {isStopped && <p className={styles.stopped}>Analysis stopped.</p>}
      </div>

      <section className={styles.cardGrid}>
        <div className={styles.card}>
          <span className={styles.label}>Run Name</span>
          <span className={styles.value}>{summary.run_name}</span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Duration</span>
          <span className={styles.value}>
            {formatDuration(analysisStartTs || "", analysisEndTs)}
          </span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Overall Score</span>
          <span className={styles.value}>
            {stats.overallScore !== null ? stats.overallScore.toFixed(2) : "-"}
          </span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Completed / Total</span>
          <span className={styles.value}>
            {stats.completedCases} / {stats.totalCases}
          </span>
        </div>
      </section>

      <section className={styles.executionWrap}>
        <div className={styles.executionHeaderRow}>
          <h3>Execution Loop</h3>
          {orderedDetails.length > 0 && (
            <span className={styles.executionCount}>
              Step {Math.min(displayedStepIndex + 1, orderedDetails.length)} /{" "}
              {orderedDetails.length}
            </span>
          )}
        </div>

        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: `${progressPercent}%` }} />
        </div>

        {orderedDetails.length === 0 ? (
          <div className={styles.empty}>No analysed test case records found.</div>
        ) : (
          <MetricStrategyAccordion
            details={orderedDetails}
            runningDetailId={runningDetailId}
            isAnalysing={isAnalysing}
          />
        )}
      </section>

      {isCompleted && (
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.routeButton}
            onClick={() =>
              navigate(`/test-runs/${encodeURIComponent(summary.run_name)}`)
            }
          >
            View Detailed Analysis
          </button>
        </div>
      )}
    </div>
  );
};

export default Analysis;
