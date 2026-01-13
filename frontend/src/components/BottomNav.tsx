'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Calendar, Map, Compass, User, Globe } from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', icon: Calendar, label: 'Today' },
  { href: '/journey', icon: Map, label: 'Journey' },
  { href: '/map', icon: Globe, label: 'Map' },
  { href: '/discover', icon: Compass, label: 'Discover' },
  { href: '/profile', icon: User, label: 'Profile' },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-zinc-900/95 backdrop-blur-sm border-t border-zinc-800 z-40 lg:hidden">
      <div className="max-w-lg mx-auto flex items-center justify-around py-2">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
          // For root path, require exact match; for others, use startsWith
          const isActive = href === '/'
            ? pathname === '/'
            : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'text-emerald-400'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs">{label}</span>
            </Link>
          );
        })}
      </div>
      {/* Safe area padding for iOS */}
      <div className="h-safe-area-inset-bottom bg-zinc-900" />
    </nav>
  );
}
