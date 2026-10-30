import "./globals.css";

export const metadata = {
  title: "Northstar Shop | Shopping Help & Customer Support",
  description: "Northstar Shop is an online store for everyday products and accessories. Get help with orders, delivery, returns, refunds, payments, and your account.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head><link href="https://api.fontshare.com/v2/css?f[]=general-sans@400,500,600&display=swap" rel="stylesheet" /></head>
      <body>{children}</body>
    </html>
  );
}
