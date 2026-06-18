// ---------------------------------------------------------------------------
// CUSTOMER TABLE COMPONENT
// ---------------------------------------------------------------------------
// Renders an HTML table of customer records for the Customers page.
//
// Props:
//   customers — array of customer objects from GET /customers endpoint.
//     Each object has: customer_id, first_name, last_name, occupation,
//     customer_segment, annual_income, preferred_product (and more).

import "./CustomerTable.css";

export default function CustomerTable({ customers }) {
  // Show a friendly message when the result set is empty
  if (!customers || customers.length === 0) {
    return <p className="empty">No customers found.</p>;
  }

  return (
    <div className="table-wrapper">
      <table className="customer-table">
        <thead>
          <tr>
            <th>Customer ID</th>
            <th>Name</th>
            <th>Occupation</th>
            <th>Segment</th>
            <th>Income</th>
            <th>Preferred Product</th>
          </tr>
        </thead>
        <tbody>
          {customers.map((c) => (
            // Use customer_id as the React key for efficient list rendering
            <tr key={c.customer_id}>
              <td>{c.customer_id}</td>
              <td>{c.first_name} {c.last_name}</td>
              <td>{c.occupation}</td>
              <td>{c.customer_segment}</td>
              {/* toLocaleString() formats the number with locale-specific separators */}
              <td>${c.annual_income?.toLocaleString()}</td>
              <td>{c.preferred_product}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
