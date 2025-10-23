import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { X } from "lucide-react";

interface User {
  username: string;
  email: string;
  role: string;
}

const Users = () => {
  const navigate = useNavigate();
  const [showCreateUser, setShowCreateUser] = useState(false);

  const users: User[] = [
    { username: "UserName", email: "eamil@iitm.ac.in", role: "Admin" },
    { username: "Manger22", email: "eamilmanager@iitm.ac.in", role: "Manager" },
    { username: "Manger44", email: "eamilmanager22@iitm.ac.in", role: "Manager" },
    { username: "CuratorUser", email: "eamilcurator@iitm.ac.in", role: "Curator" },
    { username: "CuratorUser22", email: "eamilcurator22@iitm.ac.in", role: "Curator" },
    { username: "CuratorUser44", email: "eamilcurator42@iitm.ac.in", role: "Curator" },
    { username: "Viewer24", email: "eamilviwer@iitm.ac.in", role: "Viewer" },
    { username: "Viewer27", email: "eamilviwer22@iitm.ac.in", role: "Viewer" },
    { username: "Viewer22", email: "eamilviwer42@iitm.ac.in", role: "Viewer" },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 bg-background">
        <div className="p-8">
          <h1 className="text-4xl font-bold mb-12 text-center">User's List</h1>

          <div className="max-w-5xl mx-auto bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="border-b-2">
                <tr>
                  <th className="text-left p-6 font-semibold text-lg">User Name</th>
                  <th className="text-left p-6 font-semibold text-lg">Email Address</th>
                  <th className="text-left p-6 font-semibold text-lg">Roll</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user, index) => (
                  <tr
                    key={index}
                    className="border-b hover:bg-muted/50 cursor-pointer"
                    onClick={() => navigate(`/user-history/${user.username}`)}
                  >
                    <td className="p-6">{user.username}</td>
                    <td className="p-6">{user.email}</td>
                    <td className="p-6">{user.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-8 max-w-5xl mx-auto">
            <Button
              className="bg-primary hover:bg-primary/90"
              onClick={() => setShowCreateUser(true)}
            >
              + Add User
            </Button>
          </div>
        </div>
      </main>

      <Dialog open={showCreateUser} onOpenChange={setShowCreateUser}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-3xl font-bold text-center">Create User</DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-4 top-4"
              onClick={() => setShowCreateUser(false)}
            >
              <X className="w-5 h-5" />
            </Button>
          </DialogHeader>

          <form className="space-y-6 pt-8">
            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="username" className="text-right font-semibold">
                User Name :
              </Label>
              <Input id="username" className="bg-muted" />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="email" className="text-right font-semibold">
                Email Address :
              </Label>
              <Input id="email" type="email" className="bg-muted" />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="role" className="text-right font-semibold">
                User Roll :
              </Label>
              <Input id="role" className="bg-muted" />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="password" className="text-right font-semibold">
                Password :
              </Label>
              <Input id="password" type="password" className="bg-muted" />
            </div>

            <div className="grid grid-cols-[200px_1fr] items-center gap-4">
              <Label htmlFor="confirm-password" className="text-right font-semibold">
                Confirm Password :
              </Label>
              <Input id="confirm-password" type="password" className="bg-muted" />
            </div>

            <div className="flex justify-center pt-6">
              <Button type="submit" className="bg-primary hover:bg-primary/90 px-12">
                Submit
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Users;
