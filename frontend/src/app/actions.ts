"use server";

import { and, eq, inArray } from "drizzle-orm";
import { revalidatePath } from "next/cache";

import { db } from "@/db/client";
import { articles } from "@/db/schema";
import { requireCurrentUser } from "@/lib/current-user";

export async function deleteArticleAction(id: string) {
  const user = await requireCurrentUser();
  await db
    .delete(articles)
    .where(and(eq(articles.id, id), eq(articles.userId, user.id)));
  revalidatePath("/");
}

export async function deleteArticlesAction(ids: string[]) {
  const uniqueIds = Array.from(new Set(ids.filter(Boolean)));
  if (uniqueIds.length === 0) return;

  const user = await requireCurrentUser();
  await db
    .delete(articles)
    .where(and(inArray(articles.id, uniqueIds), eq(articles.userId, user.id)));
  revalidatePath("/");
}

export type CrawlRequestResult = {
  jobIds: string[];
  targetsQueued: number;
};

type BackendCrawlJob = {
  id?: unknown;
};

type BackendCrawlSummary = {
  targets_queued?: unknown;
  job_ids?: unknown;
};

export async function triggerCrawl(targetId?: string): Promise<CrawlRequestResult> {
  const user = await requireCurrentUser();
  const backendApiUrl = process.env.BACKEND_API_URL;
  if (!backendApiUrl) {
    throw new Error("BACKEND_API_URL is not set");
  }

  const endpoint = targetId ? `/crawl/${targetId}` : "/crawl";
  const url = new URL(endpoint, backendApiUrl);
  if (targetId) {
    url.searchParams.set("user_id", user.id);
  }
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  if (process.env.BACKEND_API_TOKEN) {
    headers["X-Internal-Api-Key"] = process.env.BACKEND_API_TOKEN;
  }
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: targetId ? undefined : JSON.stringify({ user_id: user.id }),
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Crawl request failed: ${res.status} ${body}`);
  }

  const body: unknown = await res.json().catch(() => null);
  return toCrawlRequestResult(body);
}

function toCrawlRequestResult(body: unknown): CrawlRequestResult {
  if (Array.isArray(body)) {
    const jobIds = body
      .map((job: BackendCrawlJob) => job.id)
      .filter((id): id is string => typeof id === "string");
    return { jobIds, targetsQueued: body.length };
  }

  if (isRecord(body)) {
    const jobId = typeof body.id === "string" ? body.id : null;
    const summary = body as BackendCrawlSummary;
    const jobIds = Array.isArray(summary.job_ids)
      ? summary.job_ids.filter((id): id is string => typeof id === "string")
      : [];
    const targetsQueued = summary.targets_queued;
    return {
      jobIds: jobIds.length > 0 ? jobIds : jobId ? [jobId] : [],
      targetsQueued: typeof targetsQueued === "number" ? targetsQueued : 1,
    };
  }

  return { jobIds: [], targetsQueued: 1 };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
