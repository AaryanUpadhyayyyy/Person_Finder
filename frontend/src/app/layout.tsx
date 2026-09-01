import type { Metadata } from "next";
import { Geist, Geist_Mono, Leckerli_One } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const leckerliOne = Leckerli_One({
  weight: "400",
  variable: "--font-leckerli-one",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Talaash - Identity Scanner",
  description: "Face Identification & Blockchain Verification",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${leckerliOne.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
