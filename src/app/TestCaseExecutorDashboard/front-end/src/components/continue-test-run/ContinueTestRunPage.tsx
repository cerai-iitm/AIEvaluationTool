import React, { useState, useEffect, useCallback,useRef } from 'react';
import './ContinueTestRunPage.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Accordion, Button } from 'react-bootstrap';
import CustomSelect from './CustomSelect/CustomSelect';
import Loop from './Loop/Loop';
import { API_BASE_URL, API_ENDPOINTS, WS_BASE_URL } from "../../config/api";
import { useParams } from 'react-router-dom';
import { getAuthHeaders, redirectToLogin } from '../../utils/auth';
import { useNavigationBlocker } from "../../hooks/useNavigationBlocker";


interface RunFormData {
  runName: string;
  // target: string;
  testPlan: string; 
  testCaseId: string ;
  testCaseIds: string[];
  metric: string;
  maxTestCases: string;
  domain: string;
  language: string;
}

interface FilterItem {
  filter_name: string;
  extra_info?: string;
}

interface AllFiltersResponse {
  domains: FilterItem[];
  languages: FilterItem[];
  targets: FilterItem[];
  plans: FilterItem[];
  metrics: FilterItem[];
  statuses: FilterItem[];
}

interface InterfaceManagerStatus {
  docker: boolean;
}

const normalizeTargetName = (value?: string) =>
  (value || "").replace(/\s*\(.*?\)\s*$/, "").trim().toLowerCase();

const formatRunTimestamp = (timestamp?: string | null, fallback = "N/A") => {
  if (!timestamp) return fallback;
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? fallback : date.toLocaleString();
};

