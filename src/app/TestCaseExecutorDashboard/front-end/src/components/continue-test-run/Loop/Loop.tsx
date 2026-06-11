import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {WS_BASE_URL,} from "../../../config/api"


interface LoopProps {
  isRunning: boolean;
  totalTestCases: number;
  stepsPerTestCase: number; // 👈 how many steps each TC has
  stepNames?: string[]; // 👈 Names for each step
  planName?: string;     // 👈 add
  metricName?: string;   // 👈 add
  testCaseName?: string; 
  onRunFinished?: (status?: string) => void;
}

type StepStatus = "PENDING" | "RUNNING" | "DONE" | "FAILED";

const Loop: React.FC<LoopProps> = ({
  isRunning,
  totalTestCases,
  stepsPerTestCase,
  stepNames: propStepNames,
  planName,    
  metricName,
  testCaseName,
  onRunFinished
}) => {
  const [currentTestCase, setCurrentTestCase] = useState(0);
  const navigate = useNavigate();
  const { runName } = useParams();
  const [runCompleted, setRunCompleted] = useState(false);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  // Track status for each step individually
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(
    Array(stepsPerTestCase).fill("PENDING")
  );
  
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

    setRunCompleted(false);
    setRunStatus(null);
    const ws = new WebSocket(`${WS_BASE_URL}/ws/test-run`);

    ws.onopen = () => {
      console.log("✅ WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("📩 WS EVENT:", data);

      switch (data.type) {
        case "RUN_STARTED":
          setCurrentTestCase(0);
          setStepStatuses(Array(stepsPerTestCase).fill("PENDING"));
          break;

        case "STEP_UPDATE":
          console.log('STEP_UPDATE received:', { step: data.step, status: data.status });
          setCurrentTestCase(data.testcaseIndex);
          setStepStatuses((prev) => {
            const next = [...prev];
            // Convert 1-based step to 0-based index
            const stepIndex = data.step - 1;
            if (stepIndex >= 0 && stepIndex < next.length) {
              next[stepIndex] = data.status;
            } else {
              console.warn(`Invalid step index: ${stepIndex}, max allowed: ${next.length - 1}`);
            }
            console.log('Updated step statuses:', next);
            return next;
          });
          break;

        case "TESTCASE_FINISHED":
          setStepStatuses(Array(stepsPerTestCase).fill("PENDING"));
          setCurrentTestCase(data.current + 1);
          break;
        case "RUN_FINISHED":
          setRunCompleted(true);
          setRunStatus(data.status);
          onRunFinished?.(data.status);
          console.log("🏁 Run completed");
          ws.close();
          break;
      }
    };

    ws.onclose = () => console.log("❌ WebSocket closed");

    return () => ws.close();
  }, [isRunning, stepsPerTestCase, onRunFinished]);

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
      background: '#FFFFFF',
      borderRadius: 12,
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      padding: '24px',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      color: '#111827',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h2 style={{
          margin: 0,
          fontSize: '18px',
          fontWeight: 600,
          color: '#111827'
        }}>
          Test Run in Progress
        </h2>
        <div style={{
          fontSize: '14px',
          color: '#4B5563',
          background: '#F3F4F6',
          padding: '4px 8px',
          borderRadius: '4px',
          fontWeight: 500
        }}>
          {planName} {metricName && `• ${metricName}`} {testCaseName && `• ${testCaseName}`}
        </div>
      </div>
      
      <p style={{
        margin: '0 0 16px 0',
        fontSize: '14px',
        color: '#4B5563'
      }}>
        Executing test cases
      </p>
      
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
            background: runStatus === "FAILED" ? "#FEF2F2" : "#ECFDF5",
            border: `1px solid ${runStatus === "FAILED" ? "#EF4444" : "#10B981"}`,
            borderRadius: "10px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
          }}
        >
          <span
            style={{
              color: runStatus === "FAILED" ? "#991B1B" : "#065F46",
              fontWeight: 600,
              fontSize: "14px",
            }}
          >
            {runStatus === "FAILED" ? "Run failed" : "Completed successfully"}
          </span>

          <button
            onClick={() => runName && navigate(`/test-runs/${encodeURIComponent(runName)}`)}
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
            View Details
          </button>
        </div>
      )}
    </div>
  );
};

export default Loop;
