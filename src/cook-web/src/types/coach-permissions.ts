/**
 * GET /api/portal/permissions 的类型定义（P0 权限下发）。
 *
 * 后端契约（P0-EXECUTION-7-ROUTES.md §2.3）：
 *   GET /api/portal/permissions
 *   → make_common_response 解包后的 data：
 *     { roles: [{role_bid, name}], permissions: string[], data_scope: string }
 *
 * 后端实现：src/api/flaskr/service/learning_portal/routes.py
 * （resolve_user_roles / get_user_permissions / visible_students_scope）。
 */

/** 单个角色（已按 ROLE_PRIORITY 排序）。 */
export interface PortalRole {
  role_bid: string;
  name: string;
}

/** GET /api/portal/permissions 响应 data（request 层解包后）。 */
export interface PortalPermissions {
  /** 当前用户全部角色（主角色在前）。 */
  roles: PortalRole[];
  /** 权限 key 并集（含 “all”；admin 已展开为 12 key 全集）。 */
  permissions: string[];
  /**
   * 数据范围字符串：
   *  "all" | "department:<dept>" | "mentored:<user_bid>" | "self:<user_bid>"
   */
  data_scope: string;
}
