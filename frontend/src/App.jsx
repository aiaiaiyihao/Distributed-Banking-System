import { useEffect, useState, useCallback } from "react";
import BranchSelector from "./components/BranchSelector";
import AccountsPanel from "./components/AccountsPanel";
import TransactionForm from "./components/TransactionForm";
import DuplicateDemo from "./components/DuplicateDemo";
import TransactionsTable from "./components/TransactionsTable";
import { getBranches, getAccounts, getTransactions } from "./api";

const FALLBACK_BRANCHES = [
  { branch_id: 1, name: "Branch 1" },
  { branch_id: 2, name: "Branch 2" },
  { branch_id: 3, name: "Branch 3" },
];

export default function App() {
  const [branches, setBranches] = useState(FALLBACK_BRANCHES);
  const [selectedBranch, setSelectedBranch] = useState(1);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [loadingTransactions, setLoadingTransactions] = useState(true);
  const [lastTransaction, setLastTransaction] = useState(null);
  const [banner, setBanner] = useState(null);

  const refresh = useCallback(async (branchId) => {
    setLoadingAccounts(true);
    setLoadingTransactions(true);
    try {
      const [accountsData, transactionsData] = await Promise.all([
        getAccounts(branchId),
        getTransactions(branchId),
      ]);
      setAccounts(accountsData);
      setTransactions(transactionsData);
    } catch (err) {
      setBanner({ tone: "error", text: `Failed to load branch data: ${err.message}` });
    } finally {
      setLoadingAccounts(false);
      setLoadingTransactions(false);
    }
  }, []);

  useEffect(() => {
    getBranches()
      .then(setBranches)
      .catch(() => setBranches(FALLBACK_BRANCHES));
  }, []);

  useEffect(() => {
    refresh(selectedBranch);
  }, [selectedBranch, refresh]);

  function handleSubmitted({ endpoint, apiFn, body, response }) {
    setLastTransaction({ apiFn, body });
    setBanner({
      tone: response.status === "SUCCESS" ? "success" : "failed",
      text: `${endpoint.toUpperCase()} ${response.transaction_id}: ${response.status} — ${response.message}`,
    });
    refresh(selectedBranch);
  }

  function handleDuplicateResult(response) {
    const isDuplicate = (response.message || "").toLowerCase().includes("duplicate");
    setBanner({
      tone: isDuplicate ? "duplicate" : response.status === "SUCCESS" ? "success" : "failed",
      text: isDuplicate
        ? "Duplicate transaction detected. Existing result returned. Balance was not changed."
        : `${response.transaction_id}: ${response.status} — ${response.message}`,
    });
    refresh(selectedBranch);
  }

  const accountIds = accounts.length > 0 ? accounts.map((a) => a.account_id) : [1, 2, 3];

  return (
    <div className="app">
      <header className="app-header">
        <h1>Distributed Banking System</h1>
        <BranchSelector branches={branches} selectedBranch={selectedBranch} onChange={setSelectedBranch} />
      </header>

      {banner && <div className={`banner banner-${banner.tone}`}>{banner.text}</div>}

      <main className="app-grid">
        <div className="app-column">
          <AccountsPanel accounts={accounts} loading={loadingAccounts} />
          <TransactionsTable transactions={transactions} loading={loadingTransactions} />
        </div>
        <div className="app-column">
          <TransactionForm
            branches={branches}
            accountIds={accountIds}
            selectedBranch={selectedBranch}
            onSubmitted={handleSubmitted}
          />
          <DuplicateDemo lastTransaction={lastTransaction} onDuplicateResult={handleDuplicateResult} />
        </div>
      </main>
    </div>
  );
}
