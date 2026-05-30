"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { updateTargetScheduleAction } from "@/app/targets/actions";
import type { CrawlTargetItem } from "@/db/queries";
import type { CrawlScheduleConfig } from "@/db/schema";

type Mode = "interval" | "fixed";
type IntervalUnit = "minutes" | "hours" | "days";
type FixedFrequency = "hourly" | "daily" | "monthly";

const minuteOptions = Array.from({ length: 12 }, (_, index) => index * 5);
const hourOptions = Array.from({ length: 24 }, (_, index) => index);
const monthDayOptions = Array.from({ length: 28 }, (_, index) => index + 1);

export default function TargetScheduleForm({ target }: { target: CrawlTargetItem }) {
  const router = useRouter();
  const initial = target.scheduleConfig;
  const [enabled, setEnabled] = useState(target.scheduleEnabled);
  const [mode, setMode] = useState<Mode>(initial?.type ?? "interval");
  const [intervalValue, setIntervalValue] = useState(
    initial?.type === "interval" ? initial.value : 1,
  );
  const [intervalUnit, setIntervalUnit] = useState<IntervalUnit>(
    initial?.type === "interval" ? initial.unit : "days",
  );
  const [frequency, setFrequency] = useState<FixedFrequency>(
    initial?.type === "fixed" ? initial.frequency : "daily",
  );
  const [minute, setMinute] = useState(initial && "minute" in initial ? initial.minute : 0);
  const [hour, setHour] = useState(initial && "hour" in initial ? initial.hour : 9);
  const [monthDay, setMonthDay] = useState<number | "last">(
    initial?.type === "fixed" && initial.frequency === "monthly" ? initial.day : 1,
  );
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSave() {
    setSaving(true);
    setMessage("");
    try {
      await updateTargetScheduleAction(target.id, {
        enabled,
        config: enabled ? buildConfig() : null,
      });
      setMessage("Saved");
      router.refresh();
    } catch {
      setMessage("Failed to save");
    } finally {
      setSaving(false);
    }
  }

  function buildConfig(): CrawlScheduleConfig {
    if (mode === "interval") {
      return { type: "interval", value: intervalValue, unit: intervalUnit };
    }
    if (frequency === "hourly") {
      return { type: "fixed", frequency: "hourly", minute };
    }
    if (frequency === "daily") {
      return { type: "fixed", frequency: "daily", hour, minute };
    }
    return { type: "fixed", frequency: "monthly", day: monthDay, hour, minute };
  }

  return (
    <div style={styles.scheduler}>
      <div style={styles.schedulerHeader}>
        <label style={styles.toggleLabel}>
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => setEnabled(event.target.checked)}
          />
          Scheduler
        </label>
        <span style={enabled ? styles.enabledText : styles.disabledText}>
          {enabled ? "On" : "Off"}
        </span>
      </div>

      {enabled && (
        <>
          <div style={styles.segmented}>
            <button
              type="button"
              onClick={() => setMode("interval")}
              style={mode === "interval" ? styles.segmentActive : styles.segment}
            >
              間隔で実行
            </button>
            <button
              type="button"
              onClick={() => setMode("fixed")}
              style={mode === "fixed" ? styles.segmentActive : styles.segment}
            >
              指定時刻で実行
            </button>
          </div>

          {mode === "interval" ? (
            <div style={styles.controls}>
              <input
                type="number"
                min={intervalUnit === "minutes" ? 5 : 1}
                max={365}
                step={intervalUnit === "minutes" ? 5 : 1}
                value={intervalValue}
                onChange={(event) => setIntervalValue(Number(event.target.value))}
                style={styles.numberInput}
              />
              <select
                value={intervalUnit}
                onChange={(event) => {
                  const unit = event.target.value as IntervalUnit;
                  setIntervalUnit(unit);
                  if (unit === "minutes" && intervalValue < 5) {
                    setIntervalValue(5);
                  }
                }}
                style={styles.select}
              >
                <option value="days">日</option>
                <option value="hours">時</option>
                <option value="minutes">分</option>
              </select>
              <span style={styles.detail}>おき</span>
            </div>
          ) : (
            <div style={styles.controls}>
              <select
                value={frequency}
                onChange={(event) => setFrequency(event.target.value as FixedFrequency)}
                style={styles.select}
              >
                <option value="hourly">毎時</option>
                <option value="daily">毎日</option>
                <option value="monthly">毎月</option>
              </select>
              {frequency === "monthly" && (
                <select
                  value={monthDay}
                  onChange={(event) =>
                    setMonthDay(event.target.value === "last" ? "last" : Number(event.target.value))
                  }
                  style={styles.select}
                >
                  {monthDayOptions.map((day) => (
                    <option key={day} value={day}>
                      {day}日
                    </option>
                  ))}
                  <option value="last">月末</option>
                </select>
              )}
              {frequency !== "hourly" && (
                <select
                  value={hour}
                  onChange={(event) => setHour(Number(event.target.value))}
                  style={styles.select}
                >
                  {hourOptions.map((value) => (
                    <option key={value} value={value}>
                      {String(value).padStart(2, "0")}時
                    </option>
                  ))}
                </select>
              )}
              <select
                value={minute}
                onChange={(event) => setMinute(Number(event.target.value))}
                style={styles.select}
              >
                {minuteOptions.map((value) => (
                  <option key={value} value={value}>
                    {String(value).padStart(2, "0")}分
                  </option>
                ))}
              </select>
            </div>
          )}
        </>
      )}

      <div style={styles.footer}>
        <span style={styles.detail}>Next: {formatJst(target.nextRunAt)}</span>
        <span style={styles.detail}>Last: {formatJst(target.lastScheduledAt)}</span>
        <button type="button" onClick={handleSave} disabled={saving} style={styles.saveBtn}>
          {saving ? "Saving..." : "Save"}
        </button>
        {message && <span style={styles.message}>{message}</span>}
      </div>
    </div>
  );
}

