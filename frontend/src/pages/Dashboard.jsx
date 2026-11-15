import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearToken, getDashboardOverview } from "../api.js";

function getInitials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardOverview()
      .then(setOverview)
      .catch((err) => {
        if (err.status === 401) {
          clearToken();
          navigate("/login");
        } else {
          setError(err.message);
        }
      });
  }, [navigate]);

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="dashboard">
      <header className="topbar">
        <nav>
          <span className="topbar-tab">Dashboard</span>
        </nav>
        <div className="topbar-right">
          <button className="link-btn" onClick={handleLogout}>
            Log out
          </button>
          <div className="avatar">{overview ? getInitials(overview.full_name) : ""}</div>
        </div>
      </header>

      <div className="dashboard-body">
        <aside className="sidebar">
          <div className="sidebar-item active">Overview</div>
        </aside>

        <main className="content">
          <h2>Dashboard Overview</h2>
          {error && <div className="error-box">{error}</div>}
          {overview && (
            <>
              <p className="welcome">Welcome, {overview.full_name}</p>
              <div className="project-card">
                <div className="project-label">PROJECT TITLE</div>
                <div className="project-title">{overview.project_title}</div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
