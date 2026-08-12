export default function BranchSelector({ branches, selectedBranch, onChange }) {
  return (
    <div className="branch-selector">
      <label htmlFor="viewing-branch">Viewing Branch:</label>
      <select
        id="viewing-branch"
        value={selectedBranch}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        {branches.map((b) => (
          <option key={b.branch_id} value={b.branch_id}>
            {b.name}
          </option>
        ))}
      </select>
    </div>
  );
}
