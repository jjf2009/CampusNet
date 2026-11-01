import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "CampusNet", description: "Campus network operations console" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }

