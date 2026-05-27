"use server";

import { redirect } from "next/navigation";

export async function verifyInviteAction(formData: FormData) {
  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const accessCode = String(formData.get("access_code") ?? "").trim();
  if (!email || !accessCode) {
    throw new Error("Email and access code are required");
  }

  const backendApiUrl = process.env.BACKEND_API_URL;
  if (!backendApiUrl) {
    throw new Error("BACKEND_API_URL is not set");
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (process.env.BACKEND_API_TOKEN) {
    headers["X-Internal-Api-Key"] = process.env.BACKEND_API_TOKEN;
  }

  const res = await fetch(new URL("/auth/invites/verify", backendApiUrl), {
    method: "POST",
    headers,
    body: JSON.stringify({
      email,
      access_code: accessCode,
      provider: "app-register",
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Invalid or expired access code");
  }

  const params = new URLSearchParams({
    screen_hint: "signup",
    login_hint: email,
  });
  redirect(`/auth/login?${params.toString()}`);
}
