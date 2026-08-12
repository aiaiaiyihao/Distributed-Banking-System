import { formatCents } from "../money";

export default function AccountsPanel({ accounts, loading }) {
  return (
    <section className="panel">
      <h2>Accounts</h2>
      {loading ? (
        <p className="muted">Loading accounts...</p>
      ) : (
        <div className="account-cards">
          {accounts.map((account) => (
            <div className="account-card" key={account.account_id}>
              <div className="account-label">Account {account.account_id}</div>
              <div className="account-balance">{formatCents(account.balance)}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
