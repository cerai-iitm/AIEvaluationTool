import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import ceraiLogo from "@/assets/cerai-logo.png";
import iitLogo from "@/assets/iit-logo.png";
import iitBackground from "@/assets/iit-background.jpeg";

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Simple validation - in production, this would authenticate with backend
    if (username && password) {
      navigate("/dashboard");
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
            Welcome to AI Evaluation Tool Data
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
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12"
                required
              />
            </div>

            <div className="flex justify-center pt-4">
              <Button 
                type="submit" 
                className="bg-accent hover:bg-accent/90 text-accent-foreground px-12 py-6 text-lg font-medium"
              >
                Login
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
