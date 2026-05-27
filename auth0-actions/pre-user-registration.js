/**
 * Auth0 Action: Pre User Registration
 *
 * Bind this to the Pre User Registration flow for the Database connection.
 * It allows email/password signup only after the user has verified an access
 * code in the app's /register page.
 *
 * Required Action secrets:
 * - BACKEND_API_URL: https://your-render-service.onrender.com
 * - BACKEND_API_TOKEN: same value as Render/Vercel BACKEND_API_TOKEN
 */
exports.onExecutePreUserRegistration = async (event, api) => {
  const email = event.user.email;
  if (!email) {
    api.access.deny("missing_email", "An email address is required.");
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
      provider: event.connection?.name || "database",
    }),
  });

  if (!res.ok) {
    api.access.deny("invite_required", "A valid access code is required.");
  }
};
