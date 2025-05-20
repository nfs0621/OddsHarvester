"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useState } from "react";

import { api } from "@/utils/api"; // Import tRPC API
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider"; // Added Slider import

const historicFormSchema = z.object({
  sport: z.string().min(1, "Sport is required."),
  league: z.string().min(1, "League is required (e.g., nba, mlb)."),
  year: z.string().min(4, "Year must be 4 digits.").regex(/^\d{4}$/, "Year must be YYYY."),
  pagesToScrape: z.number().min(1, "Pages to scrape must be at least 1.").max(100, "Pages to scrape cannot exceed 100.").optional(),
  scrapeAllPages: z.boolean().default(false),
  outputFormat: z.string().min(1, "Output format is required."),
  storageType: z.string().min(1, "Storage type is required."),
  headless: z.boolean(),
  saveLogs: z.boolean(),
  proxies: z.string().optional(),
}).refine(data => {
  if (!data.scrapeAllPages && data.pagesToScrape === undefined) {
    return false;
  }
  return true;
}, {
  message: "Pages to scrape is required if 'Scrape all pages' is not checked.",
  path: ["pagesToScrape"],
}).refine(data => {
  const currentYear = new Date().getFullYear();
  if (parseInt(data.year, 10) > currentYear) {
    return false;
  }
  return true;
}, {
  message: "Year cannot be in the future.",
  path: ["year"],
});

type HistoricFormValues = z.infer<typeof historicFormSchema>;

// Default values for the form
const defaultValues: HistoricFormValues = { // Changed Partial<HistoricFormValues> to HistoricFormValues
  sport: "baseball", // Changed default to baseball
  league: "MLB", // Changed default to MLB
  year: "2024", // Default to 2024
  pagesToScrape: 2, // Default to 2
  scrapeAllPages: false, // Default to false
  outputFormat: "csv",
  storageType: "local",
  headless: false,
  saveLogs: false,
  proxies: "",
};

export function HistoricForm() {
  const form = useForm<HistoricFormValues>({
    resolver: zodResolver(historicFormSchema),
    defaultValues,
    mode: "onChange",
  });

  // State to track if scrapeAllPages is checked, initialized from form's default or false
  const [scrapeAllPagesChecked, setScrapeAllPagesChecked] = useState(form.getValues("scrapeAllPages") || false);

  // Watch for changes in scrapeAllPages to enable/disable slider
  const watchScrapeAllPages = form.watch("scrapeAllPages");

  // Generate year options (e.g., last 20 years)
  const currentYear = new Date().getFullYear();
  const yearOptions = Array.from({ length: 20 }, (_, i) => (currentYear - i).toString());

  const [submissionStatus, setSubmissionStatus] = useState<{ type: 'idle' | 'loading' | 'success' | 'error'; message: string }>({ type: 'idle', message: '' });

  const historicScrapeMutation = api.scrape.scrapeHistoric.useMutation({
    onMutate: () => {
      setSubmissionStatus({ type: 'loading', message: 'Submitting...' });
    },
    onSuccess: (data) => {
      console.log("Historic Scrape Success:", data);
      setSubmissionStatus({ type: 'success', message: data.message || 'Scraping initiated successfully!' });
      // form.reset(); // Optionally reset form
    },
    onError: (error) => {
      console.error("Historic Scrape Error:", error);
      setSubmissionStatus({ type: 'error', message: error.message || 'An error occurred.' });
    },
  });

  async function onSubmit(data: HistoricFormValues) {
    console.log("Submitting Historic Form:", data);
    // Ensure pagesToScrape is a number or undefined, not null if scrapeAllPages is true
    const submissionData = {
      ...data,
      pagesToScrape: data.scrapeAllPages ? undefined : (data.pagesToScrape || 2),
    };
    historicScrapeMutation.mutate(submissionData);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {submissionStatus.type !== 'idle' && (
          <div className={`p-4 rounded-md ${submissionStatus.type === 'success' ? 'bg-green-100 text-green-700' : submissionStatus.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
            {submissionStatus.message}
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-8">
          <FormField
            control={form.control}
            name="sport"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Sport</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select sport" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="all">All Sports</SelectItem>
                    <SelectItem value="basketball">Basketball</SelectItem>
                    <SelectItem value="baseball">Baseball</SelectItem>
                    <SelectItem value="hockey">Hockey</SelectItem>
                    <SelectItem value="soccer">Soccer</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="league"
            render={({ field }) => (
              <FormItem>
                <FormLabel>League (e.g., nba, mlb)</FormLabel>
                <FormControl>
                  <Input
                    placeholder="Enter league abbreviation"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Year Selector */}
        <FormField
          control={form.control}
          name="year"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Year</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select year" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {yearOptions.map(y => (
                    <SelectItem key={y} value={y}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Pages to Scrape Slider and All Pages Checkbox */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-8 items-end">
          <FormField
            control={form.control}
            name="pagesToScrape"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Pages to Scrape (1-100)</FormLabel>
                <FormControl>
                  <div className="flex items-center space-x-2">
                    <Slider
                      defaultValue={[field.value || 2]} // Default to 2 if undefined
                      min={1}
                      max={100}
                      step={1}
                      disabled={watchScrapeAllPages} // Disable if scrapeAllPages is true
                      onValueChange={(value) => field.onChange(value[0])}
                      className="w-[80%]"
                    />
                    <span className="w-[20%] text-center">
                      {watchScrapeAllPages ? 'All' : (field.value || '2')}
                    </span>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="scrapeAllPages"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center space-x-2 space-y-0 justify-start md:pt-8">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={(checked) => {
                      const isChecked = !!checked;
                      field.onChange(isChecked);
                      setScrapeAllPagesChecked(isChecked); // Update local state
                      if (isChecked) {
                        form.setValue("pagesToScrape", undefined, { shouldValidate: true });
                      } else {
                        form.setValue("pagesToScrape", 2, { shouldValidate: true });
                      }
                    }}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Scrape All Pages</FormLabel>
                </div>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-8">
          <FormField
            control={form.control}
            name="outputFormat"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Output Format</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select format" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="db">Database</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="storageType"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Storage Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select storage" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="local">Local</SelectItem>
                    <SelectItem value="s3">AWS S3</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="proxies"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Proxies (Optional, one per line)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="user:password@proxy.example.com:8080&#10;anotherproxy.example.com:3128"
                  rows={3}
                  {...field}
                />
              </FormControl>
              <FormDescription className="text-slate-500">
                Enter one proxy per line (e.g., user:pass@host:port or host:port).
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex items-start space-x-4 pt-4">
          <FormField
            control={form.control}
            name="headless"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center space-x-2 space-y-0">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Run Headless</FormLabel>
                  <FormDescription className="text-slate-500">
                    Run the browser in headless mode (no UI).
                  </FormDescription>
                </div>
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="saveLogs"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center space-x-2 space-y-0">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Save Logs</FormLabel>
                  <FormDescription className="text-slate-500">
                    Save scraping logs to a file.
                  </FormDescription>
                </div>
              </FormItem>
            )}
          />
        </div>

        <Button
          type="submit"
          className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2 px-4 rounded-md"
          disabled={historicScrapeMutation.isLoading}
        >
          {historicScrapeMutation.isLoading ? "Scraping..." : "Start Scraping Historic Odds"}
        </Button>
      </form>
    </Form>
  );
}