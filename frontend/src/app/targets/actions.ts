"use server";

import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";

import { db } from "@/db/client";
import { crawlTargets } from "@/db/schema";
import { triggerCrawl } from "@/app/actions";

export type AddTargetInput = {
  base_url: string;
  crawl_mode?: string;
  max_depth?: number;
  keywords?: string[];
  keyword_mode?: string;
  schedule?: string | null;
};

export async function addTargetAction(data: AddTargetInput) {
  // Mirror backend repository.add_crawl_target: upsert on base_url and reset
  // is_active=true so the manual reactivation case keeps working.
  await db
    .insert(crawlTargets)
    .values({
      baseUrl: data.base_url,
      crawlMode: data.crawl_mode ?? "static",
      maxDepth: data.max_depth ?? 2,
      keywords: data.keywords ?? [],
      keywordMode: data.keyword_mode ?? "any",
      schedule: data.schedule ?? null,
      isActive: true,
    })
    .onConflictDoUpdate({
      target: crawlTargets.baseUrl,
      set: {
        crawlMode: data.crawl_mode ?? "static",
        maxDepth: data.max_depth ?? 2,
        keywords: data.keywords ?? [],
        keywordMode: data.keyword_mode ?? "any",
        schedule: data.schedule ?? null,
        isActive: true,
      },
    });
  revalidatePath("/targets");
}

export async function deactivateTargetAction(id: string) {
  await db
    .update(crawlTargets)
    .set({ isActive: false })
    .where(eq(crawlTargets.id, id));
  revalidatePath("/targets");
}

export async function crawlAction(targetId?: string): Promise<void> {
  await triggerCrawl(targetId);
}
