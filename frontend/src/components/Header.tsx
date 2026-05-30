import Link from "next/link";
import { auth0 } from "@/lib/auth0";

export default async function Header() {
  const session = await auth0.getSession();
  const user = session?.user;

  return (
    <header style={styles.header}>
      <div style={styles.inner}>
        <Link href="/" style={styles.logo}>
          Web Crawler CMS
        </Link>
        <nav
          style={{
            display: "flex",
            gap: "var(--crawler-space-2)",
            alignItems: "center",
          }}
        >
          <Link href="/" style={styles.navLink}>
            Articles
          </Link>
          <Link href="/targets" style={styles.navLink}>
            Targets
          </Link>
          {!user && (
            <>
              <Link href="/register" style={styles.navLink}>
                Register
              </Link>
              <a href="/auth/login" style={styles.navLink}>
                Login
              </a>
            </>
          )}
          {user && (
            <>
              <span style={styles.email}>{user.email}</span>
              <a href="/auth/logout" style={styles.navLink}>
                Logout
              </a>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    borderBottom: "1px solid var(--crawler-border-subtle)",
    backgroundColor: "var(--crawler-surface-bg)",
  },
  inner: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "var(--crawler-space-2) var(--crawler-space-3)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  logo: {
    fontSize: "var(--crawler-font-size-title)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    textDecoration: "none",
    color: "var(--crawler-text-primary)",
  },
  navLink: {
    textDecoration: "none",
    color: "var(--crawler-text-secondary)",
  },
  email: {
    color: "var(--crawler-text-tertiary)",
    fontSize: "var(--crawler-font-size-caption)",
  },
};
