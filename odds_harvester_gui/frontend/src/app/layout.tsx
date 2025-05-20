import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css"; // Ensure globals.css is imported
import { ThemeProvider } from "@/components/theme-provider"; // Added ThemeProvider import

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OddsHarvester GUI",
  description: "GUI for OddsHarvester scraping tasks",
};

import { TRPCProvider } from "@/utils/trpcProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <TRPCProvider>
            {children}
          </TRPCProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}