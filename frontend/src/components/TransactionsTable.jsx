import { formatCents } from "../money";

export default function TransactionsTable({ transactions, loading }) {
  return (
    <section className="panel">
      <h2>Recent Transactions</h2>
      {loading ? (
        <p className="muted">Loading transactions...</p>
      ) : transactions.length === 0 ? (
        <p className="muted">No transactions yet on this branch.</p>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Origin Branch</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.transaction_id}>
                  <td className="mono">{tx.transaction_id}</td>
                  <td>{tx.type}</td>
                  <td>{formatCents(tx.amount)}</td>
                  <td>
                    <span className={`status-badge status-${tx.status.toLowerCase()}`}>
                      {tx.status}
                    </span>
                  </td>
                  <td>Branch {tx.origin_branch}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
