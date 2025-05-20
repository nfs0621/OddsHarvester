import { z } from "zod";
import { router, publicProcedure } from "../trpc";
import { spawn } from "child_process";
import path from "path";
import fs from "fs/promises";

// Define the project root. This assumes the tRPC router is some levels deep from project root.
// Adjust if Next.js CWD is different.
// If CWD of Next.js server is odds_harvester_gui/frontend/
const projectRoot = path.resolve(process.cwd(), "../..");
// If CWD of Next.js server is project root (c:/Projects/OddsHarvester)
// const projectRoot = process.cwd();


export const scrapeRouter = router({
  scrapeUpcoming: publicProcedure
    .input(
      z.object({
        sport: z.string(),
        date: z.date().optional(), // This should likely be string if coming from form
        matchLinks: z.string().optional(),
        outputFormat: z.string(),
        storageType: z.string(),
        headless: z.boolean(),
        saveLogs: z.boolean(),
        proxies: z.string().optional(),
      })
    )
    .mutation(async ({ input }) => {
      // TODO: Implement actual scraping logic for upcoming matches
      console.log("Scrape Upcoming Input:", input);
      return { success: true, message: "Upcoming scrape initiated (mock)" };
    }),

  scrapeHistoric: publicProcedure
    .input(
      z.object({
        sport: z.string(),
        league: z.string(),
        year: z.string().regex(/^\d{4}$/, "Year must be YYYY format"),
        pagesToScrape: z.number().int().min(1).optional(),
        scrapeAllPages: z.boolean(),
        outputFormat: z.string(), // e.g., "csv", "json"
        storageType: z.string(), // e.g., "local", "s3"
        headless: z.boolean(),
        saveLogs: z.boolean(), // For the python script's own logging
        proxies: z.string().optional(), // Newline-separated string
      })
    )
    .mutation(async ({ input }) => {
      console.log("Received scrapeHistoric input:", input);

      const pythonExecutable = "python"; // Assumes python is in PATH, or use absolute path
      // To run as a module, we specify the module path, not the file path.
      // The command will be `python -m src.main ...`
      const modulePath = "src.main";

      // The first part of args for spawn when using -m is the module path,
      // then the script's own arguments.
      const scriptArgs: string[] = ["scrape_historic"];

      scriptArgs.push("--sport", input.sport);

      let leagueArg = input.league;
      let seasonArg = "";

      if (input.sport.toLowerCase() === "baseball") {
        leagueArg = input.league.toLowerCase(); // Expects "mlb"
        seasonArg = input.year; // Expects "YYYY" for baseball
      } else {
        // For other sports, assume YYYY-YYYY season format is correct
        const startYear = parseInt(input.year, 10);
        seasonArg = `${startYear}-${startYear + 1}`;
      }
      scriptArgs.push("--league", leagueArg);
      scriptArgs.push("--season", seasonArg);

      if (!input.scrapeAllPages && input.pagesToScrape) {
        scriptArgs.push("--max_pages", input.pagesToScrape.toString());
      }

      scriptArgs.push("--storage", input.storageType);
      scriptArgs.push("--format", input.outputFormat);

      if (input.headless) {
        scriptArgs.push("--headless");
      }
      if (input.saveLogs) {
        scriptArgs.push("--save_logs"); // Python script handles its log saving
      }

      if (input.proxies && input.proxies.trim() !== "") {
        const proxyList = input.proxies.trim().split(/\r?\n/).filter(p => p.trim() !== "");
        if (proxyList.length > 0) {
          scriptArgs.push("--proxies", ...proxyList);
        }
      }
      
      // The following block correctly adds file_path to scriptArgs.
      // The erroneous line `args.push("--file_path", relativeFilePath)` has been removed.
      
      // Add file_path to scriptArgs if local storage
      if (input.storageType.toLowerCase() === "local") {
        const dataDir = path.join(projectRoot, "scraped_data");
        try {
          await fs.mkdir(dataDir, { recursive: true });
        } catch (err) {
          console.error("Failed to create scraped_data directory:", err);
        }
        // Use the potentially modified leagueArg and seasonArg for filename
        const filename = `historic_odds_${input.sport}_${leagueArg}_${seasonArg}.${input.outputFormat}`;
        const relativeFilePath = path.join("scraped_data", filename);
        scriptArgs.push("--file_path", relativeFilePath); // Add to scriptArgs
      }


      console.log(`Executing: uv run ${pythonExecutable} -m ${modulePath} ${scriptArgs.join(" ")} in ${projectRoot}`);

      return new Promise((resolve, reject) => {
        // For `python -m src.main`, the arguments to spawn are:
        // command: "uv"
        // args for uv: ["run", "python", "-m", "src.main", ...scriptArgs]
        const process = spawn("uv", ["run", pythonExecutable, "-m", modulePath, ...scriptArgs], { cwd: projectRoot });

        let stdout = "";
        let stderr = "";

        process.stdout.on("data", (data) => {
          stdout += data.toString();
          console.log("Python script stdout:", data.toString());
        });

        process.stderr.on("data", (data) => {
          stderr += data.toString();
          // Note: `uv run` might output "Building <package>..." to stderr initially.
          // This is not an error if the script subsequently succeeds (exit code 0).
          console.error("Python script stderr:", data.toString());
        });

        process.on("close", (code) => {
          console.log(`Python script exited with code ${code}`);
          if (code === 0) {
            resolve({
              success: true,
              // Use the potentially modified leagueArg and seasonArg for message
              message: `Historic scraping for ${leagueArg} (${seasonArg}) completed. See server logs for script output.`,
              stdout: stdout,
              stderr: stderr, // Stderr from uv/python, may include build messages
            });
          } else {
            reject(new Error(
              `Scraping script failed with code ${code}. Error:\n${stderr || "Unknown error"}\nStdout:\n${stdout}`
            ));
          }
        });

        process.on("error", (err) => {
          console.error("Failed to start Python script:", err);
          reject(new Error(`Failed to start scraping script: ${err.message}`));
        });
      });
    }),
});