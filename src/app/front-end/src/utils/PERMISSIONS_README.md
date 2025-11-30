# Role-Based Access Control (RBAC) Implementation

## Overview
This application implements role-based access control with four user roles, each with specific permissions.

## User Roles

### 1. Admin Role
**Permissions:**
- ✅ Manage user list (view users)
- ✅ Create users
- ✅ Update users
- ✅ Delete users

**UI Visibility:**
- "User's List" menu item is visible in Sidebar
- Full access to Users page (`/users`)

### 2. Manager Role
**Permissions:**
- Create tables
- Update tables
- Delete tables

**UI Visibility:**
- "User's List" menu item is hidden
- Access to table management features (to be implemented in specific pages)

### 3. Curator Role
**Permissions:**
- Create records
- Update records

**UI Visibility:**
- "User's List" menu item is hidden
- Access to record creation/editing features (to be implemented in specific pages)

### 4. Viewer Role
**Permissions:**
- Export data (if available)

**UI Visibility:**
- "User's List" menu item is hidden
- Read-only access with export capabilities (to be implemented in specific pages)

## Implementation Details

### Files Created/Modified

1. **`src/utils/permissions.ts`**
   - Defines role permissions
   - Provides utility functions: `getRolePermissions()`, `hasPermission()`, `isAdmin()`, etc.

2. **`src/hooks/usePermissions.ts`**
   - React hooks for easy permission checking in components
   - `usePermissions(role)` - Get all permissions for a role
   - `useHasPermission(role, permission)` - Check specific permission

3. **`src/components/Sidebar.tsx`**
   - Updated to conditionally show menu items based on role
   - "User's List" only visible to Admin role

4. **`src/pages/Users.tsx`**
   - Added role-based access protection
   - Redirects non-admin users
   - "Create User" button only visible to users with `canCreateUser` permission

## Usage Examples

### Check Permission in Component
```typescript
import { hasPermission } from "@/utils/permissions";

const userRole = "admin";
if (hasPermission(userRole, "canManageUsers")) {
  // Show admin features
}
```

### Use Permission Hook
```typescript
import { useHasPermission } from "@/hooks/usePermissions";

const MyComponent = ({ userRole }) => {
  const canCreate = useHasPermission(userRole, "canCreateUser");
  
  return (
    <>
      {canCreate && <CreateButton />}
    </>
  );
};
```

### Filter Menu Items
```typescript
const navItems = [
  { 
    icon: Users, 
    label: "User's List", 
    path: "/users",
    requiredPermission: "canManageUsers" // Only visible to Admin
  },
];

// Filter items based on permissions
const visibleItems = navItems.filter(item => {
  if (!item.requiredPermission) return true;
  return hasPermission(userRole, item.requiredPermission);
});
```

## Extending Permissions

To add role-based access to other pages:

1. Import the permission utilities:
```typescript
import { hasPermission } from "@/utils/permissions";
```

2. Check permissions before rendering:
```typescript
{hasPermission(userRole, "canCreateRecords") && (
  <CreateButton />
)}
```

3. Protect routes by checking permissions in useEffect:
```typescript
useEffect(() => {
  if (!hasPermission(userRole, "requiredPermission")) {
    navigate("/dashboard");
    toast({ title: "Access Denied", ... });
  }
}, [userRole]);
```

## Permission Names Reference

- `canManageUsers` - Admin only
- `canCreateUser` - Admin only
- `canUpdateUser` - Admin only
- `canDeleteUser` - Admin only
- `canCreateTables` - Manager only
- `canUpdateTables` - Manager only
- `canDeleteTables` - Manager only
- `canCreateRecords` - Curator only
- `canUpdateRecords` - Curator only
- `canExportData` - Viewer only

## Notes

- Role names are case-insensitive (admin, Admin, ADMIN all work)
- Default permissions are the most restrictive (no access)
- All permission checks should be done on both frontend and backend for security


