import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import styles from "./TestRunDetails.module.css";
import Modal from "./Modal";
import RunTimeline from "./RunTimeline";
import DetailCard from "../common/DetailCard/DetailCard";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";
import { redirectToLogin } from "../../utils/auth";

interface RunSummary {
  run_id: number;
  run_name: string;
  target: string | null;
  domain: string | null;
  status: string;
  start_ts: string;
  end_ts: string | null;
  average_score?: number | null;
}

interface RunDetail {
  detail_id: number;
  run_name: string;
  testcase_name: string;
  metric_name: string;
  plan_name: string;
  conversation_id: string;
  status: string;
  score?: number | null;
}

interface FilterOption {
  filter_name: string;
}

interface AllFilters {
  metrics: FilterOption[];
  statuses: FilterOption[];
}

const RunDetails: React.FC = () => {
  const { runName } = useParams<{ runName: string }>();

  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [details, setDetails] = useState<RunDetail[]>([]);
  const [analyseLoading, setAnalyseLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [selectedDetailId, setSelectedDetailId] = useState<number | null>(null);
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null);
  const [executionDuration, setExecutionDuration] = useState<string | null>(null);
  const [filtersData, setFiltersData] = useState<AllFilters>({ metrics: [], statuses: [] });
  const [openFilterColumn, setOpenFilterColumn] = useState<string | null>(null);
  const [showScrollHint, setShowScrollHint] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(false);
  const [downloadState, setDownloadState] = useState<{
      runName: string;
      progress: number;
      phase: "generating" | "done";
    } | null>(null);
  const [analyseModal, setAnalyseModal] = useState<{
      runName: string;
      hasScore: boolean;
    } | null>(null);  
  const [cardHeight, setCardHeight] = useState<number | null>(null);
  const summaryCardRef = useRef<HTMLDivElement | null>(null);
  const tableScrollRef = useRef<HTMLDivElement | null>(null);
  const filterRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const navigate = useNavigate();

  const getAuthHeaders = (): HeadersInit => {
    const token = localStorage.getItem("access_token");
    return token
      ? {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        }
      : {
          "Content-Type": "application/json",
        };
  };

  const [activeFilters, setActiveFilters] = useState<{ metric?: string; status?: string }>({});

  // Measure left card height via ResizeObserver — table matches this exactly
  useEffect(() => {
    const measure = () => {
      if (summaryCardRef.current) {
        setCardHeight(summaryCardRef.current.offsetHeight);
      }
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (summaryCardRef.current) ro.observe(summaryCardRef.current);
    return () => ro.disconnect();
  }, [summary, executionDuration]);

  const statusMap = (
    status: string | null | undefined
  ): "COMPLETED" | "RUNNING" | "FAILED" | undefined => {
    if (status === "COMPLETED" || status === "RUNNING" || status === "FAILED") return status;
    return undefined;
  };

  const formatScore = (score?: number | null) => {
    if (score === null || score === undefined) return "Analysis not completed";
    if (!Number.isFinite(score)) return "Analysis not completed";
    return Number.isInteger(score) ? String(score) : score.toFixed(2);
  };

  const isPlanCellEvent = (target: EventTarget | null) => {
    if (!(target instanceof Node)) return false;
    const element =
      target instanceof HTMLElement ? target : target.parentElement;
    return Boolean(element?.closest("[data-plan-cell='true']"));
  };

  const handleFilterChange = (filterType: "metric" | "status", value: string) => {
    setActiveFilters((prev) => {
      if (!value) {
        const copy = { ...prev };
        delete copy[filterType];
        return copy;
      }
      return { ...prev, [filterType]: value };
    });
    setOpenFilterColumn(null);
  };
  const startAnalysis = async (mode: string, runName: string) => {
      setAnalyseLoading(true);
      try {
        const url = API_ENDPOINTS.ANALYSE_RUN(runName, mode);
        await fetch(url, {
          method: "GET",
          headers: getAuthHeaders(),
          credentials: "include",
        });
        navigate(`/analyse/${encodeURIComponent(runName)}?mode=${mode}`);
      } catch (err) {
        console.error("Analysis failed:", err);
        setAnalyseLoading(false);
        setAnalyseModal(null);
      }
    };
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openFilterColumn && filterRefs.current[openFilterColumn]) {
        const filterElement = filterRefs.current[openFilterColumn];
        if (filterElement && !filterElement.contains(event.target as Node)) {
          setOpenFilterColumn(null);
        }
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openFilterColumn]);

  useEffect(() => {
    fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_ALL_FILTERS}`, {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Unauthorized");
        }
        return res.json();
      })
      .then((data) => setFiltersData({ metrics: data.metrics, statuses: data.statuses }))
      .catch(console.error);
  }, []);

  useEffect(() => {
    const updateScrollHint = () => {
      const node = tableScrollRef.current;
      if (!node) {
        setShowScrollHint(false);
        setIsAtBottom(false);
        return;
      }
      setShowScrollHint(node.scrollHeight > node.clientHeight + 2);
      const maxScrollTop = node.scrollHeight - node.clientHeight;
      setIsAtBottom(node.scrollTop >= maxScrollTop - 2);
    };
    updateScrollHint();
    window.addEventListener("resize", updateScrollHint);
    return () => window.removeEventListener("resize", updateScrollHint);
  }, [details, cardHeight]);

  useEffect(() => {
    const node = tableScrollRef.current;
    if (!node) return;
    const onScroll = () => {
      const maxScrollTop = node.scrollHeight - node.clientHeight;
      setIsAtBottom(node.scrollTop >= maxScrollTop - 2);
    };
    node.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => node.removeEventListener("scroll", onScroll);
  }, [details]);

  useEffect(() => {
    const clearSelectionIfConversationModal = (event: Event) => {
      const target = event.target as HTMLElement | null;
      if (target?.id !== "conversationModal") return;
      setSelectedConversationId(null);
      setSelectedDetailId(null);
    };

    // Use document-level listener so it still works even if Bootstrap replaces/rehydrates modal DOM.
    document.addEventListener(
      "hide.bs.modal",
      clearSelectionIfConversationModal as EventListener
    );
    document.addEventListener(
      "hidden.bs.modal",
      clearSelectionIfConversationModal as EventListener
    );
    return () => {
      document.removeEventListener(
        "hide.bs.modal",
        clearSelectionIfConversationModal as EventListener
      );
      document.removeEventListener(
        "hidden.bs.modal",
        clearSelectionIfConversationModal as EventListener
      );
    };
  }, []);

  const handleScrollChevronClick = () => {
    const node = tableScrollRef.current;
    if (!node) return;
    if (isAtBottom) {
      node.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
    }
  };

  useEffect(() => {
    if (!runName) return;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (activeFilters.metric) params.append("metric", activeFilters.metric);
    if (activeFilters.status) params.append("status", activeFilters.status);

    fetch(API_ENDPOINTS.GET_TEST_RUN_DETAILS(runName, params.toString()), {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Unauthorized");
        }
        if (!res.ok) throw new Error(`API ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setSummary(data.summary);
        
        setDetails(data.details);
        
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [runName, activeFilters]);

  if (loading) return <p className={styles.loading}>Loading test run...</p>;
  if (error) return <p className={styles.error}>{error}</p>;
  if (!summary) return <p>No test run found</p>;

  const groupedByPlan = details.reduce((acc, detail) => {
    if (!acc[detail.plan_name]) acc[detail.plan_name] = [];
    acc[detail.plan_name].push(detail);
    return acc;
  }, {} as Record<string, RunDetail[]>);
  const hasExistingScores = details.some((detail) => typeof detail.score === "number");

  const tableContainerHeight = cardHeight ?? undefined;

  return (
    <div className={styles.container}>
      <RunTimeline
        runName={summary.run_name}
        hoveredMetric={hoveredMetric}
        hoveredPlan={hoveredPlan}
        onHoverPlan={setHoveredPlan}
        onHoverMetric={setHoveredMetric}
        onDurationCalculated={setExecutionDuration}
      />

      <div className={styles.flex}>
        {/* ── LEFT CARD — natural height, drives table height ── */}
        <div className={styles.summaryCard} ref={summaryCardRef}>
          <div className={styles.summaryContent}>
            <DetailCard label="Target" value={summary.target ?? "-"} icon="bi-bullseye" />
            <DetailCard label="Domain" value={summary.domain ?? "-"} icon="bi-globe" />
            {/* <DetailCard
              label="Status"
              value={summary.status}
              status={statusMap(summary.status)}
              icon="bi-activity"
            /> */}
            <DetailCard
              label="Started At"
              value={new Date(summary.start_ts).toLocaleString()}
              icon="bi-calendar-event"
            />
            <DetailCard
              label="Ended At"
              value={summary.end_ts ? new Date(summary.end_ts).toLocaleString() : "-"}
              icon="bi-calendar-check"
            />
            <DetailCard
              label="Duration"
              value={executionDuration ?? "-"}
              icon="bi-clock"
            />
            <div className={styles.actionsRow}>
              <div className={styles.actionsGroup}>
                <button
                  type="button"
                  className={`${styles.actionIconButton} ${styles.actionContinue}`}
                  data-tooltip="Continue"
                  onClick={() => navigate(`/continue-run/${summary.run_name}`)}
                  title="Continue"
                  aria-label={`Continue ${summary.run_name}`}
                >
                  <i className="bi bi-arrow-clockwise"></i>
                </button>
                <button
                          type="button"
                          className={`${styles.actionIconButton} ${styles.actionAnalyse}`}
                          data-tooltip="Analyse"
                          onClick={() => setAnalyseModal({ runName: summary.run_name, hasScore: typeof summary.average_score === "number" })}
                          title="Analyse"
                          aria-label={`Analyse ${summary.run_name}`}
                        >
                          <i className="bi bi-bar-chart-fill"></i>
                        </button>
                <button
                  type="button"
                  className={`${styles.actionIconButton} ${styles.actionReport}`}
                  data-tooltip="Report"
                  onClick={async () => {
                  if (downloadState) return;
                  setDownloadState({ runName: summary.run_name, progress: 0, phase: "generating" });
                  let p = 0;
                  const tick = setInterval(() => {
                    p = Math.min(p + Math.random() * 7 + 1, 92);
                    setDownloadState(prev => prev ? { ...prev, progress: Math.round(p) } : null);
                    }, 180);
                  try {
                    const response = await fetch(API_ENDPOINTS.DOWNLOAD_REPORT_NEW(summary.run_name), {
                      headers: getAuthHeaders(),
                      credentials: "include",
                      });
                    if (!response.ok) throw new Error("Failed to download report");
                    const blob = await response.blob();
                    clearInterval(tick);
                    setDownloadState(prev => prev ? { ...prev, progress: 100, phase: "done" } : null);
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.setAttribute("download", `${summary.run_name}-evaluation.pdf`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                    setTimeout(() => setDownloadState(null), 1500);
                    } catch (err) {
                    clearInterval(tick);
                    setDownloadState(null);
                    console.error("Report download failed:", err);
                    }
                    }}
                    title="Report"
                    aria-label={`Download report for ${summary.run_name}`}
                    >
                    <i className="bi bi-clipboard2-check"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT TABLE — height locked to left card height ── */}
        <div className={styles.tableLayout}>
          <section className={styles.tableSection}>
            <div
              className={`${styles.tableContainer}${isAtBottom ? ` ${styles.atBottom}` : ""}`}
            >
              <div
                ref={tableScrollRef}
                className={`${styles.tableScroll} table-responsive`}
              >
                <table className={styles.resultsTable}>
                  <thead>
                    <tr>
                      <th>Plan Name</th>
                      <th>Test Case</th>

                      {/* Metric Column with Filter */}
                      <th>
                        <div className="header-content">
                          <span>Metric</span>
                          <div
                            className="filter-wrapper"
                            ref={(el) => { filterRefs.current["metric"] = el; }}
                          >
                            <button
                              className="filter-trigger"
                              onClick={() =>
                                setOpenFilterColumn(openFilterColumn === "metric" ? null : "metric")
                              }
                            >
                              <i className={`bi bi-funnel${activeFilters.metric ? "-fill" : ""}`}></i>
                            </button>
                            {openFilterColumn === "metric" && (
                              <div className="filter-dropdown">
                                <div className="filter-options">
                                  <select
                                    className="form-select form-select-sm"
                                    value={activeFilters.metric || ""}
                                    onChange={(e) => handleFilterChange("metric", e.target.value)}
                                  >
                                    <option value="">All Metrics</option>
                                    {filtersData.metrics.map((opt) => (
                                      <option key={opt.filter_name} value={opt.filter_name}>
                                        {opt.filter_name}
                                      </option>
                                    ))}
                                  </select>
                                  {activeFilters.metric && (
                                    <button
                                      className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                      onClick={() => handleFilterChange("metric", "")}
                                    >
                                      Clear Filter
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </th>

                      <th>Score</th>

                      {/* Status Column with Filter */}
                      <th>
                        <div className="header-content">
                          <span>Status</span>
                          <div
                            className="filter-wrapper"
                            ref={(el) => { filterRefs.current["status"] = el; }}
                          >
                            <button
                              className="filter-trigger"
                              onClick={() =>
                                setOpenFilterColumn(openFilterColumn === "status" ? null : "status")
                              }
                            >
                              <i className={`bi bi-funnel${activeFilters.status ? "-fill" : ""}`}></i>
                            </button>
                            {openFilterColumn === "status" && (
                              <div className="filter-dropdown">
                                <div className="filter-options">
                                  <select
                                    className="form-select form-select-sm"
                                    value={activeFilters.status || ""}
                                    onChange={(e) => handleFilterChange("status", e.target.value)}
                                  >
                                    <option value="">All Statuses</option>
                                    {filtersData.statuses.map((opt) => (
                                      <option key={opt.filter_name} value={opt.filter_name}>
                                        {opt.filter_name}
                                      </option>
                                    ))}
                                  </select>
                                  {activeFilters.status && (
                                    <button
                                      className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                      onClick={() => handleFilterChange("status", "")}
                                    >
                                      Clear Filter
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {details.length === 0 ? (
                      <tr>
                        <td colSpan={5} className={styles.emptyState}>
                          No test case details found
                        </td>
                      </tr>
                    ) : (
                      Object.entries(groupedByPlan).flatMap(([planName, planDetails]) =>
                        planDetails.map((d, index) => {
                          const normalizedStatus = d.status.toUpperCase();
                          const statusClass =
                            normalizedStatus === "COMPLETED" || normalizedStatus === "SUCCESS"
                              ? styles.statusCompleted
                              : normalizedStatus === "FAILED"
                              ? styles.statusFailed
                              : normalizedStatus === "NEW"
                              ? styles.statusNew
                              : styles.statusRunning;

                          return (
                            <tr
                              key={d.detail_id}
                              role="button"
                              tabIndex={0}
                              aria-pressed={selectedDetailId === d.detail_id}
                              className={`${styles.tableRow} ${
                                hoveredMetric === d.metric_name ? styles.metricRowHover : ""
                              } ${selectedDetailId === d.detail_id ? styles.selectedRow : ""}`}
                              data-bs-toggle="modal"
                              data-bs-target="#conversationModal"
                              onClick={(e) => {
                                if (isPlanCellEvent(e.target)) return;
                                setSelectedConversationId(Number(d.conversation_id));
                                setSelectedDetailId(d.detail_id);
                              }}
                              onKeyDown={(e) => {
                                if (isPlanCellEvent(e.target)) return;
                                if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  setSelectedConversationId(Number(d.conversation_id));
                                  setSelectedDetailId(d.detail_id);
                                }
                              }}
                              onMouseEnter={() => setHoveredMetric(d.metric_name)}
                              onMouseLeave={() => setHoveredMetric(null)}
                            >
                              {index === 0 && (
                                <td
                                  rowSpan={planDetails.length}
                                  data-plan-cell="true"
                                  className={`${styles.planCell} align-middle text-center`}
                                  onClick={(e) => e.stopPropagation()}
                                  onKeyDown={(e) => e.stopPropagation()}
                                >
                                  {planName}
                                </td>
                              )}
                              <td>{d.testcase_name}</td>
                              <td>{d.metric_name}</td>
                              <td>{formatScore(d.score)}</td>
                              <td>
                                <span className={`${styles.statusCell} ${statusClass}`}>
                                  {normalizedStatus}
                                </span>
                              </td>
                            </tr>
                          );
                        })
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            </section>
        </div>
      </div>
      {/* Download overlay */}
      {downloadState && (
        <div className="download-overlay">
          <div className="download-overlay-card">
            {downloadState.phase === "done" ? (
              <div className="download-success-icon">
                <i className="bi bi-check-lg" />
              </div>
            ) : (
              <div className="download-big-spinner" />
            )}
            <div className="download-overlay-text">
              <p className="download-overlay-title">
                {downloadState.phase === "done" ? "Download ready" : "Generating report…"}
              </p>
              <p className="download-overlay-sub">
                {downloadState.phase === "done" ? "Saving to your device…" : downloadState.runName}
              </p>
            </div>
            <div className="download-prog-track">
              <div className="download-prog-fill" style={{ width: `${downloadState.progress}%` }} />
            </div>
            <span className="download-pct">{downloadState.progress}%</span>
          </div>
        </div>
      )}             
      {analyseModal && (
        <div className="download-overlay" onClick={() => { if (!analyseLoading) setAnalyseModal(null); }}>
          <div className="download-overlay-card analyse-modal" onClick={(e) => e.stopPropagation()}>
            {analyseLoading ? (
              <>
                <div className="download-big-spinner" />
                <div className="analyse-modal-header">
                  <p className="download-overlay-title" style={{ margin: 0 }}>Starting Analysis…</p>
                  <p className="download-overlay-sub" style={{ marginTop: 4 }}>{analyseModal.runName}</p>
                </div>
              </>
            ) : (
              <>
                <div className="analyse-modal-header">
                  <i className="bi bi-bar-chart-fill analyse-modal-icon"></i>
                  <p className="download-overlay-title" style={{ margin: 0 }}>Analyse Run</p>
                  <p className="download-overlay-sub" style={{ marginTop: 4 }}>{analyseModal.runName}</p>
                </div>
                <div className="analyse-modal-options">
                  {analyseModal.hasScore && (
                    <button
                      className="analyse-option-btn"
                      onClick={() => startAnalysis("retry_failed", analyseModal.runName)}
                    >
                      <i className="bi bi-arrow-repeat"></i>
                      <div>
                        <p className="analyse-option-title">Retry Failed</p>
                        <p className="analyse-option-sub">Re-run only the failed test cases</p>
                      </div>
                    </button>
                  )}
                  <button
                    className="analyse-option-btn"
                    onClick={() => startAnalysis("rerun_all", analyseModal.runName)}
                  >
                    <i className="bi bi-arrow-clockwise"></i>
                    <div>
                      <p className="analyse-option-title">Run All</p>
                      <p className="analyse-option-sub">Run all test cases </p>
                    </div>
                  </button>
                </div>
                <button className="analyse-cancel-btn" onClick={() => setAnalyseModal(null)}>
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      )}
      <Modal conversationId={selectedConversationId} />
    </div>
  );
};

export default RunDetails;
