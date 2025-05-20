import { router } from "../trpc";
import { scrapeRouter } from "./scrape";

export const appRouter = router({
  scrape: scrapeRouter,
});

// Export type definition of API
export type AppRouter = typeof appRouter;