const ContinueRunPage: React.FC = () => {

  const maxTestCases = ['5', '10', '20', '30', '50', '100', 'Custom'];
  const languages = ['English', 'Spanish', 'French', 'German', 'Chinese'];
  const [isRunning, setIsRunning] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [testCaseInput, setTestCaseInput] = useState("");
  const [isValidatingTestCase, setIsValidatingTestCase] = useState(false);
  const [testCaseValidation, setTestCaseValidation] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [maxTestCasesSelection, setMaxTestCasesSelection] = useState("10");
  const [runFinished, setRunFinished] = useState(false);
  const [totalTestCases, setTotalTestCases] = useState(0);
  const [filters, setFilters] = useState<AllFiltersResponse | null>(null);
  const [existingRun, setExistingRun] = useState<any>(null);
  const [groupedDetails, setGroupedDetails] = useState<Record<string, string[]>>({});
  const [planMetrics, setPlanMetrics] = useState<string[]>([]);
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [showSeleniumLink, setShowSeleniumLink] = useState(false);
  const [hasContinuedRunStarted, setHasContinuedRunStarted] = useState(false);
  useNavigationBlocker(isRunning);
  const wsRef = useRef<WebSocket | null>(null);
  const activeRunIdRef = useRef<string | number | null>(null);
  const [formData, setFormData] = useState<RunFormData>({
    runName: "",
    // target: "",
    testPlan: "",
    testCaseId: "",
    testCaseIds: [],
    metric: "",
    maxTestCases: "10",
    domain: "",
    language: "",
  });

  const isStartDisabled = !formData.testPlan || isRunning;
  const hasSelectedTestCases = formData.testCaseIds.length > 0;
  const seleniumHref = "/selenium/";
  const existingRunTarget = normalizeTargetName(existingRun?.target);
  const selectedTarget = filters?.targets.find(
    (target) => normalizeTargetName(target.filter_name) === existingRunTarget
  );
  const selectedTargetType = selectedTarget?.extra_info?.trim().toLowerCase();
  const isSeleniumTarget =
    selectedTargetType === "whatsapp" || selectedTargetType === "webapp";
  const shouldShowSeleniumLink =
    showSeleniumLink && hasContinuedRunStarted && isSeleniumTarget;
  

  const { runName } = useParams();

  const handleRunFinished = useCallback(() => {
    setRunFinished(true);
    setIsRunning(false);
    setIsStopping(false);
    activeRunIdRef.current = null;
  }, []);

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_ALL_FILTERS}`, {
          headers: getAuthHeaders(),
          credentials: "include",
        });

        if (res.status === 401) {
          redirectToLogin();
          return;
        }

        if (!res.ok) {
          throw new Error(`Failed to fetch filters (${res.status})`);
        }

        const data: AllFiltersResponse = await res.json();
        setFilters(data);
      } catch (err) {
        console.error("Failed to fetch filters", err);
      }
    };
    fetchFilters();
  }, []);

  useEffect(() => {
    const fetchInterfaceManagerStatus = async () => {
      try {
        const res = await fetch(API_ENDPOINTS.GET_INTERFACE_MANAGER_STATUS, {
          headers: getAuthHeaders(),
          credentials: "include",
        });

        if (res.status === 401) {
          redirectToLogin();
          return;
        }

        if (!res.ok) {
          throw new Error(`Failed to fetch interface manager status (${res.status})`);
        }

        const data: InterfaceManagerStatus = await res.json();
        setShowSeleniumLink(Boolean(data.docker));
      } catch (err) {
        console.error("Failed to fetch interface manager status", err);
        setShowSeleniumLink(false);
      }
    };

    fetchInterfaceManagerStatus();
  }, []);

  useEffect(() => {
    if (runName) {
      handleChange("runName", runName);
      handleFetchRun(runName);
    }
  }, [runName]);

  useEffect(() => {
    const handleBeforeUnload = () => {
        if (wsRef.current) {
            wsRef.current.close();
        }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
}, []);

  const fetchMetricsByPlan = async (planName: string) => {
    try {
      const res = await fetch(API_ENDPOINTS.GET_METRICS_BY_PLAN(planName), {
        headers: getAuthHeaders(),
        credentials: "include",
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      if (!res.ok) {
        throw new Error(`Failed to fetch metrics (${res.status})`);
      }

      const data = await res.json();
      setPlanMetrics(data.map((m: any) => m.filter_name));
    } catch (err) {
      console.error("Failed to fetch metrics", err);
      setPlanMetrics([]);
    }
  };

  const handleFetchRun = async (nameOverride?: string) => {
    const name = nameOverride || formData.runName;
    try {
      const res = await fetch(`${API_BASE_URL}/continue-run`, {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include",
        body: JSON.stringify({ run_name: name }),
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      if (!res.ok) {
        alert("Run not found");
        return;
      }

      const data = await res.json();
      
      setExistingRun(data.run);
      setHasContinuedRunStarted(false);
      if (data.run?.target) {
        fetchTargetMetadata(data.run.target);
      }

      const grouped: Record<string, string[]> = {};
      data.details.forEach((d: any) => {
        if (!grouped[d.plan_name]) grouped[d.plan_name] = [];
        if (!grouped[d.plan_name].includes(d.metric_name)) {
          grouped[d.plan_name].push(d.metric_name);
        }
      });

      setGroupedDetails(grouped);

    } catch (err) {
      console.error(err);
    }
  };

  const fetchTargetMetadata = async (targetName: string) => {
    try {
      const res = await fetch(
        API_ENDPOINTS.GET_TARGET_METADATA(targetName),
        {
          headers: getAuthHeaders(),
          credentials: "include",
        }
      );

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      if (!res.ok) {
        throw new Error("Failed to fetch target metadata");
      }

      const data = await res.json();

      setDomainOptions(data.domains || []);
      setLanguageOptions(data.languages || []);

      setFormData(prev => ({
        ...prev,
        domain: "",
        language: ""
      }));

    } catch (err) {
      console.error("Error fetching target metadata:", err);
      setDomainOptions([]);
      setLanguageOptions([]);
    }
  };

  const handleChange = (key: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [key]: value,
      ...(key === "testPlan" && { metric: "", testCaseId: "", testCaseIds: [] }),
      ...(key === "metric" && value && { testCaseId: "", testCaseIds: [] }),
    }));

    if (key === "testPlan") {
      setTestCaseInput("");
      setTestCaseValidation(null);
      fetchMetricsByPlan(value);
    }
  };

  const addTestCase = async () => {
    const testCaseName = testCaseInput.trim().toUpperCase();
    if (!testCaseName) return;

    if (formData.testCaseIds.includes(testCaseName)) {
      setTestCaseValidation({
        type: "error",
        message: `Test case '${testCaseName}' has already been added.`,
      });
      return;
    }

    setIsValidatingTestCase(true);
    setTestCaseValidation(null);

    try {
      const testCaseUrl = `${API_ENDPOINTS.GET_TEST_CASE(testCaseName)}?plan_name=${encodeURIComponent(formData.testPlan)}`;
      const res = await fetch(testCaseUrl, {
        headers: getAuthHeaders(),
        credentials: "include",
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setTestCaseValidation({
          type: "error",
          message: data.detail || `Test case '${testCaseName}' is invalid.`,
        });
        return;
      }

      setFormData(prev => ({
        ...prev,
        metric: "",
        testCaseId: "",
        testCaseIds: [...prev.testCaseIds, testCaseName],
      }));
      setTestCaseInput("");
      setTestCaseValidation(null);
    } catch (err) {
      console.error("Failed to validate test case:", err);
      setTestCaseValidation({
        type: "error",
        message: "Unable to validate the test case. Please try again.",
      });
    } finally {
      setIsValidatingTestCase(false);
    }
  };

  const removeTestCase = (testCaseName: string) => {
    setFormData(prev => ({
      ...prev,
      testCaseIds: prev.testCaseIds.filter(name => name !== testCaseName),
    }));
  };

  const handleMaxTestCasesChange = (value: string) => {
    setMaxTestCasesSelection(value);
    handleChange("maxTestCases", value === "Custom" ? "" : value);
  };
 
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (testCaseInput.trim()) {
      alert("Click Add to include the entered test case before continuing the run.");
      return;
    }

    setRunFinished(false);
    setHasContinuedRunStarted(false);

    if (!formData.runName) {
      alert("Please enter a run name and fetch it first.");
      return;
    }

    if (!existingRun) {
      alert("Please fetch a valid run before continuing.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/continue-run-with-plan`, {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        alert(data.detail || "Failed to continue run");
        return;
      }

      setTotalTestCases(data.totalTestCases);
      activeRunIdRef.current = data.runId;
      setHasContinuedRunStarted(true);
      setIsRunning(true);

      const ws = new WebSocket(`${WS_BASE_URL}/ws/test-run`);
      wsRef.current = ws;
      ws.onopen = () => {
        console.log("WebSocket connected for continue");
        ws.send(JSON.stringify({ type: "SUBSCRIBE", runId: data.runId }));
      };

      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        if (update.runId === undefined || String(update.runId) !== String(data.runId)) {
          return;
        }
        console.log("Continue update:", update);
      };

      ws.onclose = () => {
        console.log("WebSocket closed");
        setIsRunning(false);
      };

    } catch (err) {
      console.error("Error continuing run:", err);
      setIsRunning(false);
    }
  };

  const handleStopRun = async () => {
    const runId = activeRunIdRef.current;
    if (runId === null || isStopping) return;

    setIsStopping(true);
    try {
      const res = await fetch(API_ENDPOINTS.STOP_RUN(runId), {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include",
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to stop run");
      }
    } catch (err) {
      console.error("Failed to stop run:", err);
      alert(err instanceof Error ? err.message : "Failed to stop run");
      setIsStopping(false);
    }
  };

  return (
    <div className="new-test-run-container">
      <h1>Continue Test Run</h1>
      <p className="subtitle">Use the existing setup or update plan, metrics, and test cases before running</p>

      <div className="accordion-container">
        <Accordion defaultActiveKey={null} className="mb-3">
          {existingRun && (
            <Accordion.Item eventKey="0">
              <Accordion.Header>Run Details</Accordion.Header>
              <Accordion.Body>
                <div className="run-details-accordion">
                  <div className="row">
                    <div className="col-md-6">
                      <p><strong>Target:</strong> {existingRun.target || 'N/A'}</p>
                      <p><strong>Status:</strong> 
                        <span className={`badge bg-${existingRun.status === 'completed' ? 'success' : 'warning'}`}>
                          {existingRun.status || 'N/A'}
                        </span>
                      </p>
                    </div>
                    <div className="col-md-6">
                      <p><strong>Start Time:</strong> {formatRunTimestamp(existingRun.start_ts)}</p>
                      <p><strong>End Time:</strong> {formatRunTimestamp(existingRun.end_ts, 'In Progress')}</p>
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <h5>Metrics by Plan</h5>
                    {Object.entries(groupedDetails).map(([plan, metrics]) => (
                      <div key={plan} className="mb-3">
                        <h6>{plan}</h6>
                        <div className="list-group">
                          {metrics.map((metric, idx) => (
                            <div key={idx} className="list-group-item">
                              {metric}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Accordion.Body>
            </Accordion.Item>
          )}

          <Accordion.Item eventKey="1">
            <Accordion.Header 
              className={!existingRun ? 'text-muted' : ''}
              onClick={(e) => !existingRun && e.preventDefault()}
            >
              Use Existing or Modify Setup {!existingRun && <span className="ms-2">(Fetching run...)</span>}
            </Accordion.Header>
            <Accordion.Body>
              {existingRun ? (
                <div className="filters-container">
                  <span className="form-required-notice">* Required</span>
                  <form onSubmit={handleSubmit}>
                    <div className="filters-row">
                    {/* <div className="filter-item">
                      <label>Target</label>
                      <CustomSelect
                        options={filters?.targets?.map(t => t.filter_name) ?? []}
                        defaultText="Select Target"
                        onChange={(val: string) => handleChange("target", val)}
                      />
                    </div> */}

                    <div className="filter-item">
                      <label>Test Plan <span className="required-asterisk" aria-hidden="true">*</span></label>
                      <CustomSelect
                        options={filters?.plans?.map(p => p.filter_name) ?? []}
                        defaultText="Select Test Plan"
                        onChange={(val: string) => handleChange("testPlan", val)}
                      />
                    </div>
                      <div className="filter-item">
                      <label>Metric</label>
                      <CustomSelect
                        key={formData.testCaseIds.join("|")}
                        options={planMetrics}
                        defaultText={
                          !formData.testPlan
                            ? "Select Test Plan first"
                            : formData.testCaseIds.length > 0
                            ? "Test cases selected"
                            : "All Metrics"
                        }
                        disabled={!formData.testPlan || formData.testCaseIds.length > 0}
                        onChange={(val) => handleChange("metric", val)}
                      />
                    </div>
                    <div className="filter-item">
                      <label>Test Case</label>
                      <div className="test-case-entry">
                        <input
                          type="text"
                          placeholder={
                            !formData.testPlan
                            ? "Select Test Plan first"
                            : formData.metric
                            ? "Metric selected"
                            : "Enter Test Case Name"
                          }
                          value={testCaseInput}
                          disabled={!formData.testPlan || !!formData.metric}
                          onChange={(e) => {
                            setTestCaseInput(e.target.value.toUpperCase());
                            setTestCaseValidation(null);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              addTestCase();
                            }
                          }}
                        />
                        <button
                          type="button"
                          className="add-test-case-button"
                          onClick={addTestCase}
                          disabled={!testCaseInput.trim() || !formData.testPlan || !!formData.metric || isValidatingTestCase}
                        >
                          {isValidatingTestCase ? "Checking…" : "Add"}
                        </button>
                      </div>
                      {testCaseValidation && (
                        <p className="test-case-validation error" role="alert">
                          {testCaseValidation.message}
                        </p>
                      )}
                    </div>

                    
                  </div>

                  {formData.testCaseIds.length > 0 && (
                    <div className="selected-test-cases" aria-label="Selected test cases">
                      <span className="selected-test-cases-label">Added test cases</span>
                      <div className="test-case-chips">
                        {formData.testCaseIds.map(testCaseName => (
                          <span className="test-case-chip" key={testCaseName}>
                            {testCaseName}
                            <button
                              type="button"
                              onClick={() => removeTestCase(testCaseName)}
                              aria-label={`Remove ${testCaseName}`}
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="filters-row">
                    <div className="filter-item">
                      <label>Max test cases{maxTestCasesSelection === "Custom" && <span className="required-asterisk" aria-hidden="true"> *</span>}</label>
                      <CustomSelect
                        options={maxTestCases}
                        defaultText="Select Max"
                        value={maxTestCasesSelection}
                        showDefaultOption={false}
                        disabled={hasSelectedTestCases}
                        onChange={handleMaxTestCasesChange}
                      />
                      {maxTestCasesSelection === "Custom" && (
                        <input
                          className="custom-max-input"
                          type="number"
                          min="1"
                          step="1"
                          placeholder="Enter max test cases"
                          value={formData.maxTestCases}
                          disabled={hasSelectedTestCases}
                          onChange={(e) => handleChange("maxTestCases", e.target.value)}
                          required
                        />
                      )}
                    </div>

                    <div className="filter-item">
                      <label>Domain</label>
                      <CustomSelect
                       options={domainOptions }
                        defaultText="All Domains"
                        onChange={(val) => handleChange("domain", val)}
                        disabled={hasSelectedTestCases}
                      />
                    </div>

                    <div className="filter-item">
                      <label>Language</label>
                      <CustomSelect
                        options={languageOptions}
                        defaultText="All Languages"
                        onChange={(val) => handleChange("language", val)}
                        disabled={hasSelectedTestCases}
                      />
                    </div>
                  </div>

                  <div className="run-actions-row">
                    <button type="submit" className="start-button" disabled={isStartDisabled}>
                      Start Run
                    </button>
                    {isRunning && (
                      <button
                        type="button"
                        className="stop-button"
                        onClick={handleStopRun}
                        disabled={isStopping}
                      >
                        {isStopping ? "Stopping…" : "Stop Run"}
                      </button>
                    )}
                    </div>
                  </form>
                  {(isRunning || runFinished) && (
                    <Loop
                      isRunning={isRunning}
                      totalTestCases={totalTestCases}
                      stepsPerTestCase={4}
                      stepNames={["Prepare", "Finding elements", "Execute", "Store"]}
                      planName={formData.testPlan}
                      metricName={formData.metric}
                      testCaseName={formData.testCaseIds.join(", ")}
                      onRunFinished={handleRunFinished}
                      showTestExecutionLink={shouldShowSeleniumLink}
                      seleniumHref={seleniumHref}
                    />
                  )}
                </div>
              ) : (
                <div className="text-center py-3 text-muted">
                  Please wait while we fetch the run details...
                </div>
              )}
            </Accordion.Body>
          </Accordion.Item>
        </Accordion>
      </div>
    </div>
  );
};

export default ContinueRunPage;
