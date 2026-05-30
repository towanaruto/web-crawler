import type { CrawlScheduleConfig } from "@/db/schema";

const JST_OFFSET_MS = 9 * 60 * 60 * 1000;

export function normalizeScheduleConfig(config: CrawlScheduleConfig): CrawlScheduleConfig {
  if (config.type === "interval") {
    const value = clampInteger(config.value, 1, 365);
    if (!["minutes", "hours", "days"].includes(config.unit)) {
      throw new Error("Invalid interval unit");
    }
    if (config.unit === "minutes" && (value < 5 || value % 5 !== 0)) {
      throw new Error("Minute intervals must be in 5-minute steps");
    }
    return { type: "interval", value, unit: config.unit };
  }

  if (config.frequency === "hourly") {
    return {
      type: "fixed",
      frequency: "hourly",
      minute: minuteValue(config.minute),
    };
  }
  if (config.frequency === "daily") {
    return {
      type: "fixed",
      frequency: "daily",
      hour: clampInteger(config.hour, 0, 23),
      minute: minuteValue(config.minute),
    };
  }
  return {
    type: "fixed",
    frequency: "monthly",
    day: config.day === "last" ? "last" : clampInteger(config.day, 1, 28),
    hour: clampInteger(config.hour, 0, 23),
    minute: minuteValue(config.minute),
  };
}

export function computeNextRunAt(config: CrawlScheduleConfig, after = new Date()): Date {
  const normalized = normalizeScheduleConfig(config);
  if (normalized.type === "interval") {
    const multiplier =
      normalized.unit === "minutes"
        ? 60 * 1000
        : normalized.unit === "hours"
          ? 60 * 60 * 1000
          : 24 * 60 * 60 * 1000;
    return new Date(after.getTime() + normalized.value * multiplier);
  }

  const local = toJstParts(after);
  if (normalized.frequency === "hourly") {
    let candidate = fromJstParts(local.year, local.month, local.day, local.hour, normalized.minute);
    if (candidate <= after) {
      const next = new Date(Date.UTC(local.year, local.month, local.day, local.hour + 1));
      candidate = fromJstParts(
        next.getUTCFullYear(),
        next.getUTCMonth(),
        next.getUTCDate(),
        next.getUTCHours(),
        normalized.minute,
      );
    }
    return candidate;
  }

  if (normalized.frequency === "daily") {
    let candidate = fromJstParts(
      local.year,
      local.month,
      local.day,
      normalized.hour,
      normalized.minute,
    );
    if (candidate <= after) {
      const tomorrow = new Date(Date.UTC(local.year, local.month, local.day + 1));
      candidate = fromJstParts(
        tomorrow.getUTCFullYear(),
        tomorrow.getUTCMonth(),
        tomorrow.getUTCDate(),
        normalized.hour,
        normalized.minute,
      );
    }
    return candidate;
  }

  return nextMonthlyRun(normalized, after);
}

function nextMonthlyRun(
  config: Extract<CrawlScheduleConfig, { type: "fixed"; frequency: "monthly" }>,
  after: Date,
): Date {
  const local = toJstParts(after);
  let year = local.year;
  let month = local.month;
  for (let i = 0; i < 14; i += 1) {
    const day = config.day === "last" ? lastDayOfMonth(year, month) : config.day;
    const candidate = fromJstParts(year, month, day, config.hour, config.minute);
    if (candidate > after) {
      return candidate;
    }
    month += 1;
    if (month > 11) {
      month = 0;
      year += 1;
    }
  }
  throw new Error("Could not compute next monthly run");
}

function toJstParts(date: Date) {
  const shifted = new Date(date.getTime() + JST_OFFSET_MS);
  return {
    year: shifted.getUTCFullYear(),
    month: shifted.getUTCMonth(),
    day: shifted.getUTCDate(),
    hour: shifted.getUTCHours(),
  };
}

function fromJstParts(year: number, month: number, day: number, hour: number, minute: number): Date {
  return new Date(Date.UTC(year, month, day, hour, minute) - JST_OFFSET_MS);
}

function lastDayOfMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
}

function minuteValue(value: number): number {
  const minute = clampInteger(value, 0, 55);
  if (minute % 5 !== 0) {
    throw new Error("Minute must be in 5-minute steps");
  }
  return minute;
}

function clampInteger(value: number | string, min: number, max: number): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    throw new Error(`Value must be an integer between ${min} and ${max}`);
  }
  return parsed;
}
