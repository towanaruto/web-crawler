import { neon } from "@neondatabase/serverless";
import { Pool } from "pg";
import { drizzle as drizzleNeon, type NeonHttpDatabase } from "drizzle-orm/neon-http";
import {
  drizzle as drizzleNodePostgres,
  type NodePgDatabase,
} from "drizzle-orm/node-postgres";

import * as schema from "./schema";

type Db = NeonHttpDatabase<typeof schema> | NodePgDatabase<typeof schema>;

let _db: Db | null = null;

function getDb(): Db {
  if (_db) return _db;
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is not set");
  }
  if (isNeonHttpUrl(databaseUrl)) {
    const sql = neon(databaseUrl);
    _db = drizzleNeon(sql, { schema });
  } else {
    const pool = new Pool({ connectionString: databaseUrl });
    _db = drizzleNodePostgres(pool, { schema });
  }
  return _db;
}

function isNeonHttpUrl(databaseUrl: string): boolean {
  return databaseUrl.includes("neon.tech");
}

export const db = new Proxy({} as Db, {
  get(_target, prop, receiver) {
    return Reflect.get(getDb(), prop, receiver);
  },
});

export { schema };
