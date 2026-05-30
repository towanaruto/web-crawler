export interface Env {
  BACKEND_API_URL: string;
  BACKEND_API_TOKEN: string;
}

export default {
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(runSchedulerTick(env));
  },

  async fetch(_request: Request): Promise<Response> {
    return new Response("ok");
  },
};

async function runSchedulerTick(env: Env): Promise<void> {
  const url = new URL("/scheduler/tick", env.BACKEND_API_URL);
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-Internal-Api-Key": env.BACKEND_API_TOKEN,
    },
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`Scheduler tick failed: ${response.status} ${body}`);
  }
}
