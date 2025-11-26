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
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { API_ENDPOINTS } from "@/config/api";

interface Language {
  lang_id: number;
  lang_name: string;
}

const LanguageList: React.FC = () => {
  const { toast } = useToast();
  const [languages, setLanguages] = useState<Language[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isUpdateDialogOpen, setIsUpdateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(
    null,
  );
  const [languageName, setLanguageName] = useState("");

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

  const fetchLanguages = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.LANGUAGES_V2, {
        headers: authHeaders(),
      });
      if (!response.ok) throw new Error("Failed to fetch languages");
      const data = await response.json();
      setLanguages(data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch languages.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [authHeaders, toast]);

  useEffect(() => {
    fetchLanguages();
  }, [fetchLanguages]);

  const handleAddClick = () => {
    setLanguageName("");
    setIsAddDialogOpen(true);
  };

  const handleUpdateClick = (language: Language) => {
    setSelectedLanguage(language);
    setLanguageName(language.lang_name);
    setIsUpdateDialogOpen(true);
  };

  const handleDeleteClick = (language: Language) => {
    setSelectedLanguage(language);
    setIsDeleteDialogOpen(true);
  };

  const handleSave = async (isUpdate: boolean) => {
    const endpoint = isUpdate
      ? API_ENDPOINTS.LANGUAGE_UPDATE_V2(selectedLanguage!.lang_id)
      : API_ENDPOINTS.LANGUAGE_CREATE_V2;
    const method = isUpdate ? "PUT" : "POST";

    if (!languageName.trim()) {
      toast({
        title: "Validation Error",
        description: "Language name is required",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(endpoint, {
        method,
        headers: authHeaders(),
        body: JSON.stringify({ lang_name: languageName.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save language");
      }

      toast({
        title: "Success",
        description: `Language ${isUpdate ? "updated" : "created"} successfully`,
      });

      setIsAddDialogOpen(false);
      setIsUpdateDialogOpen(false);
      fetchLanguages();
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
    if (!selectedLanguage) return;
    setIsSubmitting(true);
    try {
      const response = await fetch(
        API_ENDPOINTS.LANGUAGE_DELETE_V2(selectedLanguage.lang_id),
        {
          method: "DELETE",
          headers: authHeaders(),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete language");
      }

      toast({
        title: "Success",
        description: "Language deleted successfully",
      });

      setIsDeleteDialogOpen(false);
      fetchLanguages();
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

  const filteredLanguages = languages.filter((lang) =>
    lang.lang_name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const totalItems = filteredLanguages.length;
  const itemsPerPage = 20;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

  const paginatedLanguages = filteredLanguages.slice(
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
            Languages
          </h1>

          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <Input
              placeholder="Search languages..."
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
                        Language ID
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-left text-xs md:text-base">
                        Language Name
                      </th>
                      <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-right text-xs md:text-base">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedLanguages.length === 0 ? (
                      <tr>
                        <td
                          colSpan={3}
                          className="p-4 text-center text-muted-foreground"
                        >
                          No languages found
                        </td>
                      </tr>
                    ) : (
                      paginatedLanguages.map((row) => (
                        <tr
                          key={row.lang_id}
                          className="border-b hover:bg-muted/50 transition-colors"
                        >
                          <td className="p-2 text-left text-xs md:text-base">
                            {row.lang_id}
                          </td>
                          <td className="p-2 text-left text-xs md:text-base">
                            {row.lang_name}
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
              + Add Language
            </Button>
          </div>
        </div>
      </main>

      <Dialog
        open={isAddDialogOpen || isUpdateDialogOpen}
        onOpenChange={
          isAddDialogOpen ? setIsAddDialogOpen : setIsUpdateDialogOpen
        }
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isUpdateDialogOpen ? "Update Language" : "Add New Language"}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="languageName">Language Name</Label>
            <Input
              id="languageName"
              value={languageName}
              onChange={(e) => setLanguageName(e.target.value)}
              placeholder="Enter language name"
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

      <AlertDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              language.
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

export default LanguageList;
