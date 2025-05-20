"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";

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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { cn } from "@/lib/utils";

const upcomingFormSchema = z.object({
  sport: z.string().min(1, "Sport is required."),
  date: z.date().optional(),
  matchLinks: z.string().optional().refine(val => {
    if (val === undefined || val.trim() === "") return true; // Optional, so empty is fine
    // Check if all lines are valid URLs (basic check)
    return val.split('\n').every(line => {
      try {
        new URL(line.trim());
        return true;
      } catch (_) {
        return line.trim() === ""; // Allow empty lines
      }
    });
  }, "Each match link must be a valid URL."),
  outputFormat: z.string().min(1, "Output format is required."),
  storageType: z.string().min(1, "Storage type is required."),
  headless: z.boolean(), // Removed .default(false)
  saveLogs: z.boolean(),  // Removed .default(false)
  proxies: z.string().optional(),
});

type UpcomingFormValues = z.infer<typeof upcomingFormSchema>;

const defaultValues: UpcomingFormValues = {
  sport: "all",
  date: undefined,
  matchLinks: "",
  outputFormat: "csv",
  storageType: "local",
  headless: false,
  saveLogs: false,
  proxies: "",
};

export function UpcomingForm() {
  const form = useForm<UpcomingFormValues>({
    resolver: zodResolver(upcomingFormSchema),
    defaultValues,
    mode: "onChange",
  });

  async function onSubmit(data: UpcomingFormValues) {
    console.log("Submitting Upcoming Form:", data);
    // TODO: API call to backend
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
                    <SelectTrigger> {/* Reverted to default ShadCN style */}
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
            name="date"
            render={({ field }) => (
              <FormItem className="flex flex-col gap-2">
                <FormLabel>Date (Optional)</FormLabel>
                <Popover>
                  <PopoverTrigger asChild>
                    <FormControl>
                      <Button
                        variant={"outline"} // Default variant for such pickers
                        className={cn(
                          "w-full justify-start text-left font-normal", // Default ShadCN button text alignment
                          !field.value && "text-muted-foreground" // Default placeholder color
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" /> {/* Icon at the start */}
                        {field.value ? (
                          format(field.value, "PPP")
                        ) : (
                          <span>Pick a date</span>
                        )}
                      </Button>
                    </FormControl>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={field.value}
                      onSelect={field.onChange}
                      disabled={(date) =>
                        date < new Date("1900-01-01") // Example: disable past dates
                      }
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="matchLinks"
          render={({ field }) => (
            <FormItem className="space-y-3">
              <FormLabel>Match Links (Optional)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter one match link per line (e.g., https://www.example.com/match1)"
                  rows={3}
                  // Reverted to default ShadCN Textarea style
                  {...field}
                />
              </FormControl>
              <FormDescription className="text-slate-500">
                Provide direct links to match pages, one URL per line.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <FormField
            control={form.control}
            name="outputFormat"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Output Format</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger> {/* Reverted to default ShadCN style */}
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
                    <SelectTrigger> {/* Reverted to default ShadCN style */}
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
            <FormItem className="space-y-3">
              <FormLabel>Proxies (Optional)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="user:password@proxy.example.com:8080&#10;anotherproxy.example.com:3128"
                  rows={3}
                  // Reverted to default ShadCN Textarea style
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
              <FormItem className="flex flex-row items-center space-x-2 space-y-0"> {/* items-center for better alignment with default checkbox */}
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    // Reverted to default ShadCN Checkbox style
                  />
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
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    // Reverted to default ShadCN Checkbox style
                  />
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
          Start Scraping Upcoming Matches
        </Button>
      </form>
    </Form>
  );
}