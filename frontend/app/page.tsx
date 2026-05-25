"use client";

import { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, Edge, Node } from "reactflow";
import "reactflow/dist/style.css";
import { AgentCount, ChainStatus, Receipt } from "../lib/types";
import { Badge, Card } from "./components/ui";

const API = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

export default function DashboardPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [status, setStatus] = useState<ChainStatus | null>(null);
  const [agents, setAgents] = useState<AgentCount[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    const load = async () => {
      const [r1, r2, r3] = await Promise.all([
        fetch(`${API}/receipts`).then((r) => r.json()),
        fetch(`${API}/chain/status`).then((r) => r.json()),
        fetch(`${API}/agents`).then((r) => r.json()),
      ]);
      setReceipts(r1);
      setStatus(r2);
      setAgents(r3);
      if (selectedId === null && r1.length > 0) {
        setSelectedId(r1[0].id);
      }
    };

    load();
    const timer = setInterval(load, 2000);
    return () => clearInterval(timer);
  }, [selectedId]);

  const selectedReceipt = receipts.find((r) => r.id === selectedId) ?? null;
  const firstError = status?.errors[0] ?? null;
  const failedReceiptIds = new Set(
    (status?.receipts ?? []).filter((r) => !r.ok).map((r) => r.id)
  );

  const graph = useMemo(() => {
    const nodes: Node[] = receipts.map((r, idx) => ({
      id: r.receipt_hash,
      position: { x: 120 + idx * 180, y: r.payload.agent_id.includes("planner") ? 40 : r.payload.agent_id.includes("research") ? 200 : 360 },
      data: { label: `${r.payload.agent_id}\n#${r.payload.sequence}` },
      style: {
        border: failedReceiptIds.has(r.id) ? "2px solid #a4161a" : "1px solid #999",
        borderRadius: 10,
        padding: 8,
        background: failedReceiptIds.has(r.id) ? "#ffe8e8" : "#fff",
      },
    }));

    const mapByHash = new Map(receipts.map((r) => [r.receipt_hash, r]));
    const edges: Edge[] = [];
    receipts.forEach((r) => {
      const parent = r.payload.parent_receipt_hash;
      if (parent && mapByHash.has(parent)) {
        edges.push({
          id: `${parent}-${r.receipt_hash}`,
          source: parent,
          target: r.receipt_hash,
          label: "parent",
          style: failedReceiptIds.has(r.id) ? { stroke: "#a4161a", strokeWidth: 2 } : undefined,
          labelStyle: failedReceiptIds.has(r.id) ? { fill: "#a4161a", fontWeight: 700 } : undefined,
        });
      }
    });
    return { nodes, edges };
  }, [receipts, failedReceiptIds]);

  return (
    <main className="mx-auto max-w-7xl space-y-4 p-4">
      <h1 className="text-3xl font-bold">VeritasAgent Governance Dashboard</h1>

      <Card>
        <h2 className="mb-2 text-xl font-semibold">Tampering Alert Panel</h2>
        {firstError ? <p className="text-danger">{firstError}</p> : <p className="text-accent">No chain tampering detected.</p>}
        <div className="mt-3 flex gap-2">
          <button
            onClick={async () => {
              await fetch(`${API}/demo/failure`, { method: "POST" });
            }}
            className="rounded bg-red-700 px-3 py-2 text-sm font-semibold text-white"
          >
            Inject Dummy Failure
          </button>
          <button
            onClick={async () => {
              await fetch(`${API}/demo/reset`, { method: "POST" });
            }}
            className="rounded bg-zinc-700 px-3 py-2 text-sm font-semibold text-white"
          >
            Reset Demo Data
          </button>
        </div>
      </Card>

      <Card>
        <h2 className="mb-2 text-xl font-semibold">Edge Case Visualizer</h2>
        {status && !status.ok ? (
          <div className="space-y-2 text-sm">
            {status.receipts
              .filter((r) => !r.ok)
              .map((r) => (
                <div key={r.id} className="rounded border border-red-300 bg-red-50 p-2">
                  <div className="font-semibold">
                    Failed Receipt #{r.id} ({r.agent_id} / {r.tool_name})
                  </div>
                  {r.errors.map((e, idx) => (
                    <div key={`${r.id}-${idx}`} className="text-danger">
                      - {e}
                    </div>
                  ))}
                </div>
              ))}
          </div>
        ) : (
          <p className="text-sm">No failed receipts to visualize.</p>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 text-xl font-semibold">Receipt Chain Timeline</h2>
          <div className="space-y-2">
            {receipts.map((r) => (
              <button key={r.id} onClick={() => setSelectedId(r.id)} className="w-full rounded border border-zinc-300 p-2 text-left hover:bg-zinc-50">
                <div className="text-sm">{r.payload.timestamp}</div>
                <div className="font-semibold">{r.payload.agent_id} - {r.payload.tool_name}</div>
                <div className="text-sm">sequence #{r.payload.sequence}</div>
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="mb-3 text-xl font-semibold">Chain Integrity Status</h2>
          <div className="space-y-2">
            {status?.receipts.map((s) => (
              <div key={s.id} className="rounded border border-zinc-300 p-2">
                <div className="mb-1 font-medium">Receipt #{s.id} ({s.agent_id} / {s.tool_name})</div>
                <div className="flex gap-2">
                  <Badge ok={s.signature_valid} label={s.signature_valid ? "Signature OK" : "Signature Invalid"} />
                  <Badge ok={s.hash_valid} label={s.hash_valid ? "Hash OK" : "Hash Invalid"} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3 text-xl font-semibold">Receipt Inspector</h2>
          {selectedReceipt ? (
            <div className="space-y-1 text-sm">
              <div>tool_args_hash: {selectedReceipt.payload.tool_args_hash}</div>
              <div>result_hash: {selectedReceipt.payload.result_hash}</div>
              <div>signature: {selectedReceipt.signature.sig}</div>
              <div>previous_receipt_hash: {selectedReceipt.payload.previous_receipt_hash}</div>
              <div>policy_id: {selectedReceipt.payload.policy_id ?? "N/A"}</div>
            </div>
          ) : (
            <p>Select a receipt from the timeline.</p>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 text-xl font-semibold">Live Receipt Stream</h2>
          <p className="mb-2 text-sm">Polling backend every 2 seconds.</p>
          <div className="space-y-1 text-sm">
            {receipts.slice(-5).reverse().map((r) => (
              <div key={r.id}>#{r.id} {r.payload.agent_id} - {r.payload.tool_name}</div>
            ))}
          </div>
          <div className="mt-3 text-sm font-medium">Agent Counts</div>
          {agents.map((a) => (
            <div key={a.agent_id} className="text-sm">{a.agent_id}: {a.receipt_count}</div>
          ))}
        </Card>
      </div>

      <Card>
        <h2 className="mb-3 text-xl font-semibold">Multi-Agent Provenance Graph</h2>
        <div className="h-[420px] w-full rounded border border-zinc-300">
          <ReactFlow nodes={graph.nodes} edges={graph.edges} fitView>
            <Background />
            <Controls />
          </ReactFlow>
        </div>
      </Card>
    </main>
  );
}
