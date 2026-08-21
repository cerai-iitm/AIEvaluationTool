import { useEffect } from "react";
import { getLoginUrl, getTdmsReturnUrl } from "@/utils/auth";

const Login = () => {
  useEffect(() => {
    window.location.href = getLoginUrl();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="bg-white p-6 rounded-lg shadow-lg text-center">
        <h2 className="text-xl font-semibold">Redirecting to central login...</h2>
        <p className="mt-2 text-sm text-slate-600">If redirect does not happen, 
          <button className="text-blue-600 underline" 
            onClick={() => window.location.href = getLoginUrl(getTdmsReturnUrl())}>
            click here
            </button>.
        </p>
      </div>
    </div>
  );
};

export default Login;
