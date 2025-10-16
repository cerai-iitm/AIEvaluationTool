import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from "@/components/Sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { MoreVertical } from "lucide-react";

const MENU_OPTIONS = [
  { label: "Open", action: "open" },
  { label: "Add test case", action: "addTestCase" },
  { label: "Export", action: "export" },
  { label: "History", action: "history" },
  { label: "Delete", action: "delete", className: "text-red-600" }
];

const statCardHandlers = (navigate, stat) => ({
  open: () => stat.onClick && stat.onClick(),
  addTestCase: () => alert(`Add test case for ${stat.title}`),
  export: () => alert(`Export ${stat.title}`),
  history: () => alert(`Show history for ${stat.title}`),
  delete: () => alert(`Delete ${stat.title}`),
});

const Dashboard = () => {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(null);

  const stats = [
    { title: "Test cases", count: 1635, onClick: () => navigate("/test-cases") },
    { title: "Targets", count: 534, onClick: () => navigate("/targets") },
    { title: "Domains", count: 6 },
    { title: "Strategies", count: 44 },
    { title: "Languages", count: 9 },
    { title: "Responses", count: 288, onClick: () => navigate("/responses") },
    { title: "Prompts", count: 407, onClick: () => navigate("/prompts") },
    { title: "LLM Prompts", count: 20 },

  ];

  return (
    <>
      <div className="flex min-h-screen">
          {/* Sidebar: fixed width and position */}
          <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
            <Sidebar />
          </aside>
        <main className="flex-1 p-12 ml-[240px]">
          <div className="grid grid-cols-3 gap-8 max-w-6xl">
            {stats.map((stat, idx) => (
              <Card
                key={stat.title}
                className={`relative shadow-lg hover:shadow-xl transition-shadow ${stat.onClick ? "cursor-pointer" : ""}`}
                onClick={() => stat.onClick && stat.onClick()}
              >
                <button
                  className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent triggering card click
                    setMenuOpen(menuOpen === idx ? null : idx); // Toggle menu for this card
                  }}
                >
                  <MoreVertical className="w-5 h-5" />
                </button>
                {menuOpen === idx && (
                  <div className="absolute top-12 right-4 z-10 bg-white border rounded shadow-lg flex flex-col min-w-[150px]">
                    {MENU_OPTIONS.map(opt => (
                      <button
                        key={opt.label}
                        className={`px-4 py-2 text-left hover:bg-gray-100 ${opt.className || ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          statCardHandlers(navigate, stat)[opt.action]();
                          setMenuOpen(null);
                        }}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                <CardContent className="pt-8 pb-8 text-center">
                  <h3 className="text-xl font-semibold mb-4">{stat.title}</h3>
                  <p className="text-5xl font-bold">{stat.count.toString().padStart(3, '0')}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    </>
  );
};

export default Dashboard;
