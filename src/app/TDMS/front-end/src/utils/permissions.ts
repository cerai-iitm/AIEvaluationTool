/**
 * Role-based permissions utility
 * Defines permissions for each user role in the application
 */

export type UserRole = "admin" | "manager" | "curator" | "user";

export interface RolePermissions {
  // User Management
  canManageUsers: boolean;
  canCreateUser: boolean;
  canUpdateUser: boolean;
  canDeleteUser: boolean;
  
  // Table Management
  canCreateTables: boolean;
  canUpdateTables: boolean;
  canDeleteTables: boolean;
  
  // Record Management
  canCreateRecords: boolean;
  canUpdateRecords: boolean;
  
  // Data Export
  canExportData: boolean;
}

/**
 * Get permissions for a specific role
 */
export function getRolePermissions(role: string): RolePermissions {
  const normalizedRole = role.toLowerCase() as UserRole;
  
  switch (normalizedRole) {
    case "admin":
      return {
        canManageUsers: true,
        canCreateUser: true,
        canUpdateUser: true,
        canDeleteUser: true,
        canCreateTables: true,
        canUpdateTables: true,
        canDeleteTables: true,
        canCreateRecords: false,
        canUpdateRecords: false,
        canExportData: false,
      };
    
    case "manager":
      return {
        canManageUsers: false,
        canCreateUser: false,
        canUpdateUser: false,
        canDeleteUser: false,
        canCreateTables: true,
        canUpdateTables: true,
        canDeleteTables: true,
        canCreateRecords: false,
        canUpdateRecords: false,
        canExportData: false,
      };
    
    case "curator":
      return {
        canManageUsers: false,
        canCreateUser: false,
        canUpdateUser: false,
        canDeleteUser: false,
        canCreateTables: true,
        canUpdateTables: true,
        canDeleteTables: false,
        canCreateRecords: true,
        canUpdateRecords: true,
        canExportData: false,
      };
    
    case "user":
      return {
        canManageUsers: false,
        canCreateUser: false,
        canUpdateUser: false,
        canDeleteUser: false,
        canCreateTables: false,
        canUpdateTables: false,
        canDeleteTables: false,
        canCreateRecords: false,
        canUpdateRecords: false,
        canExportData: true,
      };
    
    default:
      // Default to most restrictive permissions
      return {
        canManageUsers: false,
        canCreateUser: false,
        canUpdateUser: false,
        canDeleteUser: false,
        canCreateTables: false,
        canUpdateTables: false,
        canDeleteTables: false,
        canCreateRecords: false,
        canUpdateRecords: false,
        canExportData: false,
      };
  }
}

/**
 * Check if a user has a specific permission
 */
export function hasPermission(role: string, permission: keyof RolePermissions): boolean {
  const permissions = getRolePermissions(role);
  return permissions[permission];
}

/**
 * Check if user is admin
 */
export function isAdmin(role: string): boolean {
  return role.toLowerCase() === "admin";
}

/**
 * Check if user is manager
 */
export function isManager(role: string): boolean {
  return role.toLowerCase() === "manager";
}

/**
 * Check if user is curator
 */
export function isCurator(role: string): boolean {
  return role.toLowerCase() === "curator";
}

/**
 * Check if user is viewer
 */
export function isUser(role: string): boolean {
  return role.toLowerCase() === "user";
}

/**
 * Get list of roles that a user can view history for
 * Based on RBAC rules:
 * - admin can view history of: admin, manager, curator, viewer
 * - manager can view history of: manager, curator, viewer
 * - curator can view history of: curator, viewer
 * - viewer cannot view history at all
 */
export function getViewableRoles(userRole: string): string[] {
  const normalizedRole = userRole.toLowerCase();
  
  switch (normalizedRole) {
    case "admin":
      return ["admin", "manager", "curator", "viewer", "user"]; // Include "user" for backward compatibility
    case "manager":
      return ["manager", "curator", "viewer", "user"];
    case "curator":
      return ["curator", "viewer", "user"];
    case "viewer":
    case "user":
      return []; // Viewers cannot view history
    default:
      return [];
  }
}

/**
 * Check if a user can view history based on their role
 */
export function canViewHistory(userRole: string): boolean {
  const normalizedRole = userRole.toLowerCase();
  return normalizedRole !== "viewer" && normalizedRole !== "user";
}

/**
 * Check if an activity's role is viewable by the current user
 */
export function canViewActivity(currentUserRole: string, activityRole: string): boolean {
  const viewableRoles = getViewableRoles(currentUserRole);
  const normalizedActivityRole = activityRole.toLowerCase();
  // Handle backward compatibility: "user" should be treated as "viewer"
  const roleToCheck = normalizedActivityRole === "user" ? "viewer" : normalizedActivityRole;
  return viewableRoles.some(role => role.toLowerCase() === roleToCheck);
}


