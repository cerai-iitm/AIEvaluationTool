import { useMemo } from "react";
import { getRolePermissions, hasPermission, type RolePermissions } from "@/utils/permissions";

/**
 * Hook to get permissions for the current user role
 */
export function usePermissions(role: string): RolePermissions {
  return useMemo(() => getRolePermissions(role), [role]);
}

/**
 * Hook to check if user has a specific permission
 */
export function useHasPermission(role: string, permission: keyof RolePermissions): boolean {
  return useMemo(() => hasPermission(role, permission), [role, permission]);
}


