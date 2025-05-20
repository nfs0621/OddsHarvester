import { z } from "zod";
import { router, publicProcedure } from "../trpc";

// Example mutation for scraping upcoming matches
export const scrapeRouter = router({
  scrapeUpcoming: publicProcedure
    .input(
      z.object({
        sport: z.string(),
        date: z.date().optional(),
        matchLinks: z.string().optional(),
        outputFormat: z.string(),
        storageType: z.string(),
        headless: z.boolean(),
        saveLogs: z.boolean(),
        proxies: z.string().optional(),
      })
    )
    .mutation(async ({ input }) => {
      // TODO: Integrate with backend or perform scraping logic
      console.log("Scrape Upcoming Input:", input);
      return { success: true };
    }),
});