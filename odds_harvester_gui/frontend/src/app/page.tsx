"use client";

import { UpcomingForm } from "@/components/forms/UpcomingForm";
import { HistoricForm } from "@/components/forms/HistoricForm";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Terminal } from "lucide-react"; // Removed Moon, Sun, useTheme as they are in ThemeToggleButton
// import { Button } from "@/components/ui/button"; // Button is used in ThemeToggleButton
import { ThemeToggleButton } from "@/components/theme-toggle-button"; // Import the new toggle button

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 bg-white text-slate-900 dark:bg-dark-bg dark:text-dark-text-primary transition-colors duration-300">
      <div className="w-full max-w-3xl mx-auto flex flex-col min-h-screen relative"> {/* Adjusted max-width */}
        <div className="absolute top-4 right-4 z-10"> {/* Adjusted positioning */}
          <ThemeToggleButton />
        </div>
        {/* Hero Section */}
        <header className="pt-12 pb-8 md:pt-20 md:pb-12 mb-8 text-center flex flex-col items-center"> {/* Adjusted padding and margin */}
          <Avatar className="h-20 w-20 md:h-24 md:w-24 mb-5 shadow-lg border-2 border-slate-200 dark:border-dark-border bg-white dark:bg-dark-card">
            <AvatarImage src="/favicon.ico" alt="OddsHarvester Logo" />
            <AvatarFallback className="text-2xl md:text-3xl font-semibold text-slate-700 dark:text-dark-text-secondary">OH</AvatarFallback>
          </Avatar>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-800 dark:text-dark-text-primary mb-3">
            OddsHarvester
          </h1>
          <p className="text-lg md:text-xl text-slate-600 dark:text-dark-text-secondary font-normal mb-5 max-w-md">
            Automate your odds scraping workflows.
          </p>
          <p className="text-2xl md:text-3xl text-slate-700 dark:text-dark-accent font-semibold">
            Fast. Reliable. Intuitive.
          </p>
        </header>

        <div className="mb-10 p-4 border-l-4 border-dark-primary dark:border-dark-accent bg-slate-50 dark:bg-dark-card rounded-md shadow">
          <h2 className="font-semibold text-lg text-slate-800 dark:text-dark-text-primary mb-1">Welcome to OddsHarvester GUI</h2>
          <p className="text-slate-600 dark:text-dark-text-secondary text-sm">
            Use the tabs below to start scraping upcoming or historic odds. Configure your options and launch your workflow in seconds.
          </p>
        </div>


        <Tabs defaultValue="historic" className="w-full flex-1 flex flex-col mb-10">
          <TabsList className="grid w-full grid-cols-2 bg-slate-100 dark:bg-dark-card p-1 rounded-lg h-auto mb-6 shadow-sm">
            <TabsTrigger value="upcoming" className="py-2.5 text-sm font-medium text-slate-600 dark:text-dark-text-secondary data-[state=active]:bg-dark-primary dark:data-[state=active]:bg-dark-primary data-[state=active]:text-white dark:data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-150 ease-in-out">
              Scrape Upcoming
            </TabsTrigger>
            <TabsTrigger value="historic" className="py-2.5 text-sm font-medium text-slate-600 dark:text-dark-text-secondary data-[state=active]:bg-dark-primary dark:data-[state=active]:bg-dark-primary data-[state=active]:text-white dark:data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-150 ease-in-out">
              Scrape Historic
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming">
            <Card className="bg-white dark:bg-dark-card shadow-lg dark:shadow-xl rounded-lg border border-slate-200 dark:border-dark-border">
              <CardHeader className="p-5 pb-3">
                <CardTitle className="text-xl md:text-2xl font-semibold text-slate-700 dark:text-dark-text-primary">Scrape Upcoming Matches</CardTitle>
                <CardDescription className="text-slate-500 dark:text-dark-text-secondary pt-1 text-sm">
                  Configure and start scraping for upcoming sports matches.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 pt-2">
                <UpcomingForm />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="historic">
            <Card className="bg-white dark:bg-dark-card shadow-lg dark:shadow-xl rounded-lg border border-slate-200 dark:border-dark-border">
              <CardHeader className="p-5 pb-3">
                <CardTitle className="text-xl md:text-2xl font-semibold text-slate-700 dark:text-dark-text-primary">Scrape Historic Odds</CardTitle>
                <CardDescription className="text-slate-500 dark:text-dark-text-secondary pt-1 text-sm">
                  Configure and start scraping for historic sports odds data.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 pt-2">
                <HistoricForm />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>


        {/* Footer */}
        <footer className="text-center text-xs text-slate-500 dark:text-dark-text-secondary py-6 mt-auto border-t border-slate-200 dark:border-dark-border">
          <span>
            &copy; {new Date().getFullYear()} OddsHarvester. Built with{" "}
            <a href="https://ui.shadcn.com/" className="underline text-dark-primary hover:text-dark-secondary dark:text-dark-accent dark:hover:text-dark-primary font-medium" target="_blank" rel="noopener noreferrer">
              ShadCN UI
            </a>
            .
          </span>
        </footer>
      </div>
    </main>
  );
}