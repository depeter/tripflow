'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Calendar, Map, Compass, User, Navigation, Globe } from 'lucide-react';
import { getTrips, type Trip } from '@/services/tripService';

const NAV_ITEMS = [
  { href: '/', icon: Calendar, label: 'Today' },
  { href: '/journey', icon: Map, label: 'Journey' },
  { href: '/map', icon: Globe, label: 'Explore Map' },
  { href: '/discover', icon: Compass, label: 'Discover' },
  { href: '/profile', icon: User, label: 'Profile' },
];

export function Sidebar() {
  const pathname = usePathname();
  const [activeTrip, setActiveTrip] = useState<Trip | null>(null);

  useEffect(() => {
    async function fetchActiveTrip() {
      try {
        const trips = await getTrips();
        const active = trips.find(t => t.status === 'active') || trips[0] || null;
        setActiveTrip(active);
      } catch (error) {
        // User not logged in or no trips - that's fine
        setActiveTrip(null);
      }
    }
    fetchActiveTrip();
  }, []);

  // Calculate trip info
  const getTripInfo = () => {
    if (!activeTrip) return null;

    const name = activeTrip.name ||
      (activeTrip.start_address && activeTrip.end_address
        ? `${activeTrip.start_address.split(',')[0]} to ${activeTrip.end_address.split(',')[0]}`
        : 'My Trip');

    let dayInfo = '';
    if (activeTrip.start_date) {
      const startDate = new Date(activeTrip.start_date);
      const today = new Date();
      const daysDiff = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
      const currentDay = Math.max(1, daysDiff + 1);
      dayInfo = `Day ${currentDay}`;
      if (activeTrip.max_distance_km) {
        dayInfo += ` - ${activeTrip.max_distance_km}km`;
      }
    }

    return { name, dayInfo };
  };

  const tripInfo = getTripInfo();

  return (
    <aside className="hidden lg:flex flex-col w-64 bg-zinc-900 border-r border-zinc-800 h-screen fixed left-0 top-0">
      {/* Logo */}
      <div className="p-6 border-b border-zinc-800">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
            <Navigation className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-zinc-100">TripFlow</h1>
            <p className="text-xs text-zinc-500">Travel Companion</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {NAV_ITEMS.map(({ href, icon: Icon, label }) => {
            // For root path, require exact match; for others, use startsWith
            const isActive = href === '/'
              ? pathname === '/'
              : pathname.startsWith(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                    isActive
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-zinc-800">
        <div className="px-4 py-3 rounded-xl bg-zinc-800/50">
          <p className="text-xs text-zinc-500">Current Trip</p>
          {tripInfo ? (
            <>
              <p className="text-sm text-zinc-300 font-medium truncate">{tripInfo.name}</p>
              {tripInfo.dayInfo && (
                <p className="text-xs text-zinc-500 mt-1">{tripInfo.dayInfo}</p>
              )}
            </>
          ) : (
            <p className="text-sm text-zinc-400 italic">No active trip</p>
          )}
        </div>
      </div>
    </aside>
  );
}
