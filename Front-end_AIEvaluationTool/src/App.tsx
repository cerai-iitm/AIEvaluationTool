import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import TestCases from "./pages/TestCases";
import Responses from "./pages/Responses";
import Users from "./pages/Users";
import UserHistory from "./pages/UserHistory";
import NotFound from "./pages/NotFound";
import Targets from "./pages/Targets";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/test-cases" element={<TestCases />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/responses" element={<Responses />} />
          <Route path="/users" element={<Users />} />
          <Route path="/user-history/:username" element={<UserHistory />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
