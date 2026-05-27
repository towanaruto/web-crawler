/**
 * Auth0 Action: Post Login
 *
 * Bind this to the Login flow. Social providers such as Google do not run the
 * Pre User Registration trigger, so this denies first-time social logins unless
 * /register has already verified an invite for the same email address.
 *
 * Required Action secrets:
 * - BACKEND_API_URL: https://your-render-service.onrender.com
 * - BACKEND_API_TOKEN: same value as Render/Vercel BACKEND_API_TOKEN
 */
exports.onExecutePostLogin = async (event, api) => {
  const email = event.user.email;
  const auth0Sub = event.user.user_id;
  if (!email || !auth0Sub) {
    api.access.deny("missing_identity", "A valid identity is required.");
    return;
  }

  const loginCount = event.stats?.logins_count || 0;
  const isSocial = event.user.identities?.some((identity) => identity.isSocial);
  if (!isSocial) {
    return;
  }
  if (loginCount > 1) {
    return;
  }

  const res = await fetch(`${event.secrets.BACKEND_API_URL}/auth/invites/consume`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Api-Key": event.secrets.BACKEND_API_TOKEN,
    },
    body: JSON.stringify({
      email,
      auth0_sub: auth0Sub,
      provider: event.connection?.name || "login",
    }),
  });

  if (!res.ok) {
    api.access.deny("invite_required", "A valid access code is required.");
  }
};
