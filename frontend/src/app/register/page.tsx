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
    margin: "var(--crawler-space-6) auto",
  },
  title: {
    fontSize: "var(--crawler-font-size-page)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    marginBottom: "var(--crawler-space-2)",
  },
  copy: {
    color: "var(--crawler-text-secondary)",
    lineHeight: 1.6,
    marginBottom: "var(--crawler-space-3)",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--crawler-space-2)",
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--crawler-space-1)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  input: {
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-md)",
    fontSize: "var(--crawler-font-size-md)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
  },
  button: {
    backgroundColor: "var(--crawler-accent-primary)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    color: "var(--crawler-text-on-accent)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-md)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
  },
};
