import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Environment variables */
  env: {
    // Public API URL for client-side fetches (browser context)
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://47.121.183.184:1243',
    // Internal API URL for SSR (server context)
    BACKEND_URL: process.env.BACKEND_URL || 'http://47.121.183.184:1243',
  },

  /* Production optimization */
  reactStrictMode: true,

  /* Output configuration */
  output: 'standalone',

  /* Image optimization */
  images: {
    unoptimized: true, // Disable image optimization for Docker deployment
  },

  /* Experimental features */
  experimental: {
    serverActions: {
      allowedOrigins: ['47.121.183.184:1243', 'localhost:3000'],
    },
  },

  /* Webpack configuration for handling modules */
  webpack: (config, { isServer }) => {
    // Fix for module not found errors
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };
    
    return config;
  },
};

export default nextConfig;
