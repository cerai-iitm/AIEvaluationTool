import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import ceraiLogo from "@/assets/cerai-logo.png";
import iitLogo from "@/assets/iit-logo.png";
import iitBackground from "@/assets/iit-background.jpeg";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";

import {Eye, EyeOff} from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setshowPassword] = useState(false);

  const getToastColor = (variant) => {
    switch(variant) {
      case "success": return "bg-green-500 text-white";
      case "destructive": return "bg-red-500 text-white";
      default: return "bg-blue-500 text-white";
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      toast({
        title: "Error",
        description: "Please enter both username and password",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.LOGIN, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_name: username,
          password: password,
        }),
      });

      const data = await response.json();

      if (response.ok && data.Status) {
        // Store the access token in localStorage
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_name", username);
        
        toast({
          title: "Success",
          description: data.message || "Login successful",
          variant: "success",
        });
        
        // Navigate to dashboard
        navigate("/dashboard");
      } else {
        toast({
          title: "Error",
          description: data.detail || "Login failed",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server. Please try again." + error,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b px-8 py-4 flex items-center justify-between">
        <img src={ceraiLogo} alt="CeRAI Logo" className="h-12" />
        <img src={iitLogo} alt="IIT Madras Logo" className="h-14" />
      </header>

      <div className="flex-1 relative flex items-center justify-center">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: `url(${iitBackground})`,
            filter: 'brightness(0.7)'
          }}
        />
        
        <div className="relative z-10 bg-white/65 backdrop-blur-sm rounded-lg shadow-2xl p-10 w-full max-w-lg mx-4"
        style = {{
            bottom: "-10%",
            left: "40%",
            transform: "translateX(-50%)",

        }}
        >
          <h1 className="text-3xl font-bold text-center mb-8 text-foreground">
            Test Data Management System
          </h1>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-base font-medium">
                User Name :
              </Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="h-12"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-base font-medium">
                Password :
              </Label>
              <div  className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-12 pr-10"
                  required
                />
                <button
                  type = "button"
                  onClick={() => setshowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className = "h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex justify-center pt-4">
              <Button 
                type="submit" 
                disabled={isLoading}
                className="bg-accent hover:bg-accent/90 text-accent-foreground px-12 py-6 text-lg font-medium"
              >
                {isLoading ? "Logging in..." : "Login"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
