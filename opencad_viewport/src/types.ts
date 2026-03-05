export type FeatureNodeStatus = "pending" | "built" | "failed" | "stale" | "suppressed";

export type ParameterType = "int" | "float" | "bool" | "string" | "shape_ref" | "json";

export interface TypedParameter {
  type: ParameterType;
  value: unknown;
}

export interface ParameterBinding {
  parameter: string;
  source: "solver" | "node";
  source_key: string;
  source_path: string;
  cast_as?: ParameterType | null;
  expression?: string | null;
}

export interface FeatureNodeView {
  id: string;
  name: string;
  operation: string;
  parameters: Record<string, unknown>;
  typed_parameters: Record<string, TypedParameter>;
  parameter_bindings: ParameterBinding[];
  sketch_id?: string | null;
  depends_on: string[];
  shape_id?: string | null;
  status: FeatureNodeStatus;
  suppressed: boolean;
}

export interface FeatureTreeView {
  nodes: Record<string, FeatureNodeView>;
  root_id: string;
  active_branch: string;
  revision: number;
}

export interface MeshPayload {
  shapeId: string;
  vertices: number[] | Float32Array;
  faces: number[] | Uint32Array;
  normals?: number[] | Float32Array;
  name?: string;
}

export interface SketchPoint {
  id: string;
  type: "point";
  x: number;
  y: number;
}

export interface SketchLine {
  id: string;
  type: "line";
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface SketchCircle {
  id: string;
  type: "circle";
  cx: number;
  cy: number;
  radius: number;
}

export type SketchEntity = SketchPoint | SketchLine | SketchCircle;

export interface SketchConstraint {
  id: string;
  type: string;
  a: string;
  b?: string;
  value?: number;
}

export interface SketchPayload {
  entities: Record<string, SketchEntity>;
  constraints: SketchConstraint[];
}

export interface SolverResult {
  status: "SOLVED" | "OVERCONSTRAINED" | "UNDERCONSTRAINED";
  sketch: SketchPayload;
  conflict_constraint_id?: string | null;
  max_residual?: number;
  message?: string;
}

export interface ChatOperationExecution {
  tool: string;
  status: "ok" | "error";
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface ChatResponsePayload {
  response: string;
  operations_executed: ChatOperationExecution[];
  new_tree_state: FeatureTreeView;
}

export interface TreeSnapshotPayload {
  version: number;
  created_at: string;
  tree: FeatureTreeView;
}
