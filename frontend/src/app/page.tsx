'use client';

import { useState, useMemo } from 'react';
import { Loader2 } from 'lucide-react';
import { CollapsibleSection } from '@/components/CollapsibleSection';
import { CurrentPosition } from '@/components/CurrentPosition';
import { DrivingEnvelope } from '@/components/DrivingEnvelope';
import { DayPlanCard } from '@/components/DayPlanCard';
import { CustomizePane } from '@/components/CustomizePane';
import { useTripState } from '@/hooks/useTripState';
import type { DayPlanType, Location } from '@/types/trip';

export default function TodayPage() {
  const {
    currentPosition,
    currentAddress,
    isLoadingPosition,
    positionError,
    destination,
    distanceToDestination,
    weather,
    drivingEnvelopeKm,
    maxDrivingKm,
    suggestedPlans,
    isLoadingNearby,
    nearbyEvents,
    nearbyLocations,
    setDrivingEnvelope,
    selectPlan,
    selectedPlanId,
    removeItemFromPlan,
  } = useTripState();

  const [detailPlanId, setDetailPlanId] = useState<string | null>(null);

  // Filter plans based on driving envelope
  const filteredPlans = useMemo(() => {
    return suggestedPlans.filter((plan) => {
      if (drivingEnvelopeKm <= 20) {
        return plan.type === 'zero';
      }
      if (drivingEnvelopeKm <= 100) {
        return plan.type === 'exploration' || plan.type === 'zero' || plan.type === 'transit';
      }
      return true;
    });
  }, [suggestedPlans, drivingEnvelopeKm]);

  const detailPlan = suggestedPlans.find((p) => p.id === detailPlanId);

  // Generate alternative options from nearby data
  const alternativeEvents = useMemo((): Location[] => {
    return nearbyEvents.slice(0, 5).map((event) => ({
      id: `alt-event-${event.id}`,
      name: event.name,
      coordinates: { lat: event.latitude, lng: event.longitude },
      type: 'event' as const,
      distance_km: event.distance_km,
      time: event.start_datetime
        ? new Date(event.start_datetime).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })
        : undefined,
    }));
  }, [nearbyEvents]);

  const alternativeOvernights = useMemo((): Location[] => {
    return nearbyLocations
      .filter((l) => l.location_type === 'CAMPSITE' || l.location_type === 'PARKING')
      .slice(0, 5)
      .map((loc) => ({
        id: `alt-overnight-${loc.id}`,
        name: loc.name,
        coordinates: { lat: loc.latitude, lng: loc.longitude },
        type: 'overnight' as const,
        distance_km: loc.distance_km,
        price: loc.price_type === 'free'
          ? 'Free'
          : loc.price_min
          ? `€${loc.price_min}`
          : undefined,
        amenities: loc.tags?.slice(0, 3),
      }));
  }, [nearbyLocations]);

  const alternativeStops = useMemo((): Location[] => {
    return nearbyLocations
      .filter((l) => l.location_type === 'POI' || l.location_type === 'ATTRACTION')
      .slice(0, 5)
      .map((loc) => ({
        id: `alt-stop-${loc.id}`,
        name: loc.name,
        coordinates: { lat: loc.latitude, lng: loc.longitude },
        type: 'poi' as const,
        distance_km: loc.distance_km,
        rating: loc.rating || undefined,
      }));
  }, [nearbyLocations]);

  const handleUpdatePlan = (updatedPlan: DayPlanType) => {
    // TODO: In a real app, this would update the backend
    console.log('Plan updated:', updatedPlan);
  };

  // Convert position to the format expected by CurrentPosition
  const coordinates = currentPosition
    ? { lat: currentPosition.latitude, lng: currentPosition.longitude }
    : null;

  const destinationForDisplay = destination
    ? {
        name: destination.name,
        coordinates: { lat: destination.coordinates.latitude, lng: destination.coordinates.longitude },
      }
    : null;

  const weatherForDisplay = weather
    ? { temp_c: weather.temperature, condition: weather.condition, icon: weather.icon }
    : null;

  return (
    <main className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-zinc-100">Today</h1>
          <span className="text-sm text-zinc-500">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
            })}
          </span>
        </div>
      </header>

      {/* Position error banner */}
      {positionError && (
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-2">
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2 text-sm text-amber-400">
            {positionError}
          </div>
        </div>
      )}

      {/* Main content - responsive grid */}
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left column - Position & Driving */}
          <div className="lg:col-span-4 space-y-4">
            {/* Section A: Current Position */}
            <CollapsibleSection title="Current Position" defaultOpen={true}>
              {isLoadingPosition ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
                  <span className="ml-2 text-sm text-zinc-500">Getting your location...</span>
                </div>
              ) : (
                <CurrentPosition
                  coordinates={coordinates}
                  address={currentAddress}
                  destination={destinationForDisplay}
                  weather={weatherForDisplay}
                />
              )}
            </CollapsibleSection>

            {/* Section B: Driving Envelope */}
            <CollapsibleSection title="Today's Driving" defaultOpen={true}>
              <DrivingEnvelope
                value={drivingEnvelopeKm}
                max={maxDrivingKm}
                onChange={setDrivingEnvelope}
              />
            </CollapsibleSection>
          </div>

          {/* Middle column - Day Plans */}
          <div className="lg:col-span-4">
            <CollapsibleSection title="Suggested Plans" defaultOpen={true}>
              {isLoadingNearby ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
                  <span className="ml-2 text-sm text-zinc-500">Finding places nearby...</span>
                </div>
              ) : filteredPlans.length > 0 ? (
                <div className="space-y-3">
                  {filteredPlans.map((plan) => (
                    <DayPlanCard
                      key={plan.id}
                      plan={plan}
                      isSelected={selectedPlanId === plan.id}
                      onSelect={() => selectPlan(plan.id)}
                      onViewDetails={() => setDetailPlanId(plan.id)}
                      onRemoveItem={(itemType, itemId) => removeItemFromPlan(plan.id, itemType, itemId)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-zinc-500">No plans available for this driving range.</p>
                  <p className="text-sm text-zinc-600 mt-1">Try adjusting the slider above.</p>
                </div>
              )}
            </CollapsibleSection>
          </div>

          {/* Right column - Customize (shown when a plan is being viewed) */}
          <div className="lg:col-span-4">
            {detailPlan ? (
              <CollapsibleSection title="Customise" defaultOpen={true}>
                <CustomizePane
                  plan={detailPlan}
                  alternativeEvents={alternativeEvents}
                  alternativeStops={alternativeStops}
                  alternativeOvernights={alternativeOvernights}
                  onUpdatePlan={handleUpdatePlan}
                />
              </CollapsibleSection>
            ) : (
              <div className="hidden lg:block">
                <CollapsibleSection title="Customise" defaultOpen={true}>
                  <div className="text-center py-12">
                    <p className="text-zinc-500">Select a plan to customise</p>
                    <p className="text-sm text-zinc-600 mt-1">
                      Click &quot;View Details&quot; on any plan
                    </p>
                  </div>
                </CollapsibleSection>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
