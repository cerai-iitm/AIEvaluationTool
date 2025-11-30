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
        canCreateTables: false,
        canUpdateTables: false,
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


