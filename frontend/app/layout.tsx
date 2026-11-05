import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "CampusNet · Goa College of Engineering", description: "Campus network authentication operations console" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