function formatJst(value: Date | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString("ja-JP", {
    timeZone: "Asia/Tokyo",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const styles: Record<string, React.CSSProperties> = {
  scheduler: {
    borderTop: "1px solid var(--crawler-border-subtle)",
    marginTop: "var(--crawler-space-2)",
    paddingTop: "var(--crawler-space-2)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--crawler-space-1)",
  },
  schedulerHeader: {
    display: "flex",
    alignItems: "center",
    gap: "var(--crawler-space-1)",
  },
  toggleLabel: {
    display: "flex",
    alignItems: "center",
    gap: "var(--crawler-space-1)",
    fontSize: "var(--crawler-font-size-caption)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
    color: "var(--crawler-text-primary)",
  },
  enabledText: {
    color: "var(--crawler-success-primary)",
    fontSize: "var(--crawler-font-size-micro)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  disabledText: {
    color: "var(--crawler-text-tertiary)",
    fontSize: "var(--crawler-font-size-micro)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  segmented: {
    display: "flex",
    gap: "var(--crawler-space-1)",
    flexWrap: "wrap",
  },
  segment: {
    border: "1px solid var(--crawler-border-subtle)",
    backgroundColor: "var(--crawler-surface-bg)",
    color: "var(--crawler-text-secondary)",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    fontSize: "var(--crawler-font-size-caption)",
    cursor: "pointer",
  },
  segmentActive: {
    border: "1px solid var(--crawler-accent-primary)",
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    fontSize: "var(--crawler-font-size-caption)",
    cursor: "pointer",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  controls: {
    display: "flex",
    alignItems: "center",
    gap: "var(--crawler-space-1)",
    flexWrap: "wrap",
  },
  numberInput: {
    width: "calc(var(--crawler-space-5) * 2)",
    padding: "var(--crawler-space-1)",
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-md)",
    fontSize: "var(--crawler-font-size-caption)",
  },
  select: {
    padding: "var(--crawler-space-1)",
    border: "1px solid var(--crawler-border-subtle)",
    borderRadius: "var(--crawler-radius-md)",
    fontSize: "var(--crawler-font-size-caption)",
    backgroundColor: "var(--crawler-surface-bg)",
  },
  footer: {
    display: "flex",
    alignItems: "center",
    gap: "var(--crawler-space-1)",
    flexWrap: "wrap",
  },
  detail: {
    color: "var(--crawler-text-tertiary)",
    fontSize: "var(--crawler-font-size-caption)",
  },
  saveBtn: {
    backgroundColor: "var(--crawler-accent-primary)",
    color: "var(--crawler-text-on-accent)",
    border: "none",
    borderRadius: "var(--crawler-radius-pill)",
    padding: "var(--crawler-space-1) var(--crawler-space-2)",
    cursor: "pointer",
    fontSize: "var(--crawler-font-size-caption)",
    fontWeight: "var(--crawler-font-weight-emphasis)",
  },
  message: {
    color: "var(--crawler-text-secondary)",
    fontSize: "var(--crawler-font-size-caption)",
  },
};
