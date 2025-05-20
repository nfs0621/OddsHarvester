import { createNextApiHandler } from "@trpc/server/adapters/next";
import { appRouter } from "@/server/api/routers/_app";

// Export API handler
export default createNextApiHandler({
  router: appRouter,
  createContext: () => ({}),
});