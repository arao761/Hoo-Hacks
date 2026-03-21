import { defineConfig, Plugin } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { createServer } from "./server";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "localhost",
    port: 8080,
    fs: {
      allow: ["./", "./client", "./shared", "./public"],
      deny: [".env", ".env.*", "*.{crt,pem}", "**/.git/**"],
    },
    proxy: {
      "/generate": { target: "http://localhost:8000", changeOrigin: true },
      "/output":   { target: "http://localhost:8000", changeOrigin: true },
      "/status":   { target: "http://localhost:8000", changeOrigin: true },
      "/health":   { target: "http://localhost:8000", changeOrigin: true },
      "/ws":       { target: "ws://localhost:8000",   changeOrigin: true, ws: true },
    },
  },
  build: {
    outDir: "dist/spa",
  },
  plugins: [react(), expressPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./client"),
      "@shared": path.resolve(__dirname, "./shared"),
    },
  },
}));

function expressPlugin(): Plugin {
  return {
    name: "express-plugin",
    apply: "serve", // Only apply during development (serve mode)
    configureServer(server) {
      const app = createServer();

      // Add Express app as middleware to Vite dev server
      server.middlewares.use(app);
    },
  };
}
