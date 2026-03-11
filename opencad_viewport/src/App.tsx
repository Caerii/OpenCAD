import { useEffect, useMemo, useState } from "react";
import { OpenCadApiClient } from "./api/client";
import { ChatPanel } from "./components/ChatPanel";
import { FeatureTreePanel } from "./components/FeatureTreePanel";
import { SketchEditor } from "./components/SketchEditor";
import { Viewport3D } from "./components/Viewport3D";
import { mockFeatureTree, mockMeshes, mockSketch } from "./mock/mockData";
import type { ChatOperationExecution, FeatureNodeView, FeatureTreeView, MeshPayload, SketchPayload } from "./types";

function getLatestGeneratedNodeId(
  previousTree: FeatureTreeView,
  nextTree: FeatureTreeView,
  operations: ChatOperationExecution[],
): string | null {
  for (let index = operations.length - 1; index >= 0; index -= 1) {
    const result = operations[index].result;
    const featureId = typeof result.feature_id === "string" ? result.feature_id : null;
    if (featureId && nextTree.nodes[featureId]) {
      return featureId;
    }
  }

  const newNodeIds = Object.keys(nextTree.nodes).filter((nodeId) => !previousTree.nodes[nodeId]);
  for (let index = newNodeIds.length - 1; index >= 0; index -= 1) {
    const nodeId = newNodeIds[index];
    if (nextTree.nodes[nodeId]?.shape_id) {
      return nodeId;
    }
  }

  return newNodeIds.length > 0 ? newNodeIds[newNodeIds.length - 1] : null;
}

function createFallbackMesh(node: FeatureNodeView, index: number): MeshPayload {
  const template = mockMeshes[index % mockMeshes.length];
  const offset = (index + 1) * 8;

  return {
    shapeId: node.shape_id ?? node.id,
    name: node.name,
    vertices: Array.from(template.vertices, (value, vertexIndex) => {
      if (vertexIndex % 3 === 0) {
        return value + offset;
      }
      if (vertexIndex % 3 === 1) {
        return value + offset * 0.35;
      }
      return value;
    }),
    faces: Array.from(template.faces),
    normals: template.normals ? Array.from(template.normals) : undefined,
  };
}

export default function App(): JSX.Element {
  const api = useMemo(() => new OpenCadApiClient(), []);
  const [tree, setTree] = useState<FeatureTreeView>(mockFeatureTree);
  const [meshes, setMeshes] = useState<MeshPayload[]>(mockMeshes);
  const [sketch, setSketch] = useState<SketchPayload>(mockSketch);
  const [selectedNodeId, setSelectedNodeId] = useState<string>(tree.root_id);

  const selectedShapeId = tree.nodes[selectedNodeId]?.shape_id ?? null;
  const selectedNode = tree.nodes[selectedNodeId] ?? null;
  const sketchMode = Boolean(selectedNode?.sketch_id) || selectedNode?.operation === "add_sketch";

  useEffect(() => {
    const missingShapeNodes = Object.values(tree.nodes).filter(
      (node) =>
        node.status === "built"
        && !node.suppressed
        && Boolean(node.shape_id)
        && !meshes.some((mesh) => mesh.shapeId === node.shape_id),
    );

    if (missingShapeNodes.length === 0) {
      return;
    }

    let cancelled = false;

    void Promise.all(
      missingShapeNodes.map(async (node, index) => {
        try {
          return await api.getMesh(node.shape_id as string);
        } catch {
          return createFallbackMesh(node, index);
        }
      }),
    ).then((loadedMeshes) => {
      if (cancelled) {
        return;
      }

      setMeshes((current) => {
        const knownShapeIds = new Set(current.map((mesh) => mesh.shapeId));
        return [...current, ...loadedMeshes.filter((mesh) => !knownShapeIds.has(mesh.shapeId))];
      });
    });

    return () => {
      cancelled = true;
    };
  }, [api, meshes, tree]);

  return (
    <div className="app-shell">
      <FeatureTreePanel
        tree={tree}
        selectedNodeId={selectedNodeId}
        onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
      />

      <main className="workspace">
        <Viewport3D
          meshes={meshes}
          selectedShapeId={selectedShapeId}
          onSelectShape={(shapeId) => {
            const node = Object.values(tree.nodes).find((item) => item.shape_id === shapeId);
            if (node) {
              setSelectedNodeId(node.id);
            }
          }}
        />
        <SketchEditor
          active={sketchMode}
          sketch={sketch}
          solveSketch={(payload) => api.solveSketch(payload)}
          onSketchChange={(updated) => setSketch(updated)}
        />
      </main>

      <ChatPanel
        onSend={async (request) => {
          const response = await api.sendChat({
            ...request,
            tree_state: tree,
          });
          setTree(response.new_tree_state);
          const latestNodeId = getLatestGeneratedNodeId(tree, response.new_tree_state, response.operations_executed);
          if (latestNodeId) {
            setSelectedNodeId(latestNodeId);
          }
          return {
            response: response.response,
            operations: response.operations_executed
          };
        }}
      />
    </div>
  );
}
