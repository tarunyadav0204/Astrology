import './globals.css';

export const metadata = {
  metadataBase: new URL('https://astroroshni.com'),
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
