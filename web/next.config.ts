import type { NextConfig } from 'next';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  // Prevent Turbopack from picking a parent lockfile outside this app (breaks /api/token).
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
