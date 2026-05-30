import type { Metadata } from "next";
import Header from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Web Crawler CMS",
  description: "Blog CMS powered by web crawling",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>
        <Header />
        <main
          style={{
            maxWidth: 960,
            margin: "0 auto",
            padding: "var(--crawler-space-3)",
          }}
        >
          {children}
        </main>
      </body>
    </html>
  );
}
