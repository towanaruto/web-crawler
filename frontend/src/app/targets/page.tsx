import { fetchCrawlTargets } from "@/lib/api";
import CrawlTargetList from "@/components/CrawlTargetList";
import AddTargetForm from "@/components/AddTargetForm";
import CrawlButton from "@/components/CrawlButton";

export default async function TargetsPage() {
  let targets;
  try {
    targets = await fetchCrawlTargets();
  } catch {
    targets = [];
  }

  return (
    <div>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 16 }}>
        Crawl Targets
      </h1>
      <div style={{ display: "flex", gap: 12, alignItems: "start", marginBottom: 16 }}>
        <AddTargetForm />
        <CrawlButton />
      </div>
      <p style={{ color: "#888", fontSize: 14, marginBottom: 24 }}>
        {targets.length} active targets
      </p>
      <CrawlTargetList targets={targets} />
    </div>
  );
}
