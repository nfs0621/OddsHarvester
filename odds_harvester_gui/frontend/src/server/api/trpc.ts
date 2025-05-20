import { initTRPC } from "@trpc/server";

// You can extend this context as needed
export const createTRPCContext = () => ({});

const t = initTRPC.context<typeof createTRPCContext>().create();

export const router = t.router;
export const publicProcedure = t.procedure;