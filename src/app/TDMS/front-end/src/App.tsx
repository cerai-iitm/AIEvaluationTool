import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./App.css";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import { getValidAccessToken, hasSharedLogoutSignal, parseUrlTokens, redirectToLogin } from "./utils/auth";
import { API_ENDPOINTS } from "./config/api";
import Sidebar from "./components/Sidebar";
import TestCases from "./pages/TestCases";
import Responses from "./pages/Responses";
import Users from "./pages/Users";
import UserHistory from "./pages/UserHistory";
import NotFound from "./pages/NotFound";
import Targets from "./pages/Targets";
import Prompts from "./pages/Prompts";
import DomainList from "./pages/Domains";
import StrategyList from "./pages/Strategies";
import LlmPrompts from "./pages/LlmPrompts";
import LanguageList from "./pages/Language";
import TestPlans from "./pages/TestPlans";
import Metrics from "./pages/Metrics";


const queryClient = new QueryClient();
const routerBasename = import.meta.env.BASE_URL;

const AuthenticatedApp = () => (
  <div className="app-container">
    <div className="sidebar">
      <Sidebar />
    </div>

    <main className="main-content">
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/test-cases" element={<TestCases />} />
        <Route path="/targets" element={<Targets />} />
        <Route path="/responses" element={<Responses />} />
        <Route path="/prompts" element={<Prompts />} />
        <Route path="/domains" element={<DomainList />} />
        <Route path="/strategies" element={<StrategyList />} />
        <Route path="/llm-prompts" element={<LlmPrompts />} />
        <Route path="/languages" element={<LanguageList />} />
        <Route path="/users" element={<Users />} />
        <Route path="/test-plans" element={<TestPlans />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/user-history/:username" element={<UserHistory />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </main>
  </div>
);

const AuthGate = () => {
  const [isAllowed, setIsAllowed] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const validateAuth = async () => {
      const token = await getValidAccessToken(API_ENDPOINTS.REFRESH);

      if (!isMounted) return;

      if (!token) {
        redirectToLogin();
        return;
      }

      setIsAllowed(true);
      setIsChecking(false);
    };

    validateAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const handleSharedLogout = () => {
      if (hasSharedLogoutSignal()) {
        redirectToLogin();
      }
    };

    handleSharedLogout();
    window.addEventListener("focus", handleSharedLogout);
    document.addEventListener("visibilitychange", handleSharedLogout);
    const intervalId = window.setInterval(handleSharedLogout, 1000);

    return () => {
      window.removeEventListener("focus", handleSharedLogout);
      document.removeEventListener("visibilitychange", handleSharedLogout);
      window.clearInterval(intervalId);
    };
  }, []);

  if (isChecking) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return isAllowed ? <AuthenticatedApp /> : null;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter basename={routerBasename}>
        {parseUrlTokens()}
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<AuthGate />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
