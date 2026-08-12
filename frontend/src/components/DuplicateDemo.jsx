import { useState } from "react";

export default function DuplicateDemo({ lastTransaction, onDuplicateResult }) {
  const [busy, setBusy] = useState(false);

  async function handleClick() {
    if (!lastTransaction) return;
    setBusy(true);
    try {
      const response = await lastTransaction.apiFn(lastTransaction.body);
      onDuplicateResult(response);
    } catch (err) {
      onDuplicateResult({ status: "ERROR", message: err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel duplicate-demo">
      <h2>Idempotency Demo</h2>
      <p className="muted">
        Resend the last successful transaction with the exact same transaction ID to prove it only
        executes once, whether the duplicate comes from a client retry or replication.
      </p>
      <button type="button" onClick={handleClick} disabled={!lastTransaction || busy}>
        {busy ? "Sending..." : "Simulate Duplicate Request"}
      </button>
    </section>
  );
}
