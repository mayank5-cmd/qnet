import type { Metadata } from 'next';
import './styles/globals.css';

export const metadata: Metadata = {
  title: 'QNet - Quantum Network Simulator',
  description: 'A production-grade quantum networking simulation framework',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white min-h-screen">
        {children}
      </body>
    </html>
  );
}
