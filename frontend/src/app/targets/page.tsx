import AddTargetForm from "@/components/AddTargetForm";
import CrawlButton from "@/components/CrawlButton";
import CrawlTargetList from "@/components/CrawlTargetList";
import { listActiveCrawlTargets, type CrawlTargetItem } from "@/db/queries";
import { requireCurrentUser } from "@/lib/current-user";

export default async function TargetsPage() {
  const user = await requireCurrentUser();
  let targets: CrawlTargetItem[] = [];
  try {
    targets = await listActiveCrawlTargets(user.id);
  } catch {
    // empty list rendered below
  }

  return (
    <div>
      <h1
        style={{
          fontSize: "var(--crawler-font-size-page)",
          fontWeight: "var(--crawler-font-weight-emphasis)",
          marginBottom: "var(--crawler-space-2)",
        }}
      >
        Crawl Targets
      </h1>
      <div
        style={{
          display: "flex",
          gap: "var(--crawler-space-2)",
          alignItems: "start",
          marginBottom: "var(--crawler-space-2)",
        }}
      >
        <AddTargetForm />
        <CrawlButton />
      </div>
      <p
        style={{
          color: "var(--crawler-text-tertiary)",
          fontSize: "var(--crawler-font-size-sm)",
          marginBottom: "var(--crawler-space-3)",
        }}
      >
        {targets.length} active targets
      </p>
      <CrawlTargetList targets={targets} />
    </div>
  );
}
