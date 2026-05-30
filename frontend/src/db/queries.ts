/**
 * Page-facing read queries. Wraps Drizzle to return shapes the React tree
 * consumes directly — no further mapping in components.
 */
import { and, asc, desc, eq, ilike, or, sql, type SQL } from "drizzle-orm";

import { db } from "./client";
import { articles, crawlTargets, type CrawlScheduleConfig } from "./schema";

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

export const articleSortKeys = ["crawledAt", "title", "publishedAt"] as const;
export type ArticleSortKey = (typeof articleSortKeys)[number];
export type ArticleSortDirection = "asc" | "desc";
export type ArticleSort = {
  sort: ArticleSortKey;
  direction: ArticleSortDirection;
};

export const DEFAULT_ARTICLE_SORT: ArticleSort = {
  sort: "crawledAt",
  direction: "desc",
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
  scheduleEnabled: boolean;
  scheduleConfig: CrawlScheduleConfig | null;
  scheduleTimezone: string;
  nextRunAt: Date | null;
  lastScheduledAt: Date | null;
};

export async function listArticles(opts: {
  userId: string;
  search?: string;
  offset?: number;
  limit?: number;
  sort?: ArticleSortKey;
  direction?: ArticleSortDirection;
}): Promise<{ items: ArticleListItem[]; total: number }> {
  const {
    userId,
    search,
    offset = 0,
    limit = 20,
    sort = DEFAULT_ARTICLE_SORT.sort,
    direction = DEFAULT_ARTICLE_SORT.direction,
  } = opts;

  const searchWhere = search
    ? or(
        ilike(articles.title, `%${search}%`),
        ilike(articles.bodyText, `%${search}%`),
        ilike(articles.excerpt, `%${search}%`),
      )
    : undefined;
  const where = searchWhere
    ? and(eq(articles.userId, userId), searchWhere)
    : eq(articles.userId, userId);

  const totalRow = await db
    .select({ count: sql<number>`count(*)::int` })
    .from(articles)
    .where(where);
  const total = totalRow[0]?.count ?? 0;

  const rows = await db.query.articles.findMany({
    where,
    orderBy: getArticleOrderBy({ sort, direction }),
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

export function normalizeArticleSort(
  sort?: string,
  direction?: string,
): ArticleSort {
  const safeSort = articleSortKeys.includes(sort as ArticleSortKey)
    ? (sort as ArticleSortKey)
    : DEFAULT_ARTICLE_SORT.sort;
  const safeDirection =
    direction === "asc" || direction === "desc"
      ? direction
      : DEFAULT_ARTICLE_SORT.direction;

  return { sort: safeSort, direction: safeDirection };
}

export async function getArticleBySlug(
  slug: string,
  userId: string,
): Promise<ArticleDetail | null> {
  const row = await db.query.articles.findFirst({
    where: and(eq(articles.slug, slug), eq(articles.userId, userId)),
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

export async function listActiveCrawlTargets(userId: string): Promise<CrawlTargetItem[]> {
  const rows = await db
    .select()
    .from(crawlTargets)
    .where(and(eq(crawlTargets.isActive, true), eq(crawlTargets.userId, userId)));
  return rows.map((t) => ({
    id: t.id,
    baseUrl: t.baseUrl,
    crawlMode: t.crawlMode,
    maxDepth: t.maxDepth,
    isActive: t.isActive,
    keywords: t.keywords ?? [],
    keywordMode: t.keywordMode ?? "any",
    scheduleEnabled: t.scheduleEnabled,
    scheduleConfig: t.scheduleConfig,
    scheduleTimezone: t.scheduleTimezone,
    nextRunAt: t.nextRunAt,
    lastScheduledAt: t.lastScheduledAt,
  }));
}

// ── Internals ────────────────────────────────────────────────────

function getArticleOrderBy(sort: ArticleSort): SQL[] {
  const timestampDirection =
    sort.direction === "asc" ? sql`asc nulls last` : sql`desc nulls last`;

  switch (sort.sort) {
    case "title":
      return [
        sort.direction === "asc" ? asc(articles.title) : desc(articles.title),
        desc(articles.crawledAt),
      ];
    case "publishedAt":
      return [
        sql`${articles.publishedAt} ${timestampDirection}`,
        desc(articles.crawledAt),
      ];
    case "crawledAt":
    default:
      return [
        sql`${articles.crawledAt} ${timestampDirection}`,
        asc(articles.title),
      ];
  }
}

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
