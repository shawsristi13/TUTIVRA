import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/components/SessionProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TUTIVRA — AI Teacher",
  description:
    "An adaptive AI Teacher that understands, plans, explains, demonstrates, questions, evaluates, adapts and teaches.",
  openGraph: {
    title: "TUTIVRA — AI Teacher",
    description: "Personalized AI-powered education through video, voice and interaction.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#0a0a16] text-slate-100 min-h-screen`}>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
