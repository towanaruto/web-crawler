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
        <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
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
    borderBottom: "1px solid #e5e7eb",
    backgroundColor: "#fff",
  },
  inner: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "16px 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  logo: {
    fontSize: 20,
    fontWeight: 700,
    textDecoration: "none",
    color: "#111",
  },
  navLink: {
    textDecoration: "none",
    color: "#555",
  },
  email: {
    color: "#666",
    fontSize: 13,
  },
};
