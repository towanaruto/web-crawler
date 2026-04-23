"use server";

import { revalidatePath } from "next/cache";
import { deleteArticle } from "@/lib/api";

export async function deleteArticleAction(id: string) {
  await deleteArticle(id);
  revalidatePath("/");
}
