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
  index,
  integer,
  jsonb,
  pgTable,
  primaryKey,
  text,
  timestamp,
  uniqueIndex,
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

export const users = pgTable(
  "users",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    auth0Sub: varchar("auth0_sub", { length: 255 }).notNull().unique(),
    email: varchar("email", { length: 320 }).notNull(),
    name: varchar("name", { length: 256 }),
    pictureUrl: text("picture_url"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  },
  (t) => [index("ix_users_email").on(t.email)],
);

export const invites = pgTable(
  "invites",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    email: varchar("email", { length: 320 }).notNull(),
    codeHash: varchar("code_hash", { length: 128 }).notNull().unique(),
    expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
    verifiedAt: timestamp("verified_at", { withTimezone: true }),
    usedAt: timestamp("used_at", { withTimezone: true }),
    usedByUserId: uuid("used_by_user_id").references(() => users.id),
    usedByAuth0Sub: varchar("used_by_auth0_sub", { length: 255 }),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  },
  (t) => [index("ix_invites_email").on(t.email)],
);

export const articles = pgTable("articles", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id),
  title: varchar("title", { length: 512 }).notNull(),
  slug: varchar("slug", { length: 512 }).notNull(),
  bodyText: text("body_text"),
  bodyHtml: text("body_html"),
  rawHtmlR2Key: varchar("raw_html_r2_key", { length: 255 }),
  imageR2Keys: jsonb("image_r2_keys").$type<string[]>().notNull().default(sql`'[]'::jsonb`),
  excerpt: varchar("excerpt", { length: 1000 }),
  sourceUrl: text("source_url").notNull(),
  authorId: uuid("author_id").references(() => authors.id),
  categoryId: uuid("category_id").references(() => categories.id),
  publishedAt: timestamp("published_at", { withTimezone: true }),
  crawledAt: timestamp("crawled_at", { withTimezone: true }).defaultNow(),
  status: varchar("status", { length: 20 }).default("draft"),
  featuredImageUrl: text("featured_image_url"),
  wordCount: integer("word_count"),
}, (t) => [
  uniqueIndex("uq_articles_user_source_url").on(t.userId, t.sourceUrl),
  uniqueIndex("uq_articles_user_slug").on(t.userId, t.slug),
  index("ix_articles_user_crawled_at").on(t.userId, t.crawledAt),
]);

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
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id),
  baseUrl: text("base_url").notNull(),
  crawlMode: varchar("crawl_mode", { length: 20 }).notNull().default("static"),
  selectorConfig: jsonb("selector_config").$type<Record<string, unknown>>().default({}),
  maxDepth: integer("max_depth").default(2),
  isActive: boolean("is_active").default(true),
  keywords: jsonb("keywords").$type<string[]>().default([]),
  keywordMode: varchar("keyword_mode", { length: 10 }).default("any"),
}, (t) => [
  uniqueIndex("uq_crawl_targets_user_base_url").on(t.userId, t.baseUrl),
  index("ix_crawl_targets_user_active").on(t.userId, t.isActive),
]);

export const crawlJobs = pgTable("crawl_jobs", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id),
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
}, (t) => [index("ix_crawl_jobs_user_started_at").on(t.userId, t.startedAt)]);

// ── Relations ────────────────────────────────────────────────────
// Required for the Drizzle query API (db.query.*.findMany with `with: ...`).

export const articlesRelations = relations(articles, ({ one, many }) => ({
  user: one(users, { fields: [articles.userId], references: [users.id] }),
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

export const usersRelations = relations(users, ({ many }) => ({
  articles: many(articles),
  crawlTargets: many(crawlTargets),
  crawlJobs: many(crawlJobs),
}));

// Inferred row types — used in components/pages without re-declaring shapes.
export type Author = typeof authors.$inferSelect;
export type Category = typeof categories.$inferSelect;
export type Tag = typeof tags.$inferSelect;
export type User = typeof users.$inferSelect;
export type Invite = typeof invites.$inferSelect;
export type Article = typeof articles.$inferSelect;
export type CrawlTarget = typeof crawlTargets.$inferSelect;
export type NewCrawlTarget = typeof crawlTargets.$inferInsert;
