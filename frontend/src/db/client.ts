/**
 * Neon HTTP driver via Drizzle. Works in both Vercel Edge and Node runtimes.
 *
 * The HTTP driver issues one round-trip per query (no persistent connection),
 * which is ideal for serverless. For interactive transactions or LISTEN/NOTIFY
 * we would switch to drizzle-orm/neon-serverless (WebSocket).
 *
 * Initialization is lazy (Proxy-based) so that Next.js build-time page-data
 * collection can run without a real DATABASE_URL — the connection only opens
 * the first time a query is executed.
 */
import { neon } from "@neondatabase/serverless";
import { drizzle, type NeonHttpDatabase } from "drizzle-orm/neon-http";

import * as schema from "./schema";

type Db = NeonHttpDatabase<typeof schema>;

let _db: Db | null = null;

function getDb(): Db {
  if (_db) return _db;
  if (!process.env.DATABASE_URL) {
    throw new Error("DATABASE_URL is not set");
  }
  const sql = neon(process.env.DATABASE_URL);
  _db = drizzle(sql, { schema });
  return _db;
}

export const db: Db = new Proxy({} as Db, {
  get(_target, prop, receiver) {
    return Reflect.get(getDb(), prop, receiver);
  },
});

export { schema };
