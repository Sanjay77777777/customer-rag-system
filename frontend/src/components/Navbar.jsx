// ---------------------------------------------------------------------------
// NAVBAR COMPONENT
// ---------------------------------------------------------------------------
// Top navigation bar with branding and page links.
// Uses NavLink (from react-router-dom) which automatically highlights
// the active link based on the current URL path.

import { NavLink } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <h1 className="navbar-brand">Customer RAG</h1>
      <ul className="navbar-links">
        {/* "end" prop on Dashboard link means it only matches the exact "/" path,
            not "/customers" or "/analytics" which would also start with "/" */}
        <li><NavLink to="/" end>Dashboard</NavLink></li>
        <li><NavLink to="/customers">Customers</NavLink></li>
        <li><NavLink to="/analytics">Analytics</NavLink></li>
        <li><NavLink to="/chat">Chat</NavLink></li>
      </ul>
    </nav>
  );
}
