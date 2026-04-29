import type { Config } from "drizzle-kit";

export default {
  schema: "./src/db/schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.MIGRATION_DATABASE_URL ?? process.env.DATABASE_URL ?? "",
  },
  // We do not generate migrations from this file — Alembic owns schema.
  // drizzle-kit is used only for `pull` (introspection) to detect drift.
} satisfies Config;
