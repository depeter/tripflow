'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { ArrowLeft, Settings, Plus, Loader2, MapPin, Trash2, X } from 'lucide-react';
import Link from 'next/link';
import { CollapsibleSection } from '@/components/CollapsibleSection';
import { JourneyProgress } from '@/components/JourneyProgress';
import { WaypointList } from '@/components/WaypointList';
import { useJourneyState } from '@/hooks/useJourneyState';
import { createTrip, type Trip } from '@/services/tripService';
import type { JourneyWaypoint } from '@/types/journey';

// Dynamic import for the map (no SSR)
const JourneyMap = dynamic(() => import('@/components/JourneyMap'), {
  ssr: false,
  loading: () => <div className="h-[300px] lg:h-full bg-zinc-800 rounded-xl animate-pulse" />,
});

export default function JourneyPage() {
  const {
    journey,
    stats,
    currentPosition,
    isLoading,
    error,
    trips,
    activeTripId,
    markVisited,
    markSkipped,
    deleteTrip,
    refetchTrips,
  } = useJourneyState();

  // Get the active trip object for delete confirmation
  const activeTrip = trips.find(t => t.id === activeTripId) || null;

  const [selectedWaypoint, setSelectedWaypoint] = useState<JourneyWaypoint | null>(null);
  const [tripToDelete, setTripToDelete] = useState<Trip | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newTripData, setNewTripData] = useState({
    start_address: '',
    end_address: '',
    max_distance_km: 500,
    duration_days: 7,
  });

  const handleDeleteTrip = async () => {
    if (!tripToDelete) return;

    setIsDeleting(true);
    try {
      await deleteTrip(tripToDelete.id);
      setTripToDelete(null);
    } catch (error) {
      console.error('Failed to delete trip:', error);
      alert('Failed to delete trip. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCreateTrip = async () => {
    if (!newTripData.start_address) {
      alert('Please enter a starting address');
      return;
    }

    setIsCreating(true);
    try {
      // Generate a name from the addresses
      const startCity = newTripData.start_address.split(',')[0].trim();
      const endCity = newTripData.end_address ? newTripData.end_address.split(',')[0].trim() : 'Adventure';
      const tripName = `${startCity} to ${endCity}`;

      await createTrip({
        name: tripName,
        start_address: newTripData.start_address,
        end_address: newTripData.end_address || undefined,
        max_distance_km: newTripData.max_distance_km,
        duration_days: newTripData.duration_days,
      });
      await refetchTrips();
      setShowCreateModal(false);
      setNewTripData({
        start_address: '',
        end_address: '',
        max_distance_km: 500,
        duration_days: 7,
      });
    } catch (error) {
      console.error('Failed to create trip:', error);
      alert('Failed to create trip. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleMarkVisited = (waypoint: JourneyWaypoint) => {
    markVisited(waypoint.id);
  };

  const handleMarkSkipped = (waypoint: JourneyWaypoint) => {
    markSkipped(waypoint.id);
  };

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen bg-zinc-950">
        <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
          <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link
                href="/"
                className="p-2 -ml-2 text-zinc-400 hover:text-zinc-200 transition-colors lg:hidden"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-lg font-semibold text-zinc-100">Journey</h1>
            </div>
          </div>
        </header>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
          <span className="ml-3 text-zinc-500">Loading your journey...</span>
        </div>
      </main>
    );
  }

  // No journey / error state
  if (error || !journey) {
    return (
      <main className="min-h-screen bg-zinc-950">
        <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
          <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link
                href="/"
                className="p-2 -ml-2 text-zinc-400 hover:text-zinc-200 transition-colors lg:hidden"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <h1 className="text-lg font-semibold text-zinc-100">Journey</h1>
            </div>
          </div>
        </header>
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="text-center py-16 lg:col-span-2">
              <MapPin className="w-16 h-16 text-zinc-700 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-zinc-300 mb-2">No Active Journey</h2>
              <p className="text-zinc-500 mb-6">
                {error || 'Start planning your adventure to see your journey here.'}
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors"
              >
                <Plus className="w-5 h-5" />
                Plan a Trip
              </button>
            </div>

            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-zinc-400">Your Trips</h3>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Trip
                </button>
              </div>
              {trips.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {trips.map((trip) => (
                    <div
                      key={trip.id}
                      className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg relative group"
                    >
                      <button
                        onClick={() => setTripToDelete(trip)}
                        className="absolute top-2 right-2 p-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-colors"
                        title="Delete trip"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                      <p className="text-zinc-200 font-medium pr-8">{trip.name || 'Unnamed Trip'}</p>
                      <p className="text-sm text-zinc-500">
                        {trip.start_address} → {trip.end_address || 'TBD'}
                      </p>
                      <span className="inline-block mt-2 text-xs px-2 py-1 bg-zinc-800 text-zinc-400 rounded">
                        {trip.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-zinc-500 text-center py-8">
                  No trips yet. Create your first trip to get started!
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Create trip modal */}
        {showCreateModal && (
          <div
            className="fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center p-4"
            onClick={() => !isCreating && setShowCreateModal(false)}
          >
            <div
              className="bg-zinc-900 rounded-xl w-full max-w-lg p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-zinc-100">Create New Trip</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  disabled={isCreating}
                  className="p-1 text-zinc-400 hover:text-zinc-200 transition-colors disabled:opacity-50"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">
                    Starting Address *
                  </label>
                  <input
                    type="text"
                    value={newTripData.start_address}
                    onChange={(e) => setNewTripData(prev => ({ ...prev, start_address: e.target.value }))}
                    placeholder="e.g., Brussels, Belgium"
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">
                    Destination (optional)
                  </label>
                  <input
                    type="text"
                    value={newTripData.end_address}
                    onChange={(e) => setNewTripData(prev => ({ ...prev, end_address: e.target.value }))}
                    placeholder="e.g., Paris, France"
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-zinc-400 mb-1">
                      Max Distance (km)
                    </label>
                    <input
                      type="number"
                      value={newTripData.max_distance_km}
                      onChange={(e) => setNewTripData(prev => ({ ...prev, max_distance_km: parseInt(e.target.value) || 500 }))}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-zinc-400 mb-1">
                      Duration (days)
                    </label>
                    <input
                      type="number"
                      value={newTripData.duration_days}
                      onChange={(e) => setNewTripData(prev => ({ ...prev, duration_days: parseInt(e.target.value) || 7 }))}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  disabled={isCreating}
                  className="flex-1 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTrip}
                  disabled={isCreating || !newTripData.start_address}
                  className="flex-1 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" />
                      Create Trip
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    );
  }

  const currentPos = currentPosition
    ? { lat: currentPosition.latitude, lng: currentPosition.longitude }
    : { lat: journey.start.coordinates.lat, lng: journey.start.coordinates.lng };

  return (
    <main className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 -ml-2 text-zinc-400 hover:text-zinc-200 transition-colors lg:hidden"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-semibold text-zinc-100">{journey.name}</h1>
              <p className="text-xs text-zinc-500">Day {journey.current_day}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-zinc-400 hover:text-zinc-200 transition-colors">
              <Settings className="w-5 h-5" />
            </button>
            {activeTrip && (
              <button
                onClick={() => setTripToDelete(activeTrip)}
                className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-colors"
                title="Delete trip"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content - responsive layout */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Map section - larger on desktop */}
          <div className="lg:col-span-7 xl:col-span-8">
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
              <div className="h-[280px] lg:h-[500px] xl:h-[600px]">
                <JourneyMap
                  journey={journey}
                  currentPosition={currentPos}
                  onWaypointClick={setSelectedWaypoint}
                  height="100%"
                />
              </div>
            </div>
          </div>

          {/* Content section */}
          <div className="lg:col-span-5 xl:col-span-4 space-y-4">
            {/* Progress section */}
            {stats && (
              <CollapsibleSection title="Progress" defaultOpen={true}>
                <JourneyProgress journey={journey} stats={stats} />
              </CollapsibleSection>
            )}

            {/* Waypoints section */}
            <CollapsibleSection title="Must-See Places" defaultOpen={true}>
              {journey.waypoints.length > 0 ? (
                <div className="max-h-[400px] overflow-y-auto">
                  <WaypointList
                    waypoints={journey.waypoints}
                    currentDistanceKm={journey.progress_km}
                    onWaypointSelect={setSelectedWaypoint}
                    onMarkVisited={handleMarkVisited}
                    onMarkSkipped={handleMarkSkipped}
                  />
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-zinc-500">No waypoints added yet.</p>
                  <p className="text-sm text-zinc-600 mt-1">
                    Add places to your journey from the Discover page.
                  </p>
                </div>
              )}
            </CollapsibleSection>
          </div>
        </div>
      </div>

      {/* Add waypoint FAB */}
      <div className="fixed bottom-24 lg:bottom-6 right-6">
        <Link
          href="/discover"
          className="w-14 h-14 bg-emerald-500 hover:bg-emerald-400 text-white rounded-full shadow-lg flex items-center justify-center transition-colors"
        >
          <Plus className="w-6 h-6" />
        </Link>
      </div>

      {/* Waypoint detail modal */}
      {selectedWaypoint && (
        <div
          className="fixed inset-0 bg-black/60 z-[9999] flex items-end lg:items-center justify-center"
          onClick={() => setSelectedWaypoint(null)}
        >
          <div
            className="bg-zinc-900 rounded-t-2xl lg:rounded-2xl w-full max-w-lg p-6 animate-slide-up lg:animate-none"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-12 h-1 bg-zinc-700 rounded-full mx-auto mb-4 lg:hidden" />
            <h2 className="text-xl font-semibold text-zinc-100 mb-2">
              {selectedWaypoint.name}
            </h2>
            {selectedWaypoint.description && (
              <p className="text-zinc-400 mb-4">{selectedWaypoint.description}</p>
            )}

            <div className="flex flex-wrap gap-2 mb-4">
              {selectedWaypoint.tags?.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-zinc-800 text-zinc-400 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-4 text-sm text-zinc-500 mb-6">
              <span>{selectedWaypoint.distance_from_start_km} km from start</span>
              {selectedWaypoint.rating && (
                <span className="text-amber-400">
                  ★ {selectedWaypoint.rating.toFixed(1)}
                </span>
              )}
            </div>

            {selectedWaypoint.type === 'mustSee' && (
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    handleMarkVisited(selectedWaypoint);
                    setSelectedWaypoint(null);
                  }}
                  className="flex-1 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors"
                >
                  Mark as Visited
                </button>
                <button
                  onClick={() => {
                    handleMarkSkipped(selectedWaypoint);
                    setSelectedWaypoint(null);
                  }}
                  className="px-4 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  Skip
                </button>
              </div>
            )}

            {selectedWaypoint.type === 'visited' && (
              <div className="flex items-center justify-between">
                <span className="text-emerald-400 text-sm">
                  Visited on {selectedWaypoint.visited_date}
                </span>
                <button
                  onClick={() => setSelectedWaypoint(null)}
                  className="px-4 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            )}

            {selectedWaypoint.type === 'skipped' && (
              <div className="flex items-center justify-between">
                <span className="text-zinc-500 text-sm">This place was skipped</span>
                <button
                  onClick={() => setSelectedWaypoint(null)}
                  className="px-4 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            )}

            {(selectedWaypoint.type === 'start' || selectedWaypoint.type === 'destination') && (
              <button
                onClick={() => setSelectedWaypoint(null)}
                className="w-full py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors"
              >
                Close
              </button>
            )}
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {tripToDelete && (
        <div
          className="fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center p-4"
          onClick={() => !isDeleting && setTripToDelete(null)}
        >
          <div
            className="bg-zinc-900 rounded-xl w-full max-w-md p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-zinc-100">Delete Trip</h2>
              <button
                onClick={() => setTripToDelete(null)}
                disabled={isDeleting}
                className="p-1 text-zinc-400 hover:text-zinc-200 transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-zinc-400 mb-6">
              Are you sure you want to delete{' '}
              <span className="text-zinc-200 font-medium">
                {tripToDelete.name || 'this trip'}
              </span>
              ? This action cannot be undone.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setTripToDelete(null)}
                disabled={isDeleting}
                className="flex-1 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteTrip}
                disabled={isDeleting}
                className="flex-1 py-3 bg-red-500 hover:bg-red-400 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create trip modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 bg-black/60 z-[9999] flex items-center justify-center p-4"
          onClick={() => !isCreating && setShowCreateModal(false)}
        >
          <div
            className="bg-zinc-900 rounded-xl w-full max-w-lg p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-zinc-100">Create New Trip</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                disabled={isCreating}
                className="p-1 text-zinc-400 hover:text-zinc-200 transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1">
                  Starting Address *
                </label>
                <input
                  type="text"
                  value={newTripData.start_address}
                  onChange={(e) => setNewTripData(prev => ({ ...prev, start_address: e.target.value }))}
                  placeholder="e.g., Brussels, Belgium"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-1">
                  Destination (optional)
                </label>
                <input
                  type="text"
                  value={newTripData.end_address}
                  onChange={(e) => setNewTripData(prev => ({ ...prev, end_address: e.target.value }))}
                  placeholder="e.g., Paris, France"
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">
                    Max Distance (km)
                  </label>
                  <input
                    type="number"
                    value={newTripData.max_distance_km}
                    onChange={(e) => setNewTripData(prev => ({ ...prev, max_distance_km: parseInt(e.target.value) || 500 }))}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">
                    Duration (days)
                  </label>
                  <input
                    type="number"
                    value={newTripData.duration_days}
                    onChange={(e) => setNewTripData(prev => ({ ...prev, duration_days: parseInt(e.target.value) || 7 }))}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                disabled={isCreating}
                className="flex-1 py-3 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTrip}
                disabled={isCreating || !newTripData.start_address}
                className="flex-1 py-3 bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isCreating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    Create Trip
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
