/**
 * Drizzle schema mirroring backend/src/db/models.py.
 *
 * SQLAlchemy is the source-of-truth (Alembic owns DDL). This file is hand
 * mirrored — keep it in sync by running `drizzle-kit pull` against Neon and
 * diffing the output (planned in CI).
 */
import { relations, sql } from "drizzle-orm";
import {
  boolean,
  integer,
  jsonb,
  pgTable,
  primaryKey,
  text,
  timestamp,
  uuid,
  varchar,
} from "drizzle-orm/pg-core";

export const authors = pgTable("authors", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: varchar("name", { length: 256 }).notNull(),
  slug: varchar("slug", { length: 256 }).notNull().unique(),
  sourceUrl: text("source_url"),
  bio: text("bio"),
});

export const categories = pgTable("categories", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: varchar("name", { length: 256 }).notNull(),
  slug: varchar("slug", { length: 256 }).notNull().unique(),
  parentId: uuid("parent_id"),
});

export const tags = pgTable("tags", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: varchar("name", { length: 128 }).notNull(),
  slug: varchar("slug", { length: 128 }).notNull().unique(),
});

export const articles = pgTable("articles", {
  id: uuid("id").primaryKey().defaultRandom(),
  title: varchar("title", { length: 512 }).notNull(),
  slug: varchar("slug", { length: 512 }).notNull().unique(),
  bodyText: text("body_text"),
  bodyHtml: text("body_html"),
  rawHtmlR2Key: varchar("raw_html_r2_key", { length: 255 }),
  imageR2Keys: jsonb("image_r2_keys").$type<string[]>().notNull().default(sql`'[]'::jsonb`),
  excerpt: varchar("excerpt", { length: 1000 }),
  sourceUrl: text("source_url").notNull().unique(),
  authorId: uuid("author_id").references(() => authors.id),
  categoryId: uuid("category_id").references(() => categories.id),
  publishedAt: timestamp("published_at", { withTimezone: true }),
  crawledAt: timestamp("crawled_at", { withTimezone: true }).defaultNow(),
  status: varchar("status", { length: 20 }).default("draft"),
  featuredImageUrl: text("featured_image_url"),
  wordCount: integer("word_count"),
});

export const articleTags = pgTable(
  "article_tags",
  {
    articleId: uuid("article_id")
      .notNull()
      .references(() => articles.id, { onDelete: "cascade" }),
    tagId: uuid("tag_id")
      .notNull()
      .references(() => tags.id, { onDelete: "cascade" }),
  },
  (t) => [primaryKey({ columns: [t.articleId, t.tagId] })],
);

export const crawlTargets = pgTable("crawl_targets", {
  id: uuid("id").primaryKey().defaultRandom(),
  baseUrl: text("base_url").notNull().unique(),
  crawlMode: varchar("crawl_mode", { length: 20 }).notNull().default("static"),
  selectorConfig: jsonb("selector_config").$type<Record<string, unknown>>().default({}),
  maxDepth: integer("max_depth").default(2),
  isActive: boolean("is_active").default(true),
  keywords: jsonb("keywords").$type<string[]>().default([]),
  keywordMode: varchar("keyword_mode", { length: 10 }).default("any"),
  schedule: varchar("schedule", { length: 100 }),
});

export const crawlJobs = pgTable("crawl_jobs", {
  id: uuid("id").primaryKey().defaultRandom(),
  targetId: uuid("target_id")
    .notNull()
    .references(() => crawlTargets.id),
  targetUrl: text("target_url").notNull(),
  status: varchar("status", { length: 20 }).default("pending"),
  httpStatusCode: integer("http_status_code"),
  errorMessage: text("error_message"),
  articlesFound: integer("articles_found").default(0),
  startedAt: timestamp("started_at", { withTimezone: true }),
  finishedAt: timestamp("finished_at", { withTimezone: true }),
});

// ── Relations ────────────────────────────────────────────────────
// Required for the Drizzle query API (db.query.*.findMany with `with: ...`).

export const articlesRelations = relations(articles, ({ one, many }) => ({
  author: one(authors, { fields: [articles.authorId], references: [authors.id] }),
  category: one(categories, { fields: [articles.categoryId], references: [categories.id] }),
  articleTags: many(articleTags),
}));

export const articleTagsRelations = relations(articleTags, ({ one }) => ({
  article: one(articles, { fields: [articleTags.articleId], references: [articles.id] }),
  tag: one(tags, { fields: [articleTags.tagId], references: [tags.id] }),
}));

export const tagsRelations = relations(tags, ({ many }) => ({
  articleTags: many(articleTags),
}));

export const authorsRelations = relations(authors, ({ many }) => ({
  articles: many(articles),
}));

export const categoriesRelations = relations(categories, ({ many }) => ({
  articles: many(articles),
}));

// Inferred row types — used in components/pages without re-declaring shapes.
export type Author = typeof authors.$inferSelect;
export type Category = typeof categories.$inferSelect;
export type Tag = typeof tags.$inferSelect;
export type Article = typeof articles.$inferSelect;
export type CrawlTarget = typeof crawlTargets.$inferSelect;
export type NewCrawlTarget = typeof crawlTargets.$inferInsert;
