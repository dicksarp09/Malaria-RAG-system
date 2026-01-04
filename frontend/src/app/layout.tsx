import './globals.css';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: "Evidence Portal | Malaria Research",
  description: "Evidence-backed malaria research assistant for clinical analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="antialiased">
      <body className={`${inter.className} bg-[#F8F9FA] text-slate-900`}>
        {children}
      </body>
    </html>
  );
}
