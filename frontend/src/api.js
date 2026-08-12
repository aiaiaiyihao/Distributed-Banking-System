const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed with status ${res.status}`);
  }
  return data;
}

export const getBranches = () => request("/api/branches");

export const getAccounts = (branchId) => request(`/api/accounts?branch_id=${branchId}`);

export const getTransactions = (branchId) => request(`/api/transactions?branch_id=${branchId}`);

export const deposit = (body) =>
  request("/api/deposit", { method: "POST", body: JSON.stringify(body) });

export const withdraw = (body) =>
  request("/api/withdraw", { method: "POST", body: JSON.stringify(body) });

export const transfer = (body) =>
  request("/api/transfer", { method: "POST", body: JSON.stringify(body) });
