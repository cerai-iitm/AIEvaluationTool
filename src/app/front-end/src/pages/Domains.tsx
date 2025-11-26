import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ChevronLeft, ChevronRight, X, Loader2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";

interface Domain {
  domain_id: number;
  domain_name: string;
}

const DomainList: React.FC = () => {
  const { toast } = useToast();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isUpdateDialogOpen, setIsUpdateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [domainName, setDomainName] = useState("");

  const authHeaders = useCallback((): HeadersInit => {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }, []);

  const fetchDomains = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.DOMAINS_V2, {
        headers: authHeaders(),
      });
      if (!response.ok) throw new Error("Failed to fetch domains");
      const data = await response.json();
      setDomains(data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch domains.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [authHeaders, toast]);

  useEffect(() => {
    fetchDomains();
  }, [fetchDomains]);

  const handleAddClick = () => {
    setDomainName("");
    setIsAddDialogOpen(true);
  };

  const handleUpdateClick = (domain: Domain) => {
    setSelectedDomain(domain);
    setDomainName(domain.domain_name);
    setIsUpdateDialogOpen(true);
  };

  const handleDeleteClick = (domain: Domain) => {
    setSelectedDomain(domain);
    setIsDeleteDialogOpen(true);
  };

  const handleSave = async (isUpdate: boolean) => {
    const endpoint = isUpdate
      ? API_ENDPOINTS.DOMAIN_UPDATE_V2(selectedDomain!.domain_id)
      : API_ENDPOINTS.DOMAIN_CREATE_V2;
    const method = isUpdate ? "PUT" : "POST";

    if (!domainName.trim()) {
      toast({
        title: "Validation Error",
        description: "Domain name is required",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(endpoint, {
        method,
        headers: authHeaders(),
        body: JSON.stringify({ domain_name: domainName.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save domain");
      }

      toast({
        title: "Success",
        description: `Domain ${isUpdate ? "updated" : "created"} successfully`,
      });

      setIsAddDialogOpen(false);
      setIsUpdateDialogOpen(false);
      fetchDomains();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedDomain) return;
    setIsSubmitting(true);
    try {
      const response = await fetch(
        API_ENDPOINTS.DOMAIN_DELETE_V2(selectedDomain.domain_id),
        {
          method: "DELETE",
          headers: authHeaders(),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete domain");
      }

      toast({
        title: "Success",
        description: "Domain deleted successfully",
      });

      setIsDeleteDialogOpen(false);
      fetchDomains();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredDomains = domains.filter((domain) =>
    domain.domain_name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const totalItems = filteredDomains.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

  const paginatedDomains = filteredDomains.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  return (
    <div className="flex min-h-screen">
      <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
        <Sidebar />
      </aside>

      <main className="flex-1 bg-background ml-[220px] md:ml-[224px]">
        <div className="p-4 md:p-8 flex flex-col h-screen">
          <h1 className="text-2xl md:text-4xl font-bold mb-4 md:mb-8 text-center">
            Domains
          </h1>

          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <Input
              placeholder="Search domains..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full sm:w-64"
            />
            <div className="ml-auto flex items-center gap-2 md:gap-4">
              <span className="text-xs sm:text-sm text-muted-foreground">
                {totalItems === 0
                  ? "0"
                  : `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(
                      currentPage * itemsPerPage,
                      totalItems,
                    )} of ${totalItems}`}
              </span>
              <div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-4 h-4 md:w-5 md:h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-4 h-4 md:w-5 md:h-5" />
                </Button>
              </div>
            </div>
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {isLoading ? (
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="w-8 h-8 animate-spin" />
                </div>
              ) : (
                <table className="w-full min-w-[400px]">
                  <thead className="border-b-2">
                    <tr>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-left text-xs md:text-base">
                        Domain ID
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-left text-xs md:text-base">
                        Domain Name
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-right text-xs md:text-base">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedDomains.length === 0 ? (
                      <tr>
                        <td
                          colSpan={3}
                          className="p-4 text-center text-muted-foreground"
                        >
                          No domains found
                        </td>
                      </tr>
                    ) : (
                      paginatedDomains.map((row) => (
                        <tr
                          key={row.domain_id}
                          className="border-b hover:bg-muted/50 transition-colors"
                        >
                          <td className="p-2 text-left text-xs md:text-base">
                            {row.domain_id}
                          </td>
                          <td className="p-2 text-left text-xs md:text-base">
                            {row.domain_name}
                          </td>
                          <td className="p-2 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUpdateClick(row)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-destructive hover:text-destructive/80"
                              onClick={() => handleDeleteClick(row)}
                            >
                              Delete
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              )}
            </div>
          </div>
          <div className="mt-4 md:mt-6 sticky bottom-5">
            <Button
              className="bg-primary hover:bg-primary/90"
              onClick={handleAddClick}
            >
              + Add Domain
            </Button>
          </div>
        </div>
      </main>

      {/* Add/Edit Dialog */}
      <Dialog
        open={isAddDialogOpen || isUpdateDialogOpen}
        onOpenChange={
          isAddDialogOpen ? setIsAddDialogOpen : setIsUpdateDialogOpen
        }
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isUpdateDialogOpen ? "Update Domain" : "Add New Domain"}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="domainName">Domain Name</Label>
            <Input
              id="domainName"
              value={domainName}
              onChange={(e) => setDomainName(e.target.value)}
              placeholder="Enter domain name"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() =>
                isAddDialogOpen
                  ? setIsAddDialogOpen(false)
                  : setIsUpdateDialogOpen(false)
              }
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleSave(isUpdateDialogOpen)}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Save"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              domain.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive hover:bg-destructive/90"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default DomainList;
