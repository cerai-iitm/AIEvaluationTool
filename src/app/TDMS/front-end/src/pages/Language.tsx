import React, { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import  {Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import  {Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { API_ENDPOINTS } from '@/config/api';
import { hasPermission } from '@/utils/permissions';
import { HistoryButton } from "@/components/HistoryButton";


interface Language {
    lang_id: number;
    lang_name: string;
}

const itemsPerPage = 20;

const LanguageList: React.FC = () => {
    const { toast } = useToast();
    const [currentUserRole, setCurrentUserRole] = useState<string>("");
    const [languages, setLanguages] = useState<Language[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);

    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showUpdateModal, setShowUpdateModal] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(null);
    const [addOpen, setAddOpen] = useState(false);

    // Add - Dialog local state
    const [newLanguageName, setNewLanguageName] = useState("");

    // Update - Dialog local state
    const [updateName, setUpdateName] = useState("");

    const [highlightedRowId, setHighlightedRowId] = useState<number | null>(null);

    // Fetch languages from API
    const fetchLanguages = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem("access_token");
            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(API_ENDPOINTS.LANGUAGES_V2, {
                method: "GET",
                headers,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            // Map API response to match our interface
            const mappedLanguages: Language[] = data.map((lang: any) => ({
                lang_id: lang.lang_id,
                lang_name: lang.lang_name
            }));
            setLanguages(mappedLanguages);
        } catch (error) {
            console.error("Error fetching languages:", error);
            toast({
                title: "Error",
                description: "Failed to fetch languages. Please try again.",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        const fetchUserRole = async () => {
            try {
                const token = localStorage.getItem("access_token");
                if (!token) return;

                const response = await fetch(API_ENDPOINTS.CURRENT_USER, {
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                });

                if (response.ok) {
                    const userData = await response.json();
                    setCurrentUserRole(userData.role || "");
                }
            } catch (error) {
                console.error("Error fetching user role:", error);
            }
        };

        fetchUserRole();
        fetchLanguages();
    }, []);

    useEffect(() => {
        if (selectedLanguage) {
            setUpdateName(selectedLanguage.lang_name);
        }
    }, [selectedLanguage]);

    // Filter and pagination data
    const filteredLanguages = languages.filter(lang => 
        lang.lang_name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    const totalItems = filteredLanguages.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

    const paginatedLanguages = filteredLanguages.slice(
        (currentPage -1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    // Create language handler
    const handleAddLanguage = async () => {
        if (!newLanguageName.trim()) {
            toast({
                title: "Validation Error",
                description: "Language name is required",
                variant: "destructive",
            });
            return;
        }

        try {
            const token = localStorage.getItem("access_token");
            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(API_ENDPOINTS.LANGUAGE_CREATE_V2, {
                method: "POST",
                headers,
                body: JSON.stringify({
                    lang_name: newLanguageName.trim()
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            toast({
                title: "Success",
                description: "Language created successfully",
                variant: "default",
            });
            
            setAddOpen(false);
            setNewLanguageName("");
            fetchLanguages(); // Refresh the list
            setHighlightedRowId(data.lang_id);
        } catch (error: any) {
            console.error("Error creating language:", error);
            toast({
                title: "Error",
                description: error.message || "Failed to create language. Please try again.",
                variant: "destructive",
            });
        }
    };

    // Update language handler
    const handleUpdate = async () => {
        if (!selectedLanguage || !updateName.trim()) {
            toast({
                title: "Validation Error",
                description: "Language name is required",
                variant: "destructive",
            });
            return;
        }

        try {
            const token = localStorage.getItem("access_token");
            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(API_ENDPOINTS.LANGUAGE_UPDATE_V2(selectedLanguage.lang_id), {
                method: "PUT",
                headers,
                body: JSON.stringify({
                    lang_name: updateName.trim()
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            toast({
                title: "Success",
                description: "Language updated successfully",
                variant: "default",
            });
            
            setShowUpdateModal(false);
            setSelectedLanguage(null);
            fetchLanguages(); // Refresh the list
        } catch (error: any) {
            console.error("Error updating language:", error);
            toast({
                title: "Error",
                description: error.message || "Failed to update language. Please try again.",
                variant: "destructive",
            });
        }
    };

    // Delete language handler
    const handleDelete = async () => {
        if (!selectedLanguage) return;

        try {
            const token = localStorage.getItem("access_token");
            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(API_ENDPOINTS.LANGUAGE_DELETE_V2(selectedLanguage.lang_id), {
                method: "DELETE",
                headers,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            toast({
                title: "Success",
                description: "Language deleted successfully",
                variant: "default",
            });
            
            setShowDeleteConfirm(false);
            setShowEditDialog(false);
            setSelectedLanguage(null);
            fetchLanguages(); // Refresh the list
            setHighlightedRowId(null);
        } catch (error: any) {
            console.error("Error deleting language:", error);
            toast({
                title: "Error",
                description: error.message || "Failed to delete language. Please try again.",
                variant: "destructive",
            });
        }
    };

    const handleRowClick = (lang: Language) => {
        setSelectedLanguage(lang);
        setShowEditDialog(true);
    };

    const handleDeleteClick = () => {
        setShowDeleteConfirm(true);
    };

    return (
        <div className="flex min-h-screen">
            {/* Sidebar */}
            <aside className="fixed top-0 left-0 h-screen w-[220px] bg-[#5252c2] z-20">
                <Sidebar />
            </aside>

            {/* Main content */}
            <main className="flex-1 bg-background ml-[220px] md:ml-[224px]">
                <div className="p-4 md:p-8 flex flex-col h-screen">
                    <h1 className="text-2xl md:text-4xl font-bold mb-4 md:mb-8 text-center">Languages</h1>

                    {/* Filter/Search Bar */}
                    <div className="flex flex-col sm:flex-row gap-4 mb-6">
                        <Select defaultValue="Language Name">
                            <SelectTrigger className="w-full sm:w-48">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="Language Name">Language Name</SelectItem>
                            </SelectContent>
                        </Select>
                    <Input
                            placeholder="search"
                            value={searchQuery}
                            onChange={e => {
                                setCurrentPage(1); 
                                setSearchQuery(e.target.value);
                            }}
                            className="w-full sm:w-64"
                        />
                        <div className="ml-auto flex items-center gap-2 md:gap-4">
                            <HistoryButton
                                entityType="Language"
                                title="Languages"
                                idField="languageId"
                                idLabel="Language ID"
                            />
                            <span className="text-xs sm:text-sm text-muted-foreground">
                                {totalItems ? `${(currentPage - 1) * itemsPerPage + 1} - ${Math.min(currentPage * itemsPerPage, totalItems)} of ${totalItems}` : "0"}
                            </span>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                disabled={currentPage === 1}
                            >
                                <ChevronLeft className="w-4 h-4 md:w-5 md:h-5" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                disabled={currentPage === totalPages}
                            >
                                <ChevronRight className="w-4 h-4 md:w-5 md:h-5" />
                            </Button>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="flex-1 min-h-0 overflow-y-auto">
                        <div className="bg-white rounded-lg shadow overflow-hidden max-h-[67vh] max-w-[60vh] overflow-y-auto">
                            {isLoading ? (
                                <div className="flex items-center justify-center p-8">
                                    <span>Loading...</span>
                                </div>
                            ) : (
                                <table className="w-full min-w-[400px]">
                                    <thead className="border-b-2">
                                        <tr>
                                            <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-center text-xs md:text-base">Language ID</th>
                                            <th className="sticky top-0 bg-white z-10 p-2 md:p-4 font-semibold text-left text-xs md:text-base">Language Name</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {paginatedLanguages.length === 0 ? (
                                            <tr>
                                                <td colSpan={2} className="p-4 text-center text-muted-foreground">
                                                    No languages found
                                                </td>
                                            </tr>
                                        ) : (
                                            paginatedLanguages.map(lang => (
                                                <tr 
                                                    key={lang.lang_id} 
                                                    className={`border-b cursor-pointer transition-colors duration-200 ${
                                                        highlightedRowId === lang.lang_id ? "bg-primary/10 hover:bg-primary/15 border-primary/30" : "hover:bg-muted/50"
                                                    }`}
                                                    onClick={() => {handleRowClick(lang); setHighlightedRowId(lang.lang_id);}}
                                                >
                                                    <td className="p-2 text-center text-xs md:text-base">{lang.lang_id}</td>
                                                    <td className="p-2 text-xs md:text-base">{lang.lang_name}</td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            )}
                        </div>
                        {/* Add Language Button */}
                        {(hasPermission(currentUserRole, "canCreateTables") || 
                          hasPermission(currentUserRole, "canCreateRecords")) && (
                            <div className="mt-4 md:mt-6 sticky bottom-5 ">
                                <button 
                                    className="bg-primary hover:bg-primary/90 text-white py-2 px-4 rounded text-sm md:text-base transition-colors" 
                                    onClick={() => setAddOpen(true)}
                                >
                                    + Add Language
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </main>

            {/* Edit Dialog - Similar to Domains.tsx */}
            {showEditDialog && selectedLanguage && (
                <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
                    <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-md">
                        <button 
                            type="button" 
                            className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
                            onClick={() => {
                                setShowEditDialog(false);
                                setSelectedLanguage(null);
                            }}
                        >
                            ×
                        </button>
                        <div className="flex items-center justify-center mb-6 md:mb-7 mt-4 md:mt-5">
                            <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Language Name :</label>
                            <span className="text-sm md:text-base">{selectedLanguage.lang_name}</span>
                        </div>
                        <div className="flex gap-4 md:gap-8 justify-center">
                            {hasPermission(currentUserRole, "canDeleteTables") && (
                                <button
                                    className="px-6 md:px-8 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm md:text-base transition-colors"
                                    onClick={handleDeleteClick}
                                >
                                    Delete
                                </button>
                            )}
                            {(hasPermission(currentUserRole, "canUpdateTables") || 
                              hasPermission(currentUserRole, "canUpdateRecords")) && (
                                <button
                                    className="px-6 md:px-8 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm md:text-base transition-colors"
                                    onClick={() => {
                                        setShowEditDialog(false);
                                        setShowUpdateModal(true);
                                    }}
                                >
                                    <p className="text-white px-2.5">Edit</p>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Dialog */}
            {showDeleteConfirm && selectedLanguage && (
                <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
                    <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-md">
                        <button 
                            type="button" 
                            className="absolute top-3 right-4 w-6 h-6 flex items-center justify-center rounded-full bg-gray-200 hover:bg-gray-300 transition-colors" 
                            onClick={() => setShowDeleteConfirm(false)}
                        >
                            <X className="w-4 h-4" />
                        </button>
                        <div className="mt-4 md:mt-6">
                            <p className="text-base md:text-lg font-semibold mb-4 text-center">
                                Are you sure you want to delete the following language? This action cannot be undone.
                            </p>
                            <div className="mb-6">
                                <p className="text-sm md:text-base">
                                    <span className="font-semibold">Language Name :</span> {selectedLanguage.lang_name}
                                </p>
                            </div>
                            <div className="flex gap-4 justify-center">
                                <button
                                    className="px-6 md:px-8 py-2 bg-gray-400 hover:bg-gray-500 text-white rounded text-sm md:text-base transition-colors"
                                    onClick={() => setShowDeleteConfirm(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="px-6 md:px-8 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm md:text-base transition-colors"
                                    onClick={handleDelete}
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Update Modal */}
            {showUpdateModal && selectedLanguage && (
                <div className="fixed inset-0 flex items-center justify-center bg-black/20 z-50 p-4">
                    <div className="relative bg-white rounded-lg shadow-xl px-4 md:px-8 pt-6 md:pt-8 pb-4 md:pb-6 w-full max-w-lg min-h-[220px]">
                        <button 
                            type="button" 
                            className="absolute top-3 right-4 text-2xl font-bold hover:text-gray-600 transition-colors" 
                            onClick={() => {
                                setShowUpdateModal(false);
                                setSelectedLanguage(null);
                            }}
                        >
                            ×
                        </button>
                        <div className="flex flex-col md:flex-row items-center mb-6 md:mb-8 mt-4 md:mt-5 gap-2 md:gap-0">
                            <label className="font-semibold text-base md:text-lg min-w-[140px] md:min-w-[165px]">Language Name :</label>
                            <input
                                value={updateName}
                                onChange={e => setUpdateName(e.target.value)}
                                className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                            />
                        </div>
                        <div className="flex justify-center">
                            <button
                                className={`px-6 md:px-8 py-2 rounded text-sm md:text-base font-semibold shadow transition-colors ${
                                    updateName.trim() 
                                        ? "bg-green-600 hover:bg-green-700 text-white cursor-pointer" 
                                        : "bg-green-300 text-white cursor-not-allowed"
                                }`}
                                disabled={!updateName.trim()}
                                onClick={handleUpdate}
                            >
                                Submit
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Language Dialog */}
            {addOpen && (
                <Dialog open={addOpen} onOpenChange={setAddOpen}>
                    <DialogContent className="w-full max-w-md p-4">
                        {/* <DialogHeader>
                            <DialogTitle>Add Language</DialogTitle>
                        </DialogHeader> */}
                        <div className="flex flex-col gap-6 ">
                            <div className="flex flex-col md:flex-row items-center mb-6 md:mb-8 mt-4 md:mt-5 gap-2 md:gap-0 mt-4 pt-4">
                                <Label className='font-semibold tet-base md:text-lg min-w-[140px] md:min-w-[165px]'>Language Name</Label>
                                <Input 
                                    value={newLanguageName} 
                                    onChange={e => setNewLanguageName(e.target.value)} 
                                    placeholder="Enter language name..." 
                                    maxLength={100} 
                                    className="bg-gray-100 rounded border border-gray-300 px-3 md:px-4 py-2 text-sm md:text-lg flex-1 w-full md:w-auto focus:outline-none focus:ring focus:ring-blue-200"
                                />
                            </div>
                            <div className="flex justify-center">
                                <Button onClick={handleAddLanguage} disabled={!newLanguageName.trim()}
                                className={`px-6 md:px-8 py-2 rounded text-sm md:text-base font-semibold shadow transition-colors 
                                    }`}
                                >
                                    Submit
                                </Button>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
            )}
        </div>
    );
};

export default LanguageList;
