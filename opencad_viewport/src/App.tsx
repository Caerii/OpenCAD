import { useMemo, useState } from "react";
import { OpenCadApiClient } from "./api/client";
import { ChatPanel } from "./components/ChatPanel";
import { FeatureTreePanel } from "./components/FeatureTreePanel";
import { SketchEditor } from "./components/SketchEditor";
import { Viewport3D } from "./components/Viewport3D";
import { mockFeatureTree, mockMeshes, mockSketch } from "./mock/mockData";
import type { FeatureTreeView, SketchPayload } from "./types";

export default function App(): JSX.Element {
  const api = useMemo(() => new OpenCadApiClient(), []);
  const [tree, setTree] = useState<FeatureTreeView>(mockFeatureTree);
  const [meshes] = useState(mockMeshes);
  const [sketch, setSketch] = useState<SketchPayload>(mockSketch);
  const [selectedNodeId, setSelectedNodeId] = useState<string>(tree.root_id);

  const selectedShapeId = tree.nodes[selectedNodeId]?.shape_id ?? null;
  const selectedNode = tree.nodes[selectedNodeId] ?? null;
  const sketchMode = Boolean(selectedNode?.sketch_id) || selectedNode?.operation === "add_sketch";

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
        onSend={async (message, reasoning) => {
          const response = await api.sendChat({
            message,
            tree_state: tree,
            conversation_history: [],
            reasoning
          });
          setTree(response.new_tree_state);
          return {
            response: response.response,
            operations: response.operations_executed
          };
        }}
      />
    </div>
  );
}
