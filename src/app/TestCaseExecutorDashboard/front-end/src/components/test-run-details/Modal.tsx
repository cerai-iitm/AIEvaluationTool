import React, { useState, useEffect } from 'react'
import { API_ENDPOINTS } from "../../config/api";
import { redirectToLogin } from "../../utils/auth";
interface ModalProps {
  conversationId: number | null;
}

interface FullConversationData {
  user_prompt: string | null;
  system_prompt: string | null;
  agent_response: string | null;
  testcase_name: string | null;
  conversation_id?: number | null;
  score: number | null;
  reason: string | null;
  target: string | null;
}

const ScoreIndicator = ({ score }: { score: number | null }) => {
  if (score === null) {
    return (
      <div className="d-flex flex-column align-items-center">
        <div 
          className="rounded-circle d-flex align-items-center justify-content-center bg-light border"
          style={{ 
            width: '120px', 
            height: '120px', 
            borderWidth: '3px',
            borderColor: '#dee2e6'
          }}
        >
          <div className="text-center">
            <div className="text-muted fw-semibold" style={{ fontSize: '18px' }}>--</div>
            <div className="text-muted small" style={{ fontSize: '12px' }}>No Score</div>
          </div>
        </div>
      </div>
    );
  }

  const roundedScore = Math.round(score * 100) / 100;
  const percentage = score * 100;

  return (
    <div className="d-flex flex-column align-items-center">
      <div className="position-relative" style={{ width: '120px', height: '120px' }}>
        <svg width="120" height="120" className="transform -rotate-90">
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="#e9ecef"
            strokeWidth="12"
          />
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="#6c757d"
            strokeWidth="12"
            strokeDasharray={`${percentage * 3.39} 339`}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="position-absolute top-50 start-50 translate-middle text-center">
          <div className="fw-bold" style={{ fontSize: '28px', color: '#495057' }}>{roundedScore.toFixed(2)}</div>
        </div>
      </div>
      <div className="mt-2 text-center">
        <div className="fw-semibold" style={{ color: '#6c757d', fontSize: '14px' }}>Score</div>
      </div>
    </div>
  );
};

