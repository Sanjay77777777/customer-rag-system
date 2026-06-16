import "./CustomerTable.css";

export default function CustomerTable({ customers }) {
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
            <tr key={c.customer_id}>
              <td>{c.customer_id}</td>
              <td>{c.first_name} {c.last_name}</td>
              <td>{c.occupation}</td>
              <td>{c.customer_segment}</td>
              <td>${c.annual_income?.toLocaleString()}</td>
              <td>{c.preferred_product}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
