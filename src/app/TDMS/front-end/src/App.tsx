import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import { isAuthenticated, parseUrlTokens } from "./utils/auth";
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

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter basename={routerBasename}>
        {parseUrlTokens()}
        <Routes>
          <Route path="/" element={isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Login />} />
          <Route path="/*" element={isAuthenticated() ? <AuthenticatedApp /> : <Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
