"use server";

import { and, eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";

import { db } from "@/db/client";
import { crawlTargets, type CrawlScheduleConfig } from "@/db/schema";
import { triggerCrawl, type CrawlRequestResult } from "@/app/actions";
import { requireCurrentUser } from "@/lib/current-user";
import { computeNextRunAt, normalizeScheduleConfig } from "@/lib/schedules";

export type AddTargetInput = {
  base_url: string;
  crawl_mode?: string;
  max_depth?: number;
  keywords?: string[];
  keyword_mode?: string;
};

export async function addTargetAction(data: AddTargetInput) {
  const user = await requireCurrentUser();
  // Mirror backend repository.add_crawl_target: upsert on base_url and reset
  // is_active=true so the manual reactivation case keeps working.
  await db
    .insert(crawlTargets)
    .values({
      userId: user.id,
      baseUrl: data.base_url,
      crawlMode: data.crawl_mode ?? "static",
      maxDepth: data.max_depth ?? 2,
      keywords: data.keywords ?? [],
      keywordMode: data.keyword_mode ?? "any",
      isActive: true,
    })
    .onConflictDoUpdate({
      target: [crawlTargets.userId, crawlTargets.baseUrl],
      set: {
        crawlMode: data.crawl_mode ?? "static",
        maxDepth: data.max_depth ?? 2,
        keywords: data.keywords ?? [],
        keywordMode: data.keyword_mode ?? "any",
        isActive: true,
      },
    });
  revalidatePath("/targets");
}

export async function deactivateTargetAction(id: string) {
  const user = await requireCurrentUser();
  await db
    .update(crawlTargets)
    .set({ isActive: false })
    .where(and(eq(crawlTargets.id, id), eq(crawlTargets.userId, user.id)));
  revalidatePath("/targets");
}

export async function updateTargetScheduleAction(
  id: string,
  data: { enabled: boolean; config: CrawlScheduleConfig | null },
) {
  const user = await requireCurrentUser();
  const config = data.enabled && data.config ? normalizeScheduleConfig(data.config) : null;
  await db
    .update(crawlTargets)
    .set({
      scheduleEnabled: data.enabled,
      scheduleConfig: config,
      scheduleTimezone: "Asia/Tokyo",
      nextRunAt: config ? computeNextRunAt(config) : null,
    })
    .where(and(eq(crawlTargets.id, id), eq(crawlTargets.userId, user.id)));
  revalidatePath("/targets");
}

export async function crawlAction(targetId?: string): Promise<CrawlRequestResult> {
  return triggerCrawl(targetId);
}
