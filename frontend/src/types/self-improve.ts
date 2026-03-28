export interface Cycle {
  id: string;
  status:
    | 'idle'
    | 'planning'
    | 'architecting'
    | 'developing'
    | 'testing'
    | 'reviewing'
    | 'documenting'
    | 'awaiting_approval'
    | 'merging'
    | 'integrating'
    | 'completed'
    | 'rejected'
    | 'failed';
  budget_usd: number;
  spent_usd: number;
  max_improvements: number;
  focus_areas: string[] | null;
  improvements: Improvement[];
  agents_spawned: number;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface GateCheck {
  name: string;
  passed: boolean;
  message: string;
  severity: string;
}

export interface GateResult {
  gate: string;
  verdict: 'pass' | 'fail' | 'warn';
  checks: GateCheck[];
  summary: string;
  retry_count: number;
  run_at: string;
  duration_ms: number;
}

export interface Improvement {
  id: string;
  cycle_id: string;
  title: string;
  description: string;
  priority: number;
  category: 'performance' | 'ux' | 'tests' | 'refactor' | 'feature' | 'docs';
  status:
    | 'proposed'
    | 'approved'
    | 'in_progress'
    | 'testing'
    | 'review'
    | 'documenting'
    | 'awaiting_approval'
    | 'approved_by_human'
    | 'rejected_by_human'
    | 'merged'
    | 'failed';
  worktree_path: string | null;
  branch_name: string | null;
  diff_summary: string | null;
  diff_stat: string | null;
  test_results: {
    passed: number;
    failed: number;
    errors: number;
    output: string;
  } | null;
  review_notes: string | null;
  security_scan: {
    passed: boolean;
    issues: string[];
  } | null;
  pr_description: string | null;
  agent_id: string | null;
  gate_results?: GateResult[];
  created_at: string;
  updated_at: string;
}

export interface SquadAgent {
  id: string;
  cycle_id: string;
  improvement_id: string | null;
  agent_id: string;
  role: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  output_summary: string | null;
}

export interface SquadRole {
  role: string;
  name: string;
  description: string;
  stage: string;
}

export type CycleStatus = Cycle['status'];
export type ImprovementStatus = Improvement['status'];
export type ImprovementCategory = Improvement['category'];
