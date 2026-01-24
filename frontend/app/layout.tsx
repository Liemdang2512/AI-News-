import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Tổng hợp Tin tức - News Aggregator",
    description: "Ứng dụng tổng hợp và tóm tắt tin tức từ các báo Việt Nam",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="vi">
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body className="antialiased min-h-screen">
                {children}
            </body>
        </html>
    );
}
