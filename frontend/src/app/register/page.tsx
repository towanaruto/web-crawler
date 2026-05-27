import { verifyInviteAction } from "./actions";

export default function RegisterPage() {
  return (
    <div style={styles.wrap}>
      <h1 style={styles.title}>Create account</h1>
      <p style={styles.copy}>
        Enter the email address and access code you received. After verification,
        you can create an Auth0 account or continue with Google using that email.
      </p>
      <form action={verifyInviteAction} style={styles.form}>
        <label style={styles.label}>
          Email
          <input
            name="email"
            type="email"
            required
            autoComplete="email"
            style={styles.input}
          />
        </label>
        <label style={styles.label}>
          Access code
          <input
            name="access_code"
            type="password"
            required
            autoComplete="one-time-code"
            style={styles.input}
          />
        </label>
        <button type="submit" style={styles.button}>
          Continue
        </button>
      </form>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: {
    maxWidth: 480,
    margin: "48px auto",
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    marginBottom: 12,
  },
  copy: {
    color: "#555",
    lineHeight: 1.6,
    marginBottom: 24,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    fontWeight: 600,
  },
  input: {
    border: "1px solid #d1d5db",
    borderRadius: 6,
    fontSize: 16,
    padding: "10px 12px",
  },
  button: {
    backgroundColor: "#0369a1",
    border: "none",
    borderRadius: 6,
    color: "#fff",
    cursor: "pointer",
    fontSize: 15,
    fontWeight: 700,
    padding: "11px 16px",
  },
};
