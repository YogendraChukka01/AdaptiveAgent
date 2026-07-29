import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-bold">404</h1>
        <p className="text-[var(--text-secondary)]">Page not found</p>
        <Link
          href="/"
          className="text-[var(--accent)] hover:underline"
        >
          Go home
        </Link>
      </div>
    </div>
  );
}
