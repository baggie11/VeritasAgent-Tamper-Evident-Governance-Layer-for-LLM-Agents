export type ReceiptPayload = {
  type: string;
  chain_id: string;
  agent_id: string;
  tool_name: string;
  tool_args_hash: string;
  result_hash: string;
  timestamp: string;
  sequence: number;
  previous_receipt_hash: string;
  policy_id?: string;
  policy_decision?: string;
  parent_receipt_hash?: string;
  metadata: Record<string, unknown>;
};

export type Receipt = {
  id: number;
  payload: ReceiptPayload;
  receipt_hash: string;
  signature: {
    alg: string;
    sig: string;
    public_key: string;
  };
};

export type ChainStatus = {
  ok: boolean;
  errors: string[];
  receipts: Array<{
    id: number;
    sequence: number;
    agent_id: string;
    tool_name: string;
    hash_valid: boolean;
    signature_valid: boolean;
    ok: boolean;
    errors: string[];
  }>;
};

export type AgentCount = {
  agent_id: string;
  receipt_count: number;
};
