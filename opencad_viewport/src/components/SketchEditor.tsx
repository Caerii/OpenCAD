import { useEffect, useMemo, useState } from "react";
import type { SketchConstraint, SketchPayload, SolverResult } from "../types";

interface SketchEditorProps {
  active: boolean;
  sketch: SketchPayload | null;
  onSketchChange?: (sketch: SketchPayload) => void;
  solveSketch: (sketch: SketchPayload) => Promise<SolverResult>;
}

function iconForConstraint(type: string): string {
  switch (type) {
    case "horizontal":
      return "H";
    case "vertical":
      return "V";
    case "parallel":
      return "||";
    case "coincident":
      return "C";
    case "distance":
      return "D";
    default:
      return "*";
  }
}

export function SketchEditor({ active, sketch, onSketchChange, solveSketch }: SketchEditorProps): JSX.Element | null {
  const [localSketch, setLocalSketch] = useState<SketchPayload | null>(sketch);
  const [solveMessage, setSolveMessage] = useState("Idle");

  useEffect(() => {
    setLocalSketch(sketch);
  }, [sketch]);

  useEffect(() => {
    if (!active || !localSketch) {
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      const result = await solveSketch(localSketch);
      if (!cancelled) {
        setSolveMessage(`${result.status}: ${result.message ?? ""}`.trim());
      }
    }, 120);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [active, localSketch, solveSketch]);

  const constraintRows = useMemo(() => {
    if (!localSketch) {
      return [] as SketchConstraint[];
    }
    return localSketch.constraints;
  }, [localSketch]);

  if (!active || !localSketch) {
    return null;
  }

  const toSvgX = (value: number): number => value * 4 + 160;
  const toSvgY = (value: number): number => 120 - value * 4;

  return (
    <div className="sketch-overlay">
      <div className="sketch-header">
        <strong>Sketch Editor</strong>
        <span>{solveMessage}</span>
      </div>
      <svg viewBox="0 0 320 240" className="sketch-canvas">
        {Object.values(localSketch.entities).map((entity) => {
          if (entity.type === "line") {
            return (
              <line
                key={entity.id}
                x1={toSvgX(entity.x1)}
                y1={toSvgY(entity.y1)}
                x2={toSvgX(entity.x2)}
                y2={toSvgY(entity.y2)}
                stroke="#0f172a"
                strokeWidth="1.5"
              />
            );
          }

          if (entity.type === "circle") {
            return (
              <circle
                key={entity.id}
                cx={toSvgX(entity.cx)}
                cy={toSvgY(entity.cy)}
                r={Math.max(2, entity.radius * 4)}
                fill="none"
                stroke="#0f172a"
                strokeWidth="1.5"
              />
            );
          }

          return (
            <circle key={entity.id} cx={toSvgX(entity.x)} cy={toSvgY(entity.y)} r={2.8} fill="#0f172a" />
          );
        })}

        {localSketch.constraints.map((constraint) => {
          const anchor = localSketch.entities[constraint.a];
          if (!anchor) {
            return null;
          }
          const x = anchor.type === "line" ? toSvgX((anchor.x1 + anchor.x2) / 2) : anchor.type === "circle" ? toSvgX(anchor.cx) : toSvgX(anchor.x);
          const y = anchor.type === "line" ? toSvgY((anchor.y1 + anchor.y2) / 2) : anchor.type === "circle" ? toSvgY(anchor.cy) : toSvgY(anchor.y);
          return (
            <text key={constraint.id} x={x + 5} y={y - 5} className="constraint-icon">
              {iconForConstraint(constraint.type)}
            </text>
          );
        })}
      </svg>
      <div className="constraint-grid">
        {constraintRows.map((constraint) => (
          <label key={constraint.id} className="constraint-row">
            <span>{constraint.id}</span>
            <span>{constraint.type}</span>
            <input
              type="number"
              value={constraint.value ?? 0}
              disabled={constraint.value === undefined}
              onChange={(event) => {
                if (constraint.value === undefined || !localSketch) {
                  return;
                }
                const nextValue = Number(event.target.value);
                const updated: SketchPayload = {
                  ...localSketch,
                  constraints: localSketch.constraints.map((item) =>
                    item.id === constraint.id ? { ...item, value: nextValue } : item
                  )
                };
                setLocalSketch(updated);
                onSketchChange?.(updated);
              }}
            />
          </label>
        ))}
      </div>
    </div>
  );
}
