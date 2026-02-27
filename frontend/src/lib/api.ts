const API_BASE =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://backend:8000"
    : "";

// On client side, proxy through Next.js rewrites (or use direct URL)
const CLIENT_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getBaseUrl() {
  if (typeof window === "undefined") {
    return API_BASE;
  }
  return CLIENT_API_BASE;
}

export interface Author {
  id: string;
  name: string;
  slug: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
}

export interface Tag {
  id: string;
  name: string;
  slug: string;
}

export interface Article {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  source_url: string;
  author: Author | null;
  category: Category | null;
  tags: Tag[];
  published_at: string | null;
  featured_image_url: string | null;
  word_count: number | null;
  status: string;
}

export interface ArticleDetail extends Article {
  body_html: string | null;
  body_text: string | null;
  crawled_at: string | null;
}

export interface PaginatedArticles {
  items: Article[];
  total: number;
  offset: number;
  limit: number;
}

export async function fetchArticles(
  offset = 0,
  limit = 20,
  category?: string
): Promise<PaginatedArticles> {
  const params = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  });
  if (category) params.set("category", category);
  const res = await fetch(`${getBaseUrl()}/api/articles?${params}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchArticle(slug: string): Promise<ArticleDetail> {
  const res = await fetch(`${getBaseUrl()}/api/articles/${slug}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchCategories(): Promise<Category[]> {
  const res = await fetch(`${getBaseUrl()}/api/categories`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
