"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

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

const historicFormSchema = z.object({
  sport: z.string().min(1, "Sport is required."),
  league: z.string().min(1, "League is required (e.g., nba, mlb)."),
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Start date must be YYYY-MM-DD."),
  endDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "End date must be YYYY-MM-DD."),
  outputFormat: z.string().min(1, "Output format is required."),
  storageType: z.string().min(1, "Storage type is required."),
  headless: z.boolean(), // Removed .default(false)
  saveLogs: z.boolean(),  // Removed .default(false)
  proxies: z.string().optional(),
}).refine(data => {
  if (data.startDate && data.endDate) {
    return new Date(data.startDate) <= new Date(data.endDate);
  }
  return true;
}, {
  message: "Start date must be before or the same as end date.",
  path: ["endDate"], // Path to show the error message on
});

type HistoricFormValues = z.infer<typeof historicFormSchema>;

// Default values for the form
const defaultValues: HistoricFormValues = { // Use HistoricFormValues directly
  sport: "all",
  league: "",
  startDate: "", // Will be validated by Zod for format
  endDate: "",   // Will be validated by Zod for format
  outputFormat: "csv",
  storageType: "local",
  headless: false, // Explicitly false
  saveLogs: false, // Explicitly false
  proxies: "",     // Zod schema has .optional(), so empty string is fine
};

export function HistoricForm() {
  const form = useForm<HistoricFormValues>({
    resolver: zodResolver(historicFormSchema),
    defaultValues,
    mode: "onChange", // Validate on change for better UX
  });

  async function onSubmit(data: HistoricFormValues) {
    console.log("Submitting Historic Form:", data);
    // TODO: API call to backend
    // Example:
    // try {
    //   const response = await fetch('/api/scrape_historic', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(data),
    //   });
    //   const result = await response.json();
    //   console.log('API Response:', result);
    //   // form.reset(); // Optionally reset form on success
    // } catch (error) {
    //   console.error('API Error:', error);
    //   // Handle error display to user, e.g., using form.setError
    // }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-8">
          <FormField
            control={form.control}
            name="sport"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Sport</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    {/* Only one child allowed in FormControl */}
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
                    {...Object.fromEntries(Object.entries(field).filter(([k]) => k !== "children"))}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-8">
          <FormField
            control={form.control}
            name="startDate"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Start Date (YYYY-MM-DD)</FormLabel>
                <FormControl>
                  <Input
                    type="date"
                    {...Object.fromEntries(Object.entries(field).filter(([k]) => k !== "children"))}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="endDate"
            render={({ field }) => (
              <FormItem>
                <FormLabel>End Date (YYYY-MM-DD)</FormLabel>
                <FormControl>
                  <Input
                    type="date"
                    {...Object.fromEntries(Object.entries(field).filter(([k]) => k !== "children"))}
                  />
                </FormControl>
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
                    {/* Only one child allowed in FormControl */}
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
                    {/* Only one child allowed in FormControl */}
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
                {(() => {
                  // Debug log to catch multiple children
                  const child = (
                    <Textarea
                      placeholder="user:password@proxy.example.com:8080&#10;anotherproxy.example.com:3128"
                      rows={3}
                      {...Object.fromEntries(Object.entries(field).filter(([k]) => k !== "children"))}
                    />
                  );
                  // @ts-ignore
                  if (Array.isArray(child)) {
                    // eslint-disable-next-line no-console
                    console.error("FormControl received multiple children in proxies field", child);
                  }
                  return child;
                })()}
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
              <FormItem className="flex flex-row items-center space-x-2 space-y-0"> {/* items-center for better alignment */}
                <FormControl>
                  {(() => {
                    // Debug log to catch multiple children
                    const child = (
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    );
                    // @ts-ignore
                    if (Array.isArray(child)) {
                      // eslint-disable-next-line no-console
                      console.error("FormControl received multiple children in headless field", child);
                    }
                    return child;
                  })()}
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Run Headless</FormLabel> {/* Default weight */}
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
              <FormItem className="flex flex-row items-center space-x-2 space-y-0"> {/* items-center for better alignment */}
                <FormControl>
                  {(() => {
                    // Debug log to catch multiple children
                    const child = (
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    );
                    // @ts-ignore
                    if (Array.isArray(child)) {
                      // eslint-disable-next-line no-console
                      console.error("FormControl received multiple children in saveLogs field", child);
                    }
                    return child;
                  })()}
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Save Logs</FormLabel> {/* Default weight */}
                  <FormDescription className="text-slate-500">
                    Save scraping logs to a file.
                  </FormDescription>
                </div>
              </FormItem>
            )}
          />
        </div>

        <Button type="submit" className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2 px-4 rounded-md">
          Start Scraping Historic Odds
        </Button>
      </form>
    </Form>
  );
}