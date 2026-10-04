import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export function NavBar() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <nav
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 24px",
        borderBottom: "1px solid #e5e7eb",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
        <Link to="/translate" style={{ fontWeight: 800, textDecoration: "none", color: "#111827" }}>
          ISL Translator
        </Link>
        {isAuthenticated && (
          <>
            <Link to="/translate" style={{ color: "#374151", textDecoration: "none" }}>
              Live
            </Link>
            <Link to="/history" style={{ color: "#374151", textDecoration: "none" }}>
              History
            </Link>
          </>
        )}
      </div>
      <div>
        {isAuthenticated ? (
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <span style={{ color: "#6b7280", fontSize: 14 }}>{user?.name}</span>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              style={{ border: "none", background: "transparent", cursor: "pointer", color: "#dc2626" }}
            >
              Log out
            </button>
          </div>
        ) : (
          <Link to="/login" style={{ color: "#111827" }}>
            Log in
          </Link>
        )}
      </div>
    </nav>
  );
}
