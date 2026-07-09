import { Routes, Route } from "react-router-dom";
import React, { useState, useEffect } from "react";

import "./App.css";
import LoginPage from "./components/Login/LoginPage";
import TestRunsPage from "./components/test-runs/TestRunsPage";
import TestRunDetails from "./components/test-run-details/TestRunDetailsPage";
import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";
import Sidebar from "./components/common/sidebar/sidebar";
import Analysis from "./components/Analysis/Analysis";
import { clearSession, hasSharedLogoutSignal, parseUrlTokens, redirectToLogin } from "./utils/auth";


function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleSharedLogout = () => {
      if (hasSharedLogoutSignal()) {
        setIsAuthenticated(false);
        redirectToLogin();
      }
    };

    window.addEventListener("focus", handleSharedLogout);
    document.addEventListener("visibilitychange", handleSharedLogout);
    const intervalId = window.setInterval(handleSharedLogout, 1000);

    return () => {
      window.removeEventListener("focus", handleSharedLogout);
      document.removeEventListener("visibilitychange", handleSharedLogout);
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    if (parseUrlTokens()) {
      setIsAuthenticated(true);
      setLoading(false);
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      redirectToLogin();
      return;
    }

    // Validate token with backend
    const tdmsBaseUrl =
      process.env.REACT_APP_TDMS_API_BASE_URL || "/tdms-api";
    const validateToken = async () => {
      try {
        const response = await fetch(`${tdmsBaseUrl}/api/users/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          credentials: "include",
        });

        if (!response.ok) {
          clearSession();
          setIsAuthenticated(false);
          setLoading(false);
          redirectToLogin();
          return;
        }
        setIsAuthenticated(true);
      } catch (error) {
        setIsAuthenticated(false);
        redirectToLogin();
      } finally {
        setLoading(false);
      }
    };

    validateToken();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  const AuthenticatedApp = () => (
    <div className="app-container">
      <div className="sidebar">
        <Sidebar onLogout={() => setIsAuthenticated(false)} />
      </div>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<TestRunsPage />} />
          <Route path="/test-runs/:runName" element={<TestRunDetails />} />
          <Route path="/create-test-run" element={<NewTestRunPage />} />
          <Route path="/continue-run/:runName" element={<ContinueRunPage />} />
          <Route path="/__dev/config" element={<DevConfigPage />} />
          <Route path="/analyse/:runName" element={<Analysis/>} />
        </Routes>
      </main>
    </div>
  );

  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage />}
      />
      <Route
        path="/*"
        element={
          isAuthenticated ? <AuthenticatedApp /> : <LoginPage />
        }
      />
    </Routes>
  );
}

export default App;
