import { useEffect } from "react";
import { AUTH_PAGE_URL } from "@/config/api";

const Login = () => {
  useEffect(() => {
    const appBase = import.meta.env.BASE_URL.replace(/\/$/, "");
    const returnUrl = `${window.location.origin}${appBase}/dashboard`;
    window.location.href = `${AUTH_PAGE_URL}?return_url=${encodeURIComponent(returnUrl)}`;
    // window.location.href = `${AUTH_PAGE_URL}`;
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="bg-white p-6 rounded-lg shadow-lg text-center">
        <h2 className="text-xl font-semibold">Redirecting to central login...</h2>
        <p className="mt-2 text-sm text-slate-600">If redirect does not happen, <button className="text-blue-600 underline" onClick={() => window.location.href = `${AUTH_PAGE_URL}`}>click here</button>.</p>
      </div>
    </div>
  );
};

export default Login;
