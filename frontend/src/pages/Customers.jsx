// ---------------------------------------------------------------------------
// CUSTOMERS PAGE
// ---------------------------------------------------------------------------
// Displays a filterable table of all customer records. Three filters are
// available (customer ID, segment, product) and the data refetches
// automatically when any filter changes via the useEffect dependency array.

import { useEffect, useState } from "react";
import { getCustomers } from "../services/api";
import CustomerTable from "../components/CustomerTable";

// Dropdown options for the segment and product filters.
// "All" means no filter (all values are returned).
const SEGMENTS = ["All", "Silver", "Gold", "Platinum"];
const PRODUCTS = ["All", "Laptop", "Tablet", "Phone", "Monitor", "Headphones"];

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter state — each change triggers a refetch
  const [customerId, setCustomerId] = useState("");
  const [segment, setSegment] = useState("All");
  const [product, setProduct] = useState("All");

  // Build query params object, omitting filters set to "All" or empty
  function buildParams() {
    const params = {};
    if (customerId) params.customer_id = customerId;
    if (segment && segment !== "All") params.segment = segment;
    if (product && product !== "All") params.product = product;
    return params;
  }

  // Count how many filters are active (for the clear button badge)
  const activeFilterCount = [
    !!customerId,
    segment !== "All",
    product !== "All",
  ].filter(Boolean).length;

  // Fetch customer data from the API
  function fetchData() {
    setLoading(true);
    setError(null);
    getCustomers(buildParams())
      .then(setCustomers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  // Refetch whenever any filter changes
  useEffect(() => {
    fetchData();
  }, [customerId, segment, product]);

  // Reset all filters to their default values
  function clearFilters() {
    setCustomerId("");
    setSegment("All");
    setProduct("All");
  }

  return (
    <div className="page">
      <h2>Customers</h2>
      <p className="subtitle">All customer records</p>

      <div className="filter-bar">
        <input
          type="number"
          placeholder="Customer ID"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          className="filter-input"
        />
        <select
          value={segment}
          onChange={(e) => setSegment(e.target.value)}
          className="filter-select"
        >
          {SEGMENTS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          className="filter-select"
        >
          {PRODUCTS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="filter-button clear"
          onClick={clearFilters}
        >
          Clear Filters
          {activeFilterCount > 0 && ` (${activeFilterCount})`}
        </button>
      </div>

      {loading && <p>Loading customers...</p>}
      {error && <p className="error">Error: {error}</p>}
      {!loading && !error && <CustomerTable customers={customers} />}
    </div>
  );
}
