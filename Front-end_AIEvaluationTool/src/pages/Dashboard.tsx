import { useNavigate } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { MoreVertical } from "lucide-react";

interface StatCard {
  title: string;
  count: number;
  onClick?: () => void;
}

const Dashboard = () => {
  const navigate = useNavigate();

  const stats: StatCard[] = [
    { title: "Test cases", count: 1635, onClick: () => navigate("/test-cases") },
    { title: "Targets", count: 534 },
    { title: "Domains", count: 6 },
    { title: "Strategies", count: 44 },
    { title: "Languages", count: 9 },
    { title: "Responses", count: 288 },
    { title: "Prompts", count: 407 },
    { title: "LLM Prompts", count: 20 },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      
      <main className="flex-1 p-12">
        <div className="grid grid-cols-3 gap-8 max-w-6xl">
          {stats.map((stat) => (
            <Card
              key={stat.title}
              className={`relative shadow-lg hover:shadow-xl transition-shadow ${
                stat.onClick ? "cursor-pointer" : ""
              }`}
              onClick={stat.onClick}
            >
              <button className="absolute top-4 right-4 text-muted-foreground hover:text-foreground">
                <MoreVertical className="w-5 h-5" />
              </button>
              
              <CardContent className="pt-8 pb-8 text-center">
                <h3 className="text-xl font-semibold mb-4">{stat.title}</h3>
                <p className="text-5xl font-bold">{stat.count.toString().padStart(3, '0')}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
