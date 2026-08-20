import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

export interface TestRunEvent {
  type: "RUN_STARTED" | "STEP_UPDATE" | "TESTCASE_FINISHED" | "RUN_FINISHED";
  runId?: string | number;
  total?: number;
  testcaseIndex?: number;
  step?: number;
  status?: StepStatus | string;
  current?: number;
  error?: string;
  agentResponse?: string;
}

interface LoopProps {
  isRunning: boolean;
  totalTestCases: number;
  stepsPerTestCase: number; // 👈 how many steps each TC has
  stepNames?: string[]; // 👈 Names for each step
  planName?: string;     // 👈 add
  runName?: string;   // <-- ADD THIS
  metricName?: string;   // 👈 add
  testCaseName?: string; 
  liveEvents?: TestRunEvent[];
  onRunFinished?: (status?: string) => void;
  showTestExecutionLink?: boolean;
  seleniumHref?: string;
  
}

type StepStatus = "PENDING" | "RUNNING" | "DONE" | "FAILED";

  const Loop: React.FC<LoopProps> = ({
     isRunning,
  totalTestCases,
  stepsPerTestCase,
  stepNames: propStepNames,
  planName,
  runName,
  metricName,
  testCaseName,
  liveEvents = [],
  onRunFinished,
  showTestExecutionLink = false,
  seleniumHref = "/selenium/"
  }) => {
  const [currentTestCase, setCurrentTestCase] = useState(0);
  const navigate = useNavigate();
  const activeTestCaseRef = useRef(0);
  const processedEventCountRef = useRef(0);
  // Track status for each step individually
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(
    Array(stepsPerTestCase).fill("PENDING")
  );
  const [runCompleted, setRunCompleted] = useState(false);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  // Default step names if not provided
  const stepLabels = Array.from({ length: stepsPerTestCase }, (_, i) => 
    i === 0 ? 'Setup' : 
    i === 1 ? 'Validation' : 
    i === 2 ? 'Execution' : 
    i === 3 ? 'Cleanup' : 
    `Step ${i + 1}`
  );
  
  // Use stepNames from props if provided, otherwise use default labels
  const displayStepNames = propStepNames || stepLabels;

  // Calculate progress percentage, ensuring it doesn't exceed 100%
  const progressPercent = totalTestCases === 0
    ? 0
    : Math.min(100, Math.round((currentTestCase / totalTestCases) * 100));
    
  // Ensure currentTestCase doesn't exceed totalTestCases for display
  const displayTestCase = Math.min(currentTestCase, totalTestCases);

  useEffect(() => {
    if (!isRunning) return;

    activeTestCaseRef.current = 0;
    processedEventCountRef.current = 0;
    setCurrentTestCase(0);
    setRunCompleted(false);
    setRunStatus(null);
    setStepStatuses(Array(stepsPerTestCase).fill("PENDING"));
  }, [isRunning, stepsPerTestCase]);

  useEffect(() => {
    const nextEvents = liveEvents.slice(processedEventCountRef.current);
    if (nextEvents.length === 0) return;

    processedEventCountRef.current = liveEvents.length;

    nextEvents.forEach((liveEvent) => {
      switch (liveEvent.type) {
      case "RUN_STARTED":
        activeTestCaseRef.current = 0;
        setRunCompleted(false);
        setRunStatus(null);
        setCurrentTestCase(0);
        setStepStatuses(Array(stepsPerTestCase).fill("PENDING"));
        break;

      case "STEP_UPDATE": {
        const testcaseIndex = Number(liveEvent.testcaseIndex ?? 0);
        const stepIndex = Number(liveEvent.step ?? 0) - 1;
        const status = liveEvent.status as StepStatus;
        const previousTestCase = activeTestCaseRef.current;

        if (testcaseIndex < previousTestCase) {
          return;
        }

        activeTestCaseRef.current = testcaseIndex;
        setCurrentTestCase((prev) => Math.max(prev, testcaseIndex));
        setStepStatuses((prev) => {
          const next =
            testcaseIndex === previousTestCase
              ? [...prev]
              : Array(stepsPerTestCase).fill("PENDING");

          if (stepIndex >= 0 && stepIndex < next.length) {
            next[stepIndex] = status;
          } else {
            console.warn(`Invalid step index: ${stepIndex}, max allowed: ${next.length - 1}`);
          }

          return next;
        });
        break;
      }

      case "TESTCASE_FINISHED": {
        const finishedTestCase = Number(liveEvent.current ?? 0);

        if (finishedTestCase < activeTestCaseRef.current) {
          return;
        }

        activeTestCaseRef.current = finishedTestCase + 1;
        setStepStatuses(Array(stepsPerTestCase).fill("PENDING"));
        setCurrentTestCase(Math.min(finishedTestCase + 1, totalTestCases));
        break;
      }

      case "RUN_FINISHED": {
        const status = String(liveEvent.status ?? "");
        const completedSuccessfully = status === "COMPLETED";
        const error = String(liveEvent.error ?? "").toLowerCase();
        const displayStatus =
          !completedSuccessfully &&
          (error.includes("stopped") || error.includes("frontend disconnected"))
            ? "STOPPED"
            : status;

        // A stopped/failed run must retain the last testcase shown. Only a
        // genuinely completed run is allowed to advance the UI to 100%.
        if (completedSuccessfully) {
          activeTestCaseRef.current = totalTestCases;
          setCurrentTestCase(totalTestCases);
        }
        setRunStatus(displayStatus);
        setRunCompleted(true);
        onRunFinished?.(status);
        console.log("🏁 Run finished", status);
        break;
      }
      }
    });
  }, [liveEvents, onRunFinished, stepsPerTestCase, totalTestCases]);

  /* ---------- UI HELPERS ---------- */

  const getStepColor = (stepIndex: number) => {
    const status = stepStatuses[stepIndex]; // stepIndex is 0-based here
    
    switch (status) {
      case "DONE":
        return "#22C55E"; // green
      case "RUNNING":
        return "#F59E0B"; // orange
      case "FAILED":
        return "#EF4444"; // red
      default:
        return "#E5E7EB"; // gray (pending)
    }
  };

  /* ---------- RENDER ---------- */

  // Calculate estimated time remaining (example: 1.5s per test case)
  const estimatedTimeRemaining = Math.max(0, (totalTestCases - currentTestCase) * 1.5);
  
  return (
    <div style={{
      width: '100%',
      borderTop: '1px solid #E5E7EB',
      marginTop: '24px',
      paddingTop: '24px',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      color: '#111827',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        marginBottom: '14px'
      }}>
        <h2 style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: 600,
          color: '#111827'
        }}>
          {runCompleted
            ? runStatus === "COMPLETED"
              ? "Test Run Completed"
              : runStatus === "STOPPED" ? "Test Run Stopped" : "Test Run Failed"
            : "Test Run in Progress"}
        </h2>
        <div style={{
          fontSize: '14px',
          color: '#4B5563',
          background: '#F3F4F6',
          padding: '4px 8px',
          borderRadius: '4px',
          fontWeight: 500,
          textAlign: 'right'
        }}>
          {planName} {metricName && `• ${metricName}`} {testCaseName && `• ${testCaseName}`}
        </div>
      </div>
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
        marginBottom: '16px'
      }}>
        <p style={{
          margin: 0,
          fontSize: '14px',
          color: '#4B5563'
        }}>
          {runCompleted
            ? runStatus === "COMPLETED"
              ? "All test cases executed"
              : runStatus === "STOPPED" ? "Execution stopped" : "Execution failed"
            : "Executing test cases"}
        </p>
        {showTestExecutionLink && (
          <a
            href={seleniumHref}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              minHeight: '32px',
              boxSizing: 'border-box',
              padding: '0 12px',
              border: '1px solid #cbd5e1',
              borderRadius: '4px',
              background: '#ffffff',
              color: '#1d4ed8',
              fontSize: '13px',
              fontWeight: 500,
              lineHeight: 1,
              textDecoration: 'none',
              whiteSpace: 'nowrap',
              boxShadow: '0 1px 2px rgba(15, 23, 42, 0.08)',
            }}
          >
            <i className="bi bi-display" aria-hidden="true" />
            <span>View Test Execution</span>
          </a>
        )}
      </div>
      
      <div style={{
        marginBottom: '16px',
        fontSize: '14px',
        fontWeight: 500,
        color: '#1F2937'
      }}>
        TC {displayTestCase} of {totalTestCases}
      </div>
      
      <div style={{
        height: '8px',
        background: '#E5E7EB',
        borderRadius: '4px',
        marginBottom: '4px',
        overflow: 'hidden'
      }}>
        <div
          style={{
            width: `${progressPercent}%`,
            height: '100%',
            background: '#10B981',
            borderRadius: '4px',
            transition: 'width 0.3s ease',
          }}
        />
      </div>
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '24px',
        fontSize: '12px',
        color: '#6B7280'
      }}>
        <span>{progressPercent}% complete</span>
      </div>
      
      <div style={{
        display: 'flex',
        alignItems: 'center',
        color: '#4B5563',
        fontSize: '14px',
        gap: '8px'
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span>Estimated time: ~{estimatedTimeRemaining.toFixed(0)}s</span>
      </div>
      
      <div style={{ marginTop: '24px' }}>
        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'center'
        }}>
          {Array.from({ length: stepsPerTestCase }).map((_, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                minWidth: '80px',
              }}
            >
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: getStepColor(idx),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  color: stepStatuses[idx] === 'PENDING' ? '#9CA3AF' : '#111827',
                  fontWeight: 500,
                  transition: 'all 0.3s ease',
                  border: stepStatuses[idx] === 'PENDING' ? '2px solid #E5E7EB' : '2px solid transparent',
                }}
              >
                {idx + 1}
              </div>
              <span style={{
                fontSize: '12px',
                color: stepStatuses[idx] === 'PENDING' ? '#9CA3AF' : '#4B5563',
                textAlign: 'center',
                fontWeight: stepStatuses[idx] === 'RUNNING' ? 600 : 400,
              }}>
                {displayStepNames[idx]}
              </span>
            </div>
          ))}
        </div>
      </div>
      {runCompleted && (
        <div
          style={{
            marginTop: "24px",
            padding: "16px",
            background: runStatus === "COMPLETED" ? "#ECFDF5" : "#FEF2F2",
            border: `1px solid ${runStatus === "COMPLETED" ? "#10B981" : "#EF4444"}`,
            borderRadius: "10px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <span
            style={{
              color: runStatus === "COMPLETED" ? "#065F46" : "#991B1B",
              fontWeight: 600,
              fontSize: "14px",
            }}
          >
            {runStatus === "COMPLETED"
              ? "✅ Test run completed successfully"
              : runStatus === "STOPPED" ? "Run stopped" : "Test run failed"}
          </span>

          <button
            onClick={() => navigate(`/test-runs/${runName}`)}
            style={{
              padding: "8px 14px",
              borderRadius: "6px",
              border: "none",
              background: "#10B981",
              color: "#FFFFFF",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            View Test Run Details
          </button>
        </div>
      )}
    </div>
  );
};

export default Loop;
