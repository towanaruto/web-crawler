"use server";

import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";

import { db } from "@/db/client";
import { articles } from "@/db/schema";

export async function deleteArticleAction(id: string) {
  await db.delete(articles).where(eq(articles.id, id));
  revalidatePath("/");
}

/**
 * Trigger the crawl workflow on GitHub. Uses workflow_dispatch so runs are
 * auditable in the Actions tab and share one workflow with the cron schedule.
 * Server-side only — the PAT never reaches the browser.
 */
export async function triggerCrawl(targetId?: string): Promise<void> {
  const owner = process.env.GH_OWNER;
  const repo = process.env.GH_REPO;
  const token = process.env.GH_DISPATCH_TOKEN;
  if (!owner || !repo || !token) {
    throw new Error("GitHub dispatch env vars missing");
  }

  const res = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/actions/workflows/crawl.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({
        ref: "main",
        inputs: targetId ? { target_id: targetId } : {},
      }),
    },
  );

  if (res.status !== 204) {
    const body = await res.text().catch(() => "");
    throw new Error(`Workflow dispatch failed: ${res.status} ${body}`);
  }
}