const ReasonCard = ({ score, reason }: { score: number | null; reason: string | null }) => {
  if (!reason) return null;

  return (
    <div className="card border-0 bg-light" style={{ borderRadius: '12px' }}>
      <div className="card-body">
        <div className="d-flex align-items-start">
          <div className="flex-grow-1">
            <h6 className="card-title mb-2 fw-semibold">Evaluation Reason</h6>
            <p className="card-text mb-0 text-secondary" style={{ lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>{reason}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

function Modal({ conversationId }: ModalProps) {
  const [data, setData] = useState<FullConversationData>({
    user_prompt: null,
    system_prompt: null,
    agent_response: null,
    testcase_name: null,
    conversation_id: null,
    target: null,
    score: null,
    reason: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    if (!conversationId) return;
    const fetchData = async () => {
        setLoading(true);
        setError(null);

        try {
        const res = await fetch(API_ENDPOINTS.GET_CONVERSATION(conversationId.toString()), {
          headers: getAuthHeaders(),
          credentials: "include",
        });
        if (res.status === 401) {
          redirectToLogin();
          throw new Error("Unauthorized");
        }
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const json: FullConversationData = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [conversationId]);

  return (
     <div
        className="modal fade"
        id="conversationModal"
        tabIndex={-1}
        aria-labelledby="conversationModalLabel"
        aria-hidden="true"
        >
        <div className="modal-dialog modal-xl modal-dialog-scrollable">
            <div className="modal-content">
            
            <div className="modal-header">
                <h5 className="modal-title" id="conversationModalLabel">
                Test Evaluation Details
                </h5>
                <button
                type="button"
                className="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
                />
            </div>

            <div className="modal-body">
                {loading ? (
                    <div className="text-center py-5">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                    </div>
                ) : error ? (
                    <div className="alert alert-danger">
                        Error: {error}
                    </div>
                ) : (
                    <div>
                        {/* Primary Evaluation Section */}
                        <div className="row mb-4">
                            <div className="col-lg-3 col-md-4 text-center mb-3 mb-md-0">
                                <ScoreIndicator score={data.score} />
                            </div>
                            <div className="col-lg-9 col-md-8">
                                <ReasonCard score={data.score} reason={data.reason} />
                            </div>
                        </div>

                        {/* Metadata Section */}
                        <div className="border-top pt-3 mb-4">
                            <div className="row g-2 text-muted small">
                                <div className="col-lg-4 col-md-6 col-12 mb-2 mb-md-0">
                                    <span className="fw-semibold">Conversation ID:</span> {data.conversation_id || "N/A"}
                                </div>
                                <div className="col-lg-4 col-md-6 col-12 mb-2 mb-md-0">
                                    <span className="fw-semibold">Testcase:</span> {data.testcase_name || "N/A"}
                                </div>
                                <div className="col-lg-4 col-12">
                                    <span className="fw-semibold">Target Model:</span> {data.target || "N/A"}
                                </div>
                            </div>
                        </div>

                        {/* Full Conversation Details */}
                        <div className="border-top pt-4">
                            <h6 className="fw-semibold mb-4">Full Conversation</h6>
                            
                            <div className="row">
                                <div className="col-12">
                                    <div className="mb-4">
                                        <div className="d-flex align-items-center mb-2">
                                            <div className="me-2">
                                                <div className="rounded-circle bg-primary d-flex align-items-center justify-content-center" style={{ width: '24px', height: '24px' }}>
                                                    <span className="text-white fw-semibold" style={{ fontSize: '12px' }}>U</span>
                                                </div>
                                            </div>
                                            <h6 className="mb-0 fw-semibold">User Prompt</h6>
                                        </div>
                                        <div className="ms-4">
                                            <pre className="bg-light border-0 p-3 rounded text-wrap" style={{ whiteSpace: "pre-wrap", fontSize: '14px', lineHeight: '1.5' }}>
                                                {data.user_prompt || "No user prompt"}
                                            </pre>
                                        </div>
                                    </div>
                                    
                                    <div className="mb-4">
                                        <div className="d-flex align-items-center mb-2">
                                            <div className="me-2">
                                                <div className="rounded-circle bg-secondary d-flex align-items-center justify-content-center" style={{ width: '24px', height: '24px' }}>
                                                    <span className="text-white fw-semibold" style={{ fontSize: '12px' }}>S</span>
                                                </div>
                                            </div>
                                            <h6 className="mb-0 fw-semibold">System Prompt</h6>
                                        </div>
                                        <div className="ms-4">
                                            <pre className="bg-light border-0 p-3 rounded text-wrap" style={{ whiteSpace: "pre-wrap", fontSize: '14px', lineHeight: '1.5' }}>
                                                {data.system_prompt || "No system prompt"}
                                            </pre>
                                        </div>
                                    </div>
                                    
                                    <div className="mb-4">
                                        <div className="d-flex align-items-center mb-2">
                                            <div className="me-2">
                                                <div className="rounded-circle bg-success d-flex align-items-center justify-content-center" style={{ width: '24px', height: '24px' }}>
                                                    <span className="text-white fw-semibold" style={{ fontSize: '12px' }}>A</span>
                                                </div>
                                            </div>
                                            <h6 className="mb-0 fw-semibold">Agent Response</h6>
                                        </div>
                                        <div className="ms-4">
                                            <pre className="bg-light border-0 p-3 rounded text-wrap" style={{ whiteSpace: "pre-wrap", fontSize: '14px', lineHeight: '1.5' }}>
                                                {data.agent_response || "No response available"}
                                            </pre>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="modal-footer">
                <button
                type="button"
                className="btn btn-secondary"
                data-bs-dismiss="modal"
                >
                Close
                </button>
            </div>

            </div>
        </div>
        </div>
  )
}

export default Modal
