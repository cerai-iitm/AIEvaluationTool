import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";

interface PageHeaderWithBackProps {
  title: string;
}

export const PageHeaderWithBack = ({ title }: PageHeaderWithBackProps) => {
  const navigate = useNavigate();

  return (
    <div className="mb-4 grid gap-3 md:mb-8 md:grid-cols-[1fr_auto_1fr] md:items-center">
      <Button
        type="button"
        variant="normal"
        className="w-fit justify-self-start"
        onClick={() => navigate("/dashboard")}
      >
        <ArrowLeft />
        Back
      </Button>
      <h1 className="text-center text-2xl font-bold md:text-4xl">{title}</h1>
      <div aria-hidden="true" className="hidden md:block" />
    </div>
  );
};
