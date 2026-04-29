/** @type {import('next').NextConfig} */

// Allow next/image to load from the R2 public bucket. We parse R2_PUBLIC_URL at
// build time so missing/typo'd env vars surface as a build error instead of a
// silent 404 in the browser.
const remotePatterns = [];
if (process.env.R2_PUBLIC_URL) {
  try {
    const url = new URL(process.env.R2_PUBLIC_URL);
    remotePatterns.push({
      protocol: url.protocol.replace(":", ""),
      hostname: url.hostname,
      pathname: "/**",
    });
  } catch {
    throw new Error(`R2_PUBLIC_URL is not a valid URL: ${process.env.R2_PUBLIC_URL}`);
  }
}

const nextConfig = {
  output: "standalone",
  images: { remotePatterns },
};

module.exports = nextConfig;
