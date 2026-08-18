import React,{useState, useEffect, useCallback, useRef} from 'react';
import './NewTestRunPage.css';
import { API_BASE_URL, API_ENDPOINTS,WS_BASE_URL } from "../../config/api";
// Import only the Bootstrap CSS for the select components

import CustomSelect from './CustomSelect/CustomSelect';
import Loop, { TestRunEvent } from './Loop/Loop';
import { getAuthHeaders, redirectToLogin } from "../../utils/auth";
import { useNavigationBlocker } from "../../hooks/useNavigationBlocker";

interface RunFormData {
  runName?: string;   // 👈 add this
  target: string;
  testPlan: string; 
  testCaseId: string ;
  testCaseIds: string[];
  metric: string;     // ✅ name
  maxTestCases: string;
  domain: string;
  language: string;
}

interface FilterItem {
  filter_name: string;
  extra_info?: string; // optional, matches backend
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

const formatTargetOption = (target: FilterItem) =>
  `${target.filter_name}${target.extra_info ? ` (${target.extra_info})` : ""}`;

const NewTestRunPage: React.FC = () => {
  // Sample data for dropdowns
  // const targets = ['Vaidya AI', 'Target 2', 'Target 3'];
  const testPlans = ['Plan 1', 'Plan 2', 'Plan 3'];
  const metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score'];
  const maxTestCases = ['5', '10', '20', '30', '50', '100', 'Custom'];
  const domains = ['E-commerce', 'Healthcare', 'Finance', 'Education'];
  const languages = ['Tamil', 'Hindi', 'Assamese', 'Bengali', 'Sindhi', 'Bodo'];
  const [runName, setRunName] = useState("");
  const [testCaseInput, setTestCaseInput] = useState("");
  const [isValidatingTestCase, setIsValidatingTestCase] = useState(false);
  const [testCaseValidation, setTestCaseValidation] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [maxTestCasesSelection, setMaxTestCasesSelection] = useState("10");
  const [domainOptions, setDomainOptions] = useState<string[]>([]);
  const [languageOptions, setLanguageOptions] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [runCompleted, setRunCompleted] = useState(false);
  const [totalTestCases, setTotalTestCases] = useState(0);
  const [filters, setFilters] = useState<AllFiltersResponse | null>(null);
  const [planMetrics, setPlanMetrics] = useState<string[]>([]);
  const [liveEvents, setLiveEvents] = useState<TestRunEvent[]>([]);
  const [showSeleniumLink, setShowSeleniumLink] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const wsConnectingRef = useRef<Promise<void> | null>(null);
  const activeRunIdRef = useRef<string | number | null>(null);
  const pendingRunStartRef = useRef(false);
  const pendingEventsRef = useRef<TestRunEvent[]>([]);
  useNavigationBlocker(isRunning);

  const [formData, setFormData] = useState<RunFormData>({
    runName: "",   
    target: "",
    testPlan: "",
    testCaseId:"",
    testCaseIds: [],
    metric: "",
    maxTestCases: "10", 
    domain: "",
    language: "",
  });

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

      // Optional: reset selected domain & language
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

  const hasPendingTestCase = testCaseInput.trim().length > 0;
  const isStartDisabled = !formData.testPlan || !formData.target || isRunning;
  const isTargetSelected = !!formData.target;
  const hasSelectedTestCases = formData.testCaseIds.length > 0;
  const seleniumHref = "/selenium/";
  const selectedTarget = filters?.targets.find(
    (target) =>
      formatTargetOption(target) === formData.target ||
      target.filter_name === formData.target
  );
  const selectedTargetType = selectedTarget?.extra_info?.trim().toLowerCase();
  const isSeleniumTarget =
    selectedTargetType === "whatsapp" || selectedTargetType === "webapp";
  const shouldShowSeleniumLink = showSeleniumLink && Boolean(runName) && isSeleniumTarget;

  const handleRunFinished = useCallback(() => {
    setRunCompleted(true);
    setIsRunning(false);
    setIsStopping(false);
  }, []);

  const handleWsMessage = useCallback((event: MessageEvent) => {
    const data: TestRunEvent = JSON.parse(event.data);
    const activeRunId = activeRunIdRef.current;

    if (activeRunId === null) {
      if (pendingRunStartRef.current) {
        pendingEventsRef.current.push(data);
      }
      return;
    }

    if (data.runId === undefined || String(data.runId) !== String(activeRunId)) {
      return;
    }

    console.log("Test run websocket event:", data);
    setLiveEvents((prev) => [...prev, data]);

    if (data.type === "RUN_FINISHED") {
      setRunCompleted(true);
      setIsRunning(false);
      setIsStopping(false);
      activeRunIdRef.current = null;
    }
  }, []);

  useEffect(() => {
    const handleBeforeUnload = () => {
      console.log("Tab closing, WS state:", wsRef.current?.readyState);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, []);

  const closeLiveSocket = useCallback(() => {
    activeRunIdRef.current = null;
    wsConnectingRef.current = null;
    pendingRunStartRef.current = false;
    pendingEventsRef.current = [];

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const ensureLiveSocket = useCallback(() => {
    const existingSocket = wsRef.current;

    if (existingSocket?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (existingSocket?.readyState === WebSocket.CONNECTING && wsConnectingRef.current) {
      return wsConnectingRef.current;
    }

    const ws = new WebSocket(`${WS_BASE_URL}/ws/test-run`);
    wsRef.current = ws;

    wsConnectingRef.current = new Promise<void>((resolve, reject) => {
      const timeoutId = window.setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          reject(new Error("Timed out connecting to test run websocket"));
          ws.close();
        }
      }, 10000);

      ws.onopen = () => {
        window.clearTimeout(timeoutId);
        wsConnectingRef.current = null;
        console.log("Test run websocket connected");
        resolve();
      };

      ws.onerror = () => {
        window.clearTimeout(timeoutId);
        wsConnectingRef.current = null;
        reject(new Error("Failed to connect to test run websocket"));
      };
    });

    ws.onmessage = handleWsMessage;
    ws.onclose = () => {
      if (wsRef.current === ws) {
        wsRef.current = null;
      }
      wsConnectingRef.current = null;
      console.log("Test run websocket closed");
    };

    return wsConnectingRef.current;
  }, [handleWsMessage]);

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
    return () => closeLiveSocket();
  }, [closeLiveSocket]);

  const fetchMetricsByPlan = async (planName: string) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/get_metrics_by_plan/${planName}`,
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
        throw new Error(`Failed to fetch metrics (${res.status})`);
      }

      const data = await res.json();
      setPlanMetrics(data.map((m: any) => m.filter_name));
    } catch (err) {
      console.error("Failed to fetch metrics", err);
      setPlanMetrics([]);
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
      fetchMetricsByPlan(value); // 🔥 second fetch happens here
    }
    if (key === "target") {
      fetchTargetMetadata(value);
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
      setTestCaseValidation({
        type: "success",
        message: ``,
      });
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
      alert("Click Add to include the entered test case before starting the run.");
      return;
    }

    setRunCompleted(false);
    setIsStopping(false);
    setLiveEvents([]);
    activeRunIdRef.current = null;
    pendingEventsRef.current = [];
    pendingRunStartRef.current = true;

    try {
      await ensureLiveSocket();
    } catch (err) {
      console.error("Unable to open websocket before starting run:", err);
      alert("Unable to connect to live progress updates. Please try again.");
      pendingRunStartRef.current = false;
      return;
    }

    let res: Response;
    try {
      res = await fetch(`${API_BASE_URL}/start-run`, {
        method: "POST",
        headers: getAuthHeaders(),
        credentials: "include",
        body: JSON.stringify(formData),
      });
    } catch (err) {
      console.error("Failed to start run:", err);
      pendingRunStartRef.current = false;
      alert("Failed to start run");
      return;
    }

    if (res.status === 401) {
      redirectToLogin();
      pendingRunStartRef.current = false;
      return;
    }

    const runData = await res.json(); // <-- this should now include runName, runId, testPlanId, metricId
     if (!res.ok) {
      alert(runData.detail || "Failed to start run");
      pendingRunStartRef.current = false;
      return;  // 🛑 STOP here
    }
    setTotalTestCases(runData.totalTestCases);
    setRunName(runData.runName);
    activeRunIdRef.current = runData.runId;
    pendingRunStartRef.current = false;

    const bufferedEvents = pendingEventsRef.current.filter(
      (pendingEvent) =>
        pendingEvent.runId !== undefined &&
        String(pendingEvent.runId) === String(runData.runId)
    );
    pendingEventsRef.current = [];

    if (bufferedEvents.length > 0) {
      setLiveEvents((prev) => [...prev, ...bufferedEvents]);
    }

    setIsRunning(true); // now we can start the Loop component
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
      <h1>Create New Test Run</h1>
      <p className="subtitle">Configure and start AI evaluation run</p>
      
      

      <div className="filters-container">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
          <label>Test Run Name</label>
          <input 
            type="text" 
            className="form-input" 
            placeholder="Enter run name (optional)"
            value={formData.runName}
            onChange={(e) => handleChange("runName", e.target.value)}
          />
        </div>
        <div className="filters-row">
          <div className="filter-item">
            <label>Target <span style={{ color: "#dc2626" }} aria-hidden="true">*</span></label>
            <CustomSelect
              options={
                filters?.targets.map(formatTargetOption) ?? []
              }
              defaultText="Select Target"
              onChange={(val) => handleChange("target", val)}
            />
          </div>

          <div className="filter-item">
            <label>Test Plan <span style={{ color: "#dc2626" }} aria-hidden="true">*</span></label>
            <CustomSelect
              options={filters?.plans.map(p => p.filter_name) ?? []}
              defaultText="Select Test Plan"
              onChange={(val) => handleChange("testPlan", val)}
            />
          </div>
          <div className="filter-item">
            <label>Metric </label>
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
              <p
                className={`test-case-validation ${testCaseValidation.type}`}
                role={testCaseValidation.type === "error" ? "alert" : "status"}
              >
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
            <label>Max test cases{maxTestCasesSelection === "Custom" && <span style={{ color: "#dc2626" }} aria-hidden="true"> *</span>}</label>
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
              options={isTargetSelected ? domainOptions : []}
              defaultText={
                isTargetSelected
                  ? "All Domains"
                  : "Please select target first"
              }
              onChange={(val) => handleChange("domain", val)}
              disabled={!isTargetSelected || hasSelectedTestCases}
            />
          </div>

          <div className="filter-item">
            <label>Language</label>
            <CustomSelect
              options={isTargetSelected ? languageOptions : []}
              defaultText={
                isTargetSelected
                  ? "All Languages"
                  : "Please select target first"
              }
              onChange={(val) => handleChange("language", val)}
              disabled={!isTargetSelected || hasSelectedTestCases}
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
        {(isRunning || runCompleted) && 
        <Loop isRunning={isRunning} 
          totalTestCases={totalTestCases} 
          stepsPerTestCase={4} 
          stepNames={["Prepare", "Finding elements", "Execute", "Store"]} planName={formData.testPlan}   
          metricName={formData.metric}
          testCaseName={formData.testCaseIds.join(", ")}
          runName={runName}
          liveEvents={liveEvents}
          onRunFinished={handleRunFinished}
          showTestExecutionLink={shouldShowSeleniumLink}
          seleniumHref={seleniumHref}
        />}       
      </div>
      
    </div>
  );
};

export default NewTestRunPage;
