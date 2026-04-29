/**
 * Page-facing read queries. Wraps Drizzle to return shapes the React tree
 * consumes directly — no further mapping in components.
 */
import { desc, eq, ilike, or, sql } from "drizzle-orm";

import { db } from "./client";
import { articles, crawlTargets } from "./schema";

export type ArticleListItem = {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  sourceUrl: string;
  publishedAt: Date | null;
  crawledAt: Date | null;
  featuredImageUrl: string | null;
  wordCount: number | null;
  status: string;
  author: { id: string; name: string; slug: string } | null;
  category: { id: string; name: string; slug: string } | null;
  tags: { id: string; name: string; slug: string }[];
};

export type ArticleDetail = ArticleListItem & {
  bodyHtml: string | null;
  bodyText: string | null;
  rawHtmlR2Key: string | null;
  imageR2Keys: string[];
};

export type CrawlTargetItem = {
  id: string;
  baseUrl: string;
  crawlMode: string;
  maxDepth: number | null;
  isActive: boolean | null;
  keywords: string[];
  keywordMode: string;
  schedule: string | null;
};

export async function listArticles(opts: {
  search?: string;
  offset?: number;
  limit?: number;
}): Promise<{ items: ArticleListItem[]; total: number }> {
  const { search, offset = 0, limit = 20 } = opts;

  const where = search
    ? or(
        ilike(articles.title, `%${search}%`),
        ilike(articles.bodyText, `%${search}%`),
        ilike(articles.excerpt, `%${search}%`),
      )
    : undefined;

  const totalRow = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(articles)
    .where(where);
  const total = totalRow[0]?.count ?? 0;

  const rows = await db.query.articles.findMany({
    where,
    orderBy: [desc(articles.crawledAt)],
    offset,
    limit,
    with: {
      author: true,
      category: true,
      articleTags: { with: { tag: true } },
    },
  });

  return { items: rows.map(toListItem), total };
}

export async function getArticleBySlug(slug: string): Promise<ArticleDetail | null> {
  const row = await db.query.articles.findFirst({
    where: eq(articles.slug, slug),
    with: {
      author: true,
      category: true,
      articleTags: { with: { tag: true } },
    },
  });
  if (!row) return null;
  return {
    ...toListItem(row),
    bodyHtml: row.bodyHtml,
    bodyText: row.bodyText,
    rawHtmlR2Key: row.rawHtmlR2Key,
    imageR2Keys: row.imageR2Keys ?? [],
  };
}

export async function listActiveCrawlTargets(): Promise<CrawlTargetItem[]> {
  const rows = await db
    .select()
    .from(crawlTargets)
    .where(eq(crawlTargets.isActive, true));
  return rows.map((t) => ({
    id: t.id,
    baseUrl: t.baseUrl,
    crawlMode: t.crawlMode,
    maxDepth: t.maxDepth,
    isActive: t.isActive,
    keywords: t.keywords ?? [],
    keywordMode: t.keywordMode ?? "any",
    schedule: t.schedule,
  }));
}

// ── Internals ────────────────────────────────────────────────────

type ArticleRow = {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  sourceUrl: string;
  publishedAt: Date | null;
  crawledAt: Date | null;
  featuredImageUrl: string | null;
  wordCount: number | null;
  status: string | null;
  author: { id: string; name: string; slug: string } | null;
  category: { id: string; name: string; slug: string } | null;
  articleTags: { tag: { id: string; name: string; slug: string } }[];
};

function toListItem(r: ArticleRow): ArticleListItem {
  return {
    id: r.id,
    title: r.title,
    slug: r.slug,
    excerpt: r.excerpt,
    sourceUrl: r.sourceUrl,
    publishedAt: r.publishedAt,
    crawledAt: r.crawledAt,
    featuredImageUrl: r.featuredImageUrl,
    wordCount: r.wordCount,
    status: r.status ?? "draft",
    author: r.author,
    category: r.category,
    tags: r.articleTags.map((at) => at.tag),
  };
}
