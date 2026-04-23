"use server";

import { revalidatePath } from "next/cache";
import {
  createCrawlTarget,
  deleteCrawlTarget,
  triggerCrawl,
  CrawlTargetCreate,
  CrawlResult,
} from "@/lib/api";

export async function addTargetAction(data: CrawlTargetCreate) {
  await createCrawlTarget(data);
  revalidatePath("/targets");
}

export async function deactivateTargetAction(id: string) {
  await deleteCrawlTarget(id);
  revalidatePath("/targets");
}

export async function crawlAction(): Promise<CrawlResult> {
  const result = await triggerCrawl();
  revalidatePath("/");
  return result;
}
