import { useEffect, useState } from "react";
import { deposit, withdraw, transfer } from "../api";
import { dollarsToCents } from "../money";

const TYPES = ["DEPOSIT", "WITHDRAW", "TRANSFER"];

function newTransactionId() {
  return `tx-${crypto.randomUUID()}`;
}

export default function TransactionForm({ branches, accountIds, selectedBranch, onSubmitted }) {
  const [type, setType] = useState("DEPOSIT");
  const [account, setAccount] = useState(accountIds[0]);
  const [fromAccount, setFromAccount] = useState(accountIds[0]);
  const [toAccount, setToAccount] = useState(accountIds[1] ?? accountIds[0]);
  const [amount, setAmount] = useState("100");
  const [branchId, setBranchId] = useState(selectedBranch);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => setBranchId(selectedBranch), [selectedBranch]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const cents = dollarsToCents(amount);
    if (!cents || cents <= 0) {
      setError("Amount must be a positive number.");
      return;
    }

    const transactionId = newTransactionId();
    let endpoint, apiFn, body;

    if (type === "DEPOSIT") {
      body = { account_id: account, amount: cents, branch_id: branchId, transaction_id: transactionId };
      endpoint = "deposit";
      apiFn = deposit;
    } else if (type === "WITHDRAW") {
      body = { account_id: account, amount: cents, branch_id: branchId, transaction_id: transactionId };
      endpoint = "withdraw";
      apiFn = withdraw;
    } else {
      if (fromAccount === toAccount) {
        setError("From Account and To Account must be different.");
        return;
      }
      body = {
        from_account: fromAccount,
        to_account: toAccount,
        amount: cents,
        branch_id: branchId,
        transaction_id: transactionId,
      };
      endpoint = "transfer";
      apiFn = transfer;
    }

    setSubmitting(true);
    try {
      const response = await apiFn(body);
      onSubmitted({ endpoint, apiFn, body, response });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <h2>New Transaction</h2>
      <form className="transaction-form" onSubmit={handleSubmit}>
        <label>
          Type
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0) + t.slice(1).toLowerCase()}
              </option>
            ))}
          </select>
        </label>

        {type === "TRANSFER" ? (
          <>
            <label>
              From Account
              <select value={fromAccount} onChange={(e) => setFromAccount(Number(e.target.value))}>
                {accountIds.map((id) => (
                  <option key={id} value={id}>
                    Account {id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              To Account
              <select value={toAccount} onChange={(e) => setToAccount(Number(e.target.value))}>
                {accountIds.map((id) => (
                  <option key={id} value={id}>
                    Account {id}
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : (
          <label>
            Account
            <select value={account} onChange={(e) => setAccount(Number(e.target.value))}>
              {accountIds.map((id) => (
                <option key={id} value={id}>
                  Account {id}
                </option>
              ))}
            </select>
          </label>
        )}

        <label>
          Amount
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </label>

        <label>
          Branch
          <select value={branchId} onChange={(e) => setBranchId(Number(e.target.value))}>
            {branches.map((b) => (
              <option key={b.branch_id} value={b.branch_id}>
                {b.name}
              </option>
            ))}
          </select>
        </label>

        {error && <div className="form-error">{error}</div>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Submitting..." : "Submit"}
        </button>
      </form>
    </section>
  );
}
