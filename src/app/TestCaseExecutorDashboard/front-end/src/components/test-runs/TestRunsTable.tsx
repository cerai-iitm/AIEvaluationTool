import React, { useEffect, useState, useRef } from "react";
import "./TestRunsTable.css";
import { useNavigate, useSearchParams } from "react-router-dom";
import { API_BASE_URL, API_ENDPOINTS, LOGIN_URL } from "../../config/api";
import { AllFilters, FilterOption } from "../../types/Filters";
import { getAuthHeaders, redirectToLogin } from "../../utils/auth";

interface TestRun {
  run_id: number;
  totalPages : number;
  run_name: string;
  target: string;
  status: string;
  start_ts: string;
  end_ts: string | null;
  domain: string;
  duration_ms?: number;
  average_score?: number | null;
  evaluation_ts?: string;
  analysis_status?: string;
}

interface HeaderConfig {
  key: string;
  label: string;
  filterable: boolean;
  sortable?: boolean;
  sortKey?: "start_ts" | "end_ts";
  filterType?: "target" | "status" | "domain";
}

interface Props {
  filters: Record<string, string>;
  onFilterChange?: (filterType: string, value: string) => void;
}

const TestRunsTable: React.FC<Props> = ({ filters, onFilterChange }) => {
  const navigate = useNavigate();
  const loginUrl = LOGIN_URL;
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [filteredRuns, setFilteredRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [downloadState, setDownloadState] = useState<{
    runName: string;
    progress: number;
    phase: "generating" | "done";
  } | null>(null);
  const [analyseModal, setAnalyseModal] = useState<{
    runName: string;
    hasScore: boolean;
  } | null>(null);
  const [analyseLoading, setAnalyseLoading] = useState(false);
  const [availableFilters, setAvailableFilters] = useState<AllFilters>({
    domains: [],
    languages: [],
    targets: [],
    plans: [],
    metrics: [],
    statuses: [],
  });
  const [filtersLoading, setFiltersLoading] = useState(true);
  const [openFilterColumn, setOpenFilterColumn] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const filterRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const [sortBy, setSortBy] = useState<"start_ts" | "end_ts">("end_ts");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const pageNumbersWrapperRef = useRef<HTMLDivElement | null>(null);
  const pageNumberButtonRefs = useRef<Record<number, HTMLButtonElement | null>>({});
  const FILTER_KEY_MAP: Record<string, keyof AllFilters> = {
    domain: "domains",
    target: "targets",
    status: "statuses",
  };
  const COLUMN_CLASS: Record<string, string> = {
    run_id: "col-run-id",
    run_name: "col-run-name",
    target: "col-target",
    start_ts: "col-started-at",
    duration: "col-duration",
    average_score: "col-score",
    evaluation_ts: "col-evaluation",
    status: "col-status",
    domain: "col-domain",
    actions: "col-actions",
  };
  const headers: HeaderConfig[] = [
    { key: "run_id", label: "Run Id", filterable: false },
    { key: "run_name", label: "Run Name", filterable: false },
    { key: "target", label: "Target", filterable: true, filterType: "target" },
    { key: "start_ts", label: "Started At", filterable: false, sortable: true, sortKey: "start_ts" },
    { key: "duration", label: "Duration", filterable: false },
    { key: "average_score", label: "Score", filterable: false },
    { key: "evaluation_ts", label: "Evaluation Time", filterable: false },
    { key: "status", label: "Status", filterable: true, filterType: "status" },
    { key: "domain", label: "Domain", filterable: true, filterType: "domain" },
    { key: "actions", label: "Actions", filterable: false },
  ];
  const handleAnalyseClick = async (runName: string, hasScore: boolean) => {
  try {
    const res = await fetch(API_ENDPOINTS.ANALYSE_HEALTH, {  // ✅ no ()
      headers: getAuthHeaders(),
      credentials: "include",
    });
    if (!res.ok) {
      alert("Ollama is not running. Please start Ollama and try again.");
      return;
    }
    setAnalyseModal({ runName, hasScore });
  } catch (err) {
    alert("Ollama is not running. Please start Ollama and try again.");
  }
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
    setFiltersLoading(true);
    fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_ALL_FILTERS}`, {
      headers: getAuthHeaders(),
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) { redirectToLogin(); throw new Error("Unauthorized"); }
        if (!res.ok) throw new Error(`Failed to fetch filters (${res.status})`);
        return res.json();
      })
      .then((data: AllFilters) => { setAvailableFilters(data); setFiltersLoading(false); })
      .catch((err) => { console.error("Error fetching filters:", err); setFiltersLoading(false); });
  }, [loginUrl]);

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

  const handleFilterChange = (filterType: string, value: string) => {
    onFilterChange?.(filterType, value);
    setOpenFilterColumn(null);
  };

  const handleFilterClear = (filterType: string) => {
    onFilterChange?.(filterType, "");
    setOpenFilterColumn(null);
  };

  const toggleFilterDropdown = (columnKey: string) => {
    setOpenFilterColumn(openFilterColumn === columnKey ? null : columnKey);
  };

  const handleSort = (sortKey: "start_ts" | "end_ts") => {
    if (sortBy === sortKey) {
      setOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(sortKey);
      setOrder("desc");
    }
    setCurrentPage(1);
  };

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams(filters);
    params.append("sort_by", sortBy);
    params.append("order", order);
    params.append("page", String(currentPage));
    params.append("page_size", String(itemsPerPage));
    
    const url = `${API_BASE_URL}${API_ENDPOINTS.GET_ALL_TEST_RUNS}?${params.toString()}`;
    fetch(url, { headers: getAuthHeaders(), credentials: "include" })
      .then((res) => {
        if (res.status === 401) { redirectToLogin(); throw new Error("Unauthorized"); }
        if (!res.ok) throw new Error(`Failed to fetch test runs (${res.status})`);
        return res.json();
      })
      .then((data: TestRun[] | { detail?: string }) => {
        const safeRuns = Array.isArray(data) ? data : [];
        setRuns(safeRuns);
        setFilteredRuns(safeRuns);
        setTotalPages(safeRuns[0]?.totalPages ?? 1); 
        
      })
      .catch((err) => console.error("Error fetching test runs:", err))
      .finally(() => setLoading(false));
  }, [filters, sortBy, order, loginUrl,currentPage,itemsPerPage]);
  // alert(totalPage);
  // const indexOfLastRun = currentPage * itemsPerPage;
  // const indexOfFirstRun = indexOfLastRun - itemsPerPage;
  const safeFilteredRuns = Array.isArray(filteredRuns) ? filteredRuns : [];
  // const currentRuns = safeFilteredRuns.slice(indexOfFirstRun, indexOfLastRun);
  const currentRuns = safeFilteredRuns;
  // const totalPages = Math.ceil(safeFilteredRuns.length / itemsPerPage);
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  useEffect(() => {
    if (totalPages <= 5) return;
    const activeButton = pageNumberButtonRefs.current[currentPage];
    if (activeButton) {
      activeButton.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
    }
  }, [currentPage, totalPages]);

  const pageNumbers = [];
  for (let i = 1; i <= totalPages; i++) pageNumbers.push(i);

  const SortIcon = ({ columnKey }: { columnKey: "start_ts" | "end_ts" }) => {
    const isActive = sortBy === columnKey;
    if (columnKey === "start_ts") {
      const isAscending = isActive && order === "asc";
      return (
        <i
          className={`bi ${isAscending ? "bi-chevron-down" : "bi-chevron-up"}`}
          style={{
            fontSize: '22px',
            color: '#ffffff',
            fontWeight: 'bold',
          }}
        ></i>
      );
    }
    if (!isActive) return <i className="bi bi-chevron-expand" style={{ fontSize: '22px', color: 'rgba(255,255,255,0.35)' }}></i>;
    return order === "asc"
      ? <i className="bi bi-chevron-up" style={{ fontSize: '22px', color: '#ffffff', fontWeight: 'bold' }}></i>
      : <i className="bi bi-chevron-down" style={{ fontSize: '22px', color: '#ffffff', fontWeight: 'bold' }}></i>;
  };

  return (
    <div className="test-runs-table-wrapper">
      <div className="table-card">
        <div className="table-responsive">
          <table className="test-runs-table">
            <colgroup>
              {headers.map((header) => (
                <col key={header.key} className={COLUMN_CLASS[header.key] || ""} />
              ))}
            </colgroup>
            <thead>
              <tr>
                {headers.map((header) => (
                  <th
                    key={header.key}
                    scope="col"
                    className={`${COLUMN_CLASS[header.key] || ""} ${header.filterable ? "filterable-header" : ""} ${header.sortable ? "sortable-header" : ""}`}
                  >
                    <div className="header-content">
                      {header.sortable && header.sortKey ? (
                        <button className="sort-trigger" onClick={() => handleSort(header.sortKey!)} title={`Sort by ${header.label}`}>
                          <span>{header.label}</span>
                          <SortIcon columnKey={header.sortKey} />
                        </button>
                      ) : (
                        <span>{header.label}</span>
                      )}
                      {header.filterable && header.filterType && (
                        <div className="filter-wrapper" ref={(el) => { filterRefs.current[header.key] = el; }}>
                          <button className="filter-trigger" onClick={() => toggleFilterDropdown(header.key)} title={`Filter by ${header.label}`}>
                            <i className={`bi bi-funnel${filters[header.filterType] ? "-fill" : ""}`}></i>
                          </button>
                          {openFilterColumn === header.key && (
                            <div className="filter-dropdown">
                              <div className="filter-options">
                                <select
                                  className="form-select form-select-sm"
                                  value={filters[header.filterType] || ""}
                                  onChange={(e) => handleFilterChange(header.filterType!, e.target.value)}
                                  disabled={filtersLoading}
                                >
                                  <option value="">All {header.label}</option>
                                  {availableFilters[FILTER_KEY_MAP[header.filterType!]]?.map((opt: FilterOption) => (
                                    <option key={opt.filter_name} value={opt.filter_name}>{opt.filter_name}</option>
                                  ))}
                                </select>
                                {filters[header.filterType] && (
                                  <button className="btn btn-sm btn-outline-secondary mt-2 w-100" onClick={() => handleFilterClear(header.filterType!)}>
                                    Clear Filter
                                  </button>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={headers.length} className="table-loading">
                    <div className="loading-spinner"></div>
                    <span>Loading test runs...</span>
                  </td>
                </tr>
              ) : !Array.isArray(currentRuns) || currentRuns.length === 0 ? (
                <tr>
                  <td colSpan={headers.length} className="table-empty">
                    No test runs match the selected filters
                  </td>
                </tr>
              ) : (
                currentRuns.map((run) => (
                  <tr
                    key={run.run_id}
                    role="button"
                    className="table-row"
                    onClick={() => {
                      if (run.status === "RUNNING" || run.status === "NEW") {
                        alert("Run is not completed yet");
                        return;
                      }
                      navigate(`/test-runs/${run.run_name}`);
                    }}
                  >
                    <td className="col-run-id cell-center nowrap">{run.run_id}</td>
                    <td className="col-run-name run-name-cell">
                      <span className="run-name-text" title={run.run_name}>{run.run_name}</span>
                    </td>
                    <td className="col-target nowrap">
                      <span className="cell-ellipsis" title={run.target}>{run.target}</span>
                    </td>
                    <td className="col-started-at nowrap">
                      <span className="cell-ellipsis" title={new Date(run.start_ts).toLocaleString()}>
                        {new Date(run.start_ts).toLocaleString()}
                      </span>
                    </td>
                    <td className="col-duration cell-center nowrap">
                      {run.duration_ms != null ? formatDuration(run.duration_ms) : "-"}
                    </td>
                    <td className="col-score cell-center nowrap" onClick={(e) => e.stopPropagation()}>
                      {typeof run.average_score === "number" ? run.average_score.toFixed(2) : "-"}
                    </td>
                    <td className="col-evaluation nowrap">
                      {run.evaluation_ts != null ? (
                        <span className="cell-ellipsis" title={new Date(run.evaluation_ts).toLocaleString("en-US")}>
                          {new Date(run.evaluation_ts).toLocaleString("en-US")}
                        </span>
                      ) : "-"}
                    </td>
                    <td className="col-status nowrap">
                      <span className={`status-badge ${
                        run.status === "COMPLETED" || run.status === "PASSED" ? "status-completed"
                        : run.status === "RUNNING" || run.status === "IN_PROGRESS" ? "status-running"
                        : run.status === "FAILED" ? "status-failed"
                        : "status-default"
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="col-domain nowrap">
                      <span className="cell-ellipsis" title={run.domain}>{run.domain}</span>
                    </td>
                    <td className="col-actions actions-cell nowrap" onClick={(e) => e.stopPropagation()}>
                      <div className="actions-group">
                        <button
                          type="button"
                          className="action-icon-button action-continue"
                          data-tooltip="Continue"
                          onClick={() => navigate(`/continue-run/${run.run_name}`)}
                          title="Continue"
                          aria-label={`Continue ${run.run_name}`}
                        >
                          <i className="bi bi-arrow-clockwise"></i>
                        </button>
                        <button
                          type="button"
                          className="action-icon-button action-analyse"
                          data-tooltip="Analyse"
                          onClick={() => handleAnalyseClick(run.run_name, typeof run.average_score === "number")}
                          title="Analyse"
                          aria-label={`Analyse ${run.run_name}`}
                        >
                          <i className="bi bi-bar-chart-fill"></i>
                        </button>
                        <button
                          type="button"
                          className="action-icon-button action-report"
                          data-tooltip="Report"
                          onClick={async () => {
                            if (run.analysis_status === "failed") {
                              alert("Please complete the Analysis first.");
                              return;
                            }
                            if (downloadState) return;
                            setDownloadState({ runName: run.run_name, progress: 0, phase: "generating" });
                            let p = 0;
                            const tick = setInterval(() => {
                              p = Math.min(p + Math.random() * 7 + 1, 92);
                              setDownloadState(prev => prev ? { ...prev, progress: Math.round(p) } : null);
                            }, 180);
                            try {
                              const response = await fetch(API_ENDPOINTS.DOWNLOAD_REPORT_NEW(run.run_name), {
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
                              link.setAttribute("download", `${run.run_name}-evaluation.pdf`);
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
                          aria-label={`Download report for ${run.run_name}`}
                        >
                          <i className="bi bi-clipboard2-check"></i>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="sticky">
        {totalPages > 1 && (
          <div className="pagination-wrapper">
            <div className="pagination-container">
              <button className="pagination-button" onClick={() => paginate(1)} disabled={currentPage === 1} aria-label="First page">
                <i className="bi bi-chevron-double-left"></i>
              </button>
              <button className="pagination-button" onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1} aria-label="Previous page">
                <i className="bi bi-chevron-left"></i>
              </button>
              <div ref={pageNumbersWrapperRef} className={`pagination-numbers-wrapper ${totalPages > 5 ? 'scrollable' : ''}`}>
                {pageNumbers.map(number => (
                  <button
                    key={number}
                    ref={(el) => { pageNumberButtonRefs.current[number] = el; }}
                    className={`pagination-number ${number === currentPage ? 'active' : ''}`}
                    onClick={() => paginate(number)}
                    aria-label={`Page ${number}`}
                  >
                    {number}
                  </button>
                ))}
              </div>
              <button className="pagination-button" onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages} aria-label="Next page">
                <i className="bi bi-chevron-right"></i>
              </button>
              <button className="pagination-button" onClick={() => paginate(totalPages)} disabled={currentPage === totalPages} aria-label="Last page">
                <i className="bi bi-chevron-double-right"></i>
              </button>
            </div>
          </div>
        )}
        <div className="table-footer">
          Showing {currentRuns.length} of {safeFilteredRuns[0]?.totalPages! * itemsPerPage} test runs
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

      {/* Analyse modal */}
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

    </div>
  );
};

export default TestRunsTable;

function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "-";
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}
