import { redirect } from "next/navigation";

import { db } from "@/db/client";
import { users, type User } from "@/db/schema";
import { auth0 } from "@/lib/auth0";

export async function requireCurrentUser(): Promise<User> {
  const session = await auth0.getSession();
  const profile = session?.user;
  if (!profile?.sub || !profile.email) {
    redirect("/auth/login");
  }

  const now = new Date();
  const values = {
    auth0Sub: profile.sub,
    email: profile.email.toLowerCase(),
    name: typeof profile.name === "string" ? profile.name : null,
    pictureUrl: typeof profile.picture === "string" ? profile.picture : null,
    updatedAt: now,
  };

  const [row] = await db
    .insert(users)
    .values({ ...values, createdAt: now })
    .onConflictDoUpdate({
      target: users.auth0Sub,
      set: values,
    })
    .returning();

  return row;
}
