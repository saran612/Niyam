export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "regional_officer" | "bureau_officer" | "committee" | "institution" | "admin";
  region_id?: number | null;
  institution_id?: number | null;
}

export interface Obligation {
  id: number;
  application_id?: number | null;
  institution_id: number;
  region_id: number;
  obligation_type: "STAGE_SLA" | "EVC_REPORT" | "UNDERTAKING" | "LEASE_EXPIRY" | "DEFICIENCY_RECTIFICATION";
  title: string;
  description?: string;
  stage_key?: string;
  owner_id?: number | null;
  owner_role: string;
  status: "PENDING" | "SUBMITTED" | "SATISFIED" | "BREACHED" | "WAIVED";
  due_at: string;
  satisfied_at?: string | null;
  created_at: string;
}

export interface Application {
  id: number;
  application_number: string;
  institution_id: number;
  region_id: number;
  academic_year: string;
  current_stage: string;
  status: string;
  suggested_action?: string | null;
  created_at: string;
  updated_at: string;
  obligations?: Obligation[];
}

export interface AuditLogItem {
  id: number;
  prev_hash: string;
  hash: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id?: number | null;
  payload: Record<string, any>;
  timestamp: string;
}

export interface ClockStatus {
  current_time: string;
  offset_seconds: number;
}
