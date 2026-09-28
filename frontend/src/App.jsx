import { useState, useEffect } from "react";

function App() {
  // 1. State: Variables that update the UI when modified
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. Fetch data from your live backend API
  const fetchStudents = async () => {
    try {
      setLoading(true);
      const res = await fetch("https://student-ledger-backend.onrender.com/students");
      if (!res.ok) {
        throw new Error(`Server returned status: ${res.status}`);
      }
      const data = await res.json();
      setStudents(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Lifecycle hook: Runs once when the page loads (like a startup function in Python)
  useEffect(() => {
    fetchStudents();
  }, []);

  return (
    <div style={{ maxWidth: "800px", margin: "40px auto", fontFamily: "system-ui, sans-serif", padding: "0 20px" }}>
      <header style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: "16px", marginBottom: "24px" }}>
        <h1 style={{ margin: 0, color: "#111827" }}>Student Ledger Dashboard</h1>
        <p style={{ margin: "6px 0 0", color: "#6b7280" }}>
          Live API: <code>https://student-ledger-backend.onrender.com</code>
        </p>
      </header>

      {/* Loading & Error States */}
      {loading && <p style={{ color: "#2563eb" }}>Loading students from Render backend...</p>}
      {error && (
        <div style={{ padding: "12px", backgroundColor: "#fee2e2", color: "#991b1b", borderRadius: "6px" }}>
          <strong>Error connecting to API:</strong> {error}
        </div>
      )}

      {/* Student List Grid */}
      {!loading && !error && (
        <div style={{ display: "grid", gap: "16px" }}>
          {students.length === 0 ? (
            <p>No student records found.</p>
          ) : (
            students.map((student) => (
              <div
                key={student.id}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  padding: "16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                }}
              >
                <div>
                  <h3 style={{ margin: "0 0 4px", fontSize: "1.1rem" }}>{student.name}</h3>
                  <span
                    style={{
                      fontSize: "0.85rem",
                      backgroundColor: "#f3f4f6",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      color: "#4b5563",
                    }}
                  >
                    Course: {student.course}
                  </span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>Balance Due</div>
                  <div
                  style={{
                    fontSize: "1.25rem",
                    fontWeight: "bold",
                    color: (student.fee_balance ?? student.balance) > 0 ? "#dc2626" : "#16a34a",
                   }}
                  >
                   ₹{student.fee_balance ?? student.balance ?? 0}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default App;