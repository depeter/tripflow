'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  User,
  MapPin,
  Mountain,
  Building2,
  TreePine,
  Waves,
  Camera,
  Music,
  Utensils,
  Bike,
  Castle,
  Wine,
  Tent,
  Caravan,
  Car,
  Home,
  ChevronRight,
  Check,
  Settings,
  Bell,
  Shield,
  HelpCircle,
  LogOut,
  Loader2,
  Globe,
} from 'lucide-react';
import Link from 'next/link';
import { CollapsibleSection } from '@/components/CollapsibleSection';
import type { UserProfile } from '@/types/profile';
import {
  getCurrentUser,
  isAuthenticated,
  getProfilePreferences,
  updateProfilePreferences,
  logout,
  type User as AuthUser,
  type ProfilePreferences
} from '@/services/authService';
import { getAvailableLanguages, type LanguageInfo } from '@/services/languageService';

const INTEREST_OPTIONS: { id: string; name: string; icon: typeof Camera }[] = [
  { id: 'nature', name: 'Nature & Hiking', icon: Mountain },
  { id: 'history', name: 'History & Culture', icon: Castle },
  { id: 'food', name: 'Local Food', icon: Utensils },
  { id: 'photography', name: 'Photography', icon: Camera },
  { id: 'music', name: 'Music & Festivals', icon: Music },
  { id: 'cycling', name: 'Cycling', icon: Bike },
  { id: 'wine', name: 'Wine & Beer', icon: Wine },
  { id: 'architecture', name: 'Architecture', icon: Building2 },
];

const ENVIRONMENT_OPTIONS = [
  { id: 'nature', name: 'Nature', icon: TreePine },
  { id: 'cities', name: 'Cities', icon: Building2 },
  { id: 'villages', name: 'Villages', icon: Home },
  { id: 'coast', name: 'Coastal', icon: Waves },
];

const ACCOMMODATION_OPTIONS = [
  { id: 'camping', name: 'Campgrounds', icon: Tent },
  { id: 'wild', name: 'Wild Camping', icon: Mountain },
  { id: 'stellplatz', name: 'Stellplatz', icon: Caravan },
  { id: 'hotel', name: 'Hotels', icon: Building2 },
];

// Default empty profile (preferences stored locally until backend supports them)
const getDefaultProfile = (user: AuthUser | null): UserProfile => ({
  name: user?.full_name || user?.email?.split('@')[0] || 'Guest',
  language: 'en', // Default to English
  interests: INTEREST_OPTIONS.map(opt => ({
    id: opt.id,
    name: opt.name,
    icon: opt.icon.name || opt.id,
    selected: false,
  })),
  travelStyle: {
    pace: 'moderate',
    environment: [],
    budget: 'mid-range',
    accommodation: [],
  },
  vehicle: {
    type: 'campervan',
    length_m: 6.0,
    height_m: 2.5,
  },
  homeBase: undefined,
});

// Convert API preferences to UserProfile format
const mergePreferencesIntoProfile = (
  defaultProfile: UserProfile,
  prefs: ProfilePreferences
): UserProfile => {
  // Merge interests: keep all default options, update selected state from API
  const mergedInterests = defaultProfile.interests.map(defaultInterest => {
    const apiInterest = prefs.interests?.find(i => i.id === defaultInterest.id);
    return apiInterest ? apiInterest : defaultInterest;
  });

  return {
    ...defaultProfile,
    language: prefs.language || defaultProfile.language,
    interests: mergedInterests,
    travelStyle: prefs.travelStyle || defaultProfile.travelStyle,
    vehicle: prefs.vehicle || defaultProfile.vehicle,
    homeBase: prefs.homeBase || defaultProfile.homeBase,
  };
};

function ToggleChip({
  selected,
  onClick,
  icon: Icon,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  icon: typeof Camera;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all ${
        selected
          ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
          : 'bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600'
      }`}
    >
      <Icon className="w-4 h-4" />
      <span className="text-sm">{children}</span>
      {selected && <Check className="w-4 h-4 ml-auto" />}
    </button>
  );
}

function PaceSelector({
  value,
  onChange,
}: {
  value: 'slow' | 'moderate' | 'fast';
  onChange: (pace: 'slow' | 'moderate' | 'fast') => void;
}) {
  const options = [
    { id: 'slow', label: 'Slow', description: '50-100 km/day' },
    { id: 'moderate', label: 'Moderate', description: '100-200 km/day' },
    { id: 'fast', label: 'Fast', description: '200+ km/day' },
  ] as const;

  return (
    <div className="space-y-2">
      <label className="text-sm text-zinc-400">Travel Pace</label>
      <div className="grid grid-cols-3 gap-2">
        {options.map((option) => (
          <button
            key={option.id}
            onClick={() => onChange(option.id)}
            className={`p-3 rounded-lg border text-center transition-all ${
              value === option.id
                ? 'bg-emerald-500/20 border-emerald-500/50'
                : 'bg-zinc-800/50 border-zinc-700 hover:border-zinc-600'
            }`}
          >
            <p
              className={`text-sm font-medium ${
                value === option.id ? 'text-emerald-400' : 'text-zinc-300'
              }`}
            >
              {option.label}
            </p>
            <p className="text-xs text-zinc-500 mt-1">{option.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

function SettingsMenuItem({
  icon: Icon,
  label,
  description,
}: {
  icon: typeof Settings;
  label: string;
  description?: string;
}) {
  return (
    <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-zinc-800/50 transition-colors text-left">
      <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
        <Icon className="w-5 h-5 text-zinc-400" />
      </div>
      <div className="flex-1">
        <p className="text-zinc-200 font-medium">{label}</p>
        {description && <p className="text-xs text-zinc-500">{description}</p>}
      </div>
      <ChevronRight className="w-5 h-5 text-zinc-600" />
    </button>
  );
}

export default function ProfilePage() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isEditingVehicle, setIsEditingVehicle] = useState(false);
  const [availableLanguages, setAvailableLanguages] = useState<LanguageInfo[]>([]);
  const [isLoadingLanguages, setIsLoadingLanguages] = useState(true);

  // Fetch user data on mount
  useEffect(() => {
    async function loadProfile() {
      setIsLoading(true);
      setError(null);

      try {
        // Check if authenticated
        if (!isAuthenticated()) {
          setIsLoggedIn(false);
          setProfile(getDefaultProfile(null));
          setIsLoading(false);
          return;
        }

        setIsLoggedIn(true);

        // Fetch user from API
        const currentUser = await getCurrentUser();
        setUser(currentUser);

        // Create default profile
        const defaultProfile = getDefaultProfile(currentUser);

        // Fetch preferences from API
        try {
          const prefs = await getProfilePreferences();
          console.log('Loaded preferences from API:', prefs);
          if (prefs && Object.keys(prefs).length > 0) {
            const mergedProfile = mergePreferencesIntoProfile(defaultProfile, prefs);
            console.log('Merged profile:', mergedProfile);
            setProfile(mergedProfile);
          } else {
            console.log('No preferences found, using defaults');
            setProfile(defaultProfile);
          }
        } catch (err) {
          // No preferences saved yet, use defaults
          console.log('Failed to load preferences, using defaults:', err);
          setProfile(defaultProfile);
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
        setError('Failed to load profile. Please try again.');
        setProfile(getDefaultProfile(null));
      } finally {
        setIsLoading(false);
      }
    }

    loadProfile();
  }, []);

  // Fetch available languages on mount
  useEffect(() => {
    async function loadLanguages() {
      setIsLoadingLanguages(true);
      try {
        const response = await getAvailableLanguages();
        setAvailableLanguages(response.languages);
      } catch (err) {
        console.error('Failed to load languages:', err);
        // Fallback to English only
        setAvailableLanguages([
          { code: 'en', name: 'English', nativeName: 'English', translationCount: 0 }
        ]);
      } finally {
        setIsLoadingLanguages(false);
      }
    }

    loadLanguages();
  }, []);

  // Save preferences to API (immediate)
  const saveToAPI = async (newProfile: UserProfile) => {
    if (!isLoggedIn) {
      console.log('Not logged in, skipping save');
      return;
    }

    console.log('Saving preferences to API:', {
      language: newProfile.language,
      interests: newProfile.interests,
      travelStyle: newProfile.travelStyle,
      vehicle: newProfile.vehicle,
      homeBase: newProfile.homeBase,
    });

    setIsSaving(true);
    try {
      const result = await updateProfilePreferences({
        language: newProfile.language,
        interests: newProfile.interests,
        travelStyle: newProfile.travelStyle,
        vehicle: newProfile.vehicle,
        homeBase: newProfile.homeBase,
      });
      console.log('Successfully saved preferences:', result);
    } catch (err) {
      console.error('Failed to save preferences:', err);
      setError('Failed to save preferences. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Update profile and trigger immediate save
  const updateProfileAndSave = (updater: (prev: UserProfile) => UserProfile) => {
    setProfile((prev) => {
      if (!prev) return prev;
      const newProfile = updater(prev);

      // Immediately save for logged-in users
      if (isLoggedIn) {
        saveToAPI(newProfile);
      }

      return newProfile;
    });
  };

  const toggleInterest = (id: string) => {
    if (!profile) return;
    updateProfileAndSave((prev) => ({
      ...prev,
      interests: prev.interests.map((i) =>
        i.id === id ? { ...i, selected: !i.selected } : i
      ),
    }));
  };

  const toggleEnvironment = (id: string) => {
    if (!profile) return;
    updateProfileAndSave((prev) => ({
      ...prev,
      travelStyle: {
        ...prev.travelStyle,
        environment: prev.travelStyle.environment.includes(id as 'nature' | 'cities' | 'villages' | 'coast')
          ? prev.travelStyle.environment.filter((e) => e !== id)
          : [...prev.travelStyle.environment, id as 'nature' | 'cities' | 'villages' | 'coast'],
      },
    }));
  };

  const toggleAccommodation = (id: string) => {
    if (!profile) return;
    updateProfileAndSave((prev) => ({
      ...prev,
      travelStyle: {
        ...prev.travelStyle,
        accommodation: prev.travelStyle.accommodation.includes(id as 'camping' | 'wild' | 'stellplatz' | 'hotel')
          ? prev.travelStyle.accommodation.filter((a) => a !== id)
          : [...prev.travelStyle.accommodation, id as 'camping' | 'wild' | 'stellplatz' | 'hotel'],
      },
    }));
  };

  const updatePace = (pace: 'slow' | 'moderate' | 'fast') => {
    if (!profile) return;
    updateProfileAndSave((prev) => ({
      ...prev,
      travelStyle: { ...prev.travelStyle, pace },
    }));
  };

  const updateVehicle = (updates: Partial<UserProfile['vehicle']>) => {
    if (!profile) return;
    updateProfileAndSave((prev) => ({
      ...prev,
      vehicle: { ...prev.vehicle, ...updates },
    }));
  };

  const updateLanguage = (languageCode: string) => {
    if (!profile) return;
    updateProfileAndSave((prev) => ({
      ...prev,
      language: languageCode,
    }));
  };

  // Loading state
  if (isLoading) {
    return (
      <main className="min-h-screen bg-zinc-950">
        <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
          <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3">
            <h1 className="text-lg font-semibold text-zinc-100">Profile</h1>
          </div>
        </header>
        <div className="flex items-center justify-center py-24">
          <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
          <span className="ml-3 text-zinc-500">Loading profile...</span>
        </div>
      </main>
    );
  }

  // Error or no profile state
  if (!profile) {
    return (
      <main className="min-h-screen bg-zinc-950">
        <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
          <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3">
            <h1 className="text-lg font-semibold text-zinc-100">Profile</h1>
          </div>
        </header>
        <div className="flex flex-col items-center justify-center py-24">
          <p className="text-zinc-400 mb-4">{error || 'Unable to load profile'}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-zinc-950/90 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-zinc-100">Profile</h1>
          {isSaving && (
            <span className="flex items-center gap-2 text-sm text-zinc-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </span>
          )}
          {!isLoggedIn && (
            <Link
              href="/login"
              className="text-sm text-emerald-400 hover:text-emerald-300"
            >
              Sign in to save preferences
            </Link>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left column - Profile info */}
          <div className="lg:col-span-4 space-y-4">
            {/* Profile header */}
            <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <User className="w-10 h-10 text-emerald-400" />
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-zinc-100">
                    {profile.name}
                  </h2>
                  <div className="flex items-center gap-1 text-sm text-zinc-500 mt-1">
                    <MapPin className="w-4 h-4" />
                    <span>{profile.homeBase?.name || 'Set your home location'}</span>
                  </div>
                  <button className="mt-2 text-sm text-emerald-400 hover:text-emerald-300">
                    Edit Profile
                  </button>
                </div>
              </div>
            </div>

            {/* Vehicle */}
            <CollapsibleSection title="Vehicle" defaultOpen={true}>
              <div className="space-y-4">
                {!isEditingVehicle ? (
                  <>
                    <div className="flex items-center gap-3 p-4 bg-zinc-800/50 rounded-lg">
                      {profile.vehicle.type === 'campervan' || profile.vehicle.type === 'car-tent' ? (
                        <Car className="w-8 h-8 text-emerald-400" />
                      ) : (
                        <Caravan className="w-8 h-8 text-emerald-400" />
                      )}
                      <div>
                        <p className="font-medium text-zinc-100 capitalize">
                          {profile.vehicle.type.replace('-', ' ')}
                        </p>
                        <p className="text-sm text-zinc-500">
                          {profile.vehicle.length_m}m × {profile.vehicle.height_m}m
                        </p>
                      </div>
                      <button
                        onClick={() => setIsEditingVehicle(true)}
                        className="ml-auto px-3 py-1 text-sm text-zinc-400 hover:text-zinc-200 bg-zinc-700 rounded-lg"
                      >
                        Edit
                      </button>
                    </div>
                    <p className="text-xs text-zinc-500">
                      Vehicle dimensions help filter parking spots that fit your camper.
                    </p>
                  </>
                ) : (
                  <div className="space-y-4 p-4 bg-zinc-800/50 rounded-lg">
                    <div>
                      <label className="block text-sm text-zinc-400 mb-2">Vehicle Type</label>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { id: 'campervan', label: 'Campervan', icon: Car },
                          { id: 'motorhome', label: 'Motorhome', icon: Caravan },
                          { id: 'caravan', label: 'Caravan', icon: Caravan },
                          { id: 'car-tent', label: 'Car + Tent', icon: Car },
                        ].map(({ id, label, icon: Icon }) => (
                          <button
                            key={id}
                            onClick={() => updateVehicle({ type: id as 'campervan' | 'motorhome' | 'caravan' | 'car-tent' })}
                            className={`flex items-center gap-2 p-3 rounded-lg border transition-all ${
                              profile.vehicle.type === id
                                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                                : 'bg-zinc-900 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                            }`}
                          >
                            <Icon className="w-5 h-5" />
                            <span className="text-sm">{label}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-zinc-400 mb-2">Length (m)</label>
                        <input
                          type="number"
                          step="0.1"
                          min="2"
                          max="15"
                          value={profile.vehicle.length_m || ''}
                          onChange={(e) => updateVehicle({ length_m: parseFloat(e.target.value) || undefined })}
                          className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-emerald-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-zinc-400 mb-2">Height (m)</label>
                        <input
                          type="number"
                          step="0.1"
                          min="1"
                          max="5"
                          value={profile.vehicle.height_m || ''}
                          onChange={(e) => updateVehicle({ height_m: parseFloat(e.target.value) || undefined })}
                          className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-emerald-500"
                        />
                      </div>
                    </div>

                    <button
                      onClick={() => setIsEditingVehicle(false)}
                      className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg transition-colors"
                    >
                      Done
                    </button>
                  </div>
                )}
              </div>
            </CollapsibleSection>

            {/* Settings menu - desktop only */}
            <div className="hidden lg:block">
              <CollapsibleSection title="Settings" defaultOpen={true}>
                <div className="space-y-1">
                  {/* Language Selector */}
                  <div className="p-3">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
                        <Globe className="w-5 h-5 text-zinc-400" />
                      </div>
                      <div className="flex-1">
                        <p className="text-zinc-200 font-medium">Language</p>
                        <p className="text-xs text-zinc-500">Content language preference</p>
                      </div>
                    </div>
                    {isLoadingLanguages ? (
                      <div className="flex items-center gap-2 text-zinc-500 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading languages...
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-2">
                        {availableLanguages.map((lang) => (
                          <button
                            key={lang.code}
                            onClick={() => updateLanguage(lang.code)}
                            className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-all text-left ${
                              profile.language === lang.code
                                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                                : 'bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                            }`}
                          >
                            <span className="text-sm">{lang.nativeName}</span>
                            {profile.language === lang.code && <Check className="w-4 h-4" />}
                          </button>
                        ))}
                      </div>
                    )}
                    {availableLanguages.length > 0 && !isLoadingLanguages && (
                      <p className="text-xs text-zinc-600 mt-2">
                        {availableLanguages.reduce((sum, l) => sum + l.translationCount, 0).toLocaleString()} translations available
                      </p>
                    )}
                  </div>
                  <div className="border-t border-zinc-800 my-2" />
                  <SettingsMenuItem
                    icon={Bell}
                    label="Notifications"
                    description="Push notifications, email"
                  />
                  <SettingsMenuItem
                    icon={Shield}
                    label="Privacy & Security"
                    description="Data, permissions"
                  />
                  <SettingsMenuItem
                    icon={HelpCircle}
                    label="Help & Support"
                    description="FAQ, contact us"
                  />
                  {isLoggedIn ? (
                    <div className="pt-2 mt-2 border-t border-zinc-800">
                      <button
                        onClick={() => {
                          logout();
                          window.location.reload();
                        }}
                        className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-red-500/10 transition-colors text-left text-red-400"
                      >
                        <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
                          <LogOut className="w-5 h-5" />
                        </div>
                        <span className="font-medium">Sign Out</span>
                      </button>
                    </div>
                  ) : (
                    <div className="pt-2 mt-2 border-t border-zinc-800">
                      <Link
                        href="/login"
                        className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-emerald-500/10 transition-colors text-left text-emerald-400"
                      >
                        <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                          <User className="w-5 h-5" />
                        </div>
                        <span className="font-medium">Sign In</span>
                      </Link>
                    </div>
                  )}
                </div>
              </CollapsibleSection>
            </div>
          </div>

          {/* Middle column - Interests */}
          <div className="lg:col-span-4">
            <CollapsibleSection title="Interests" defaultOpen={true}>
              <p className="text-sm text-zinc-500 mb-3">
                Select what you&apos;re interested in. This helps us suggest relevant places
                and events.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-2">
                {INTEREST_OPTIONS.map((interest) => (
                  <ToggleChip
                    key={interest.id}
                    selected={profile.interests.some(
                      (i) => i.id === interest.id && i.selected
                    )}
                    onClick={() => toggleInterest(interest.id)}
                    icon={interest.icon}
                  >
                    {interest.name}
                  </ToggleChip>
                ))}
              </div>
            </CollapsibleSection>
          </div>

          {/* Right column - Travel Style */}
          <div className="lg:col-span-4">
            <CollapsibleSection title="Travel Style" defaultOpen={true}>
              <div className="space-y-6">
                <PaceSelector
                  value={profile.travelStyle.pace}
                  onChange={updatePace}
                />

                <div className="space-y-2">
                  <label className="text-sm text-zinc-400">
                    Preferred Environment
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {ENVIRONMENT_OPTIONS.map((env) => (
                      <ToggleChip
                        key={env.id}
                        selected={profile.travelStyle.environment.includes(
                          env.id as any
                        )}
                        onClick={() => toggleEnvironment(env.id)}
                        icon={env.icon}
                      >
                        {env.name}
                      </ToggleChip>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-zinc-400">Accommodation</label>
                  <div className="grid grid-cols-2 gap-2">
                    {ACCOMMODATION_OPTIONS.map((acc) => (
                      <ToggleChip
                        key={acc.id}
                        selected={profile.travelStyle.accommodation.includes(
                          acc.id as any
                        )}
                        onClick={() => toggleAccommodation(acc.id)}
                        icon={acc.icon}
                      >
                        {acc.name}
                      </ToggleChip>
                    ))}
                  </div>
                </div>
              </div>
            </CollapsibleSection>
          </div>
        </div>

        {/* Settings menu - mobile only */}
        <div className="lg:hidden mt-6">
          <CollapsibleSection title="Settings" defaultOpen={false}>
            <div className="space-y-1">
              {/* Language Selector - Mobile */}
              <div className="p-3">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
                    <Globe className="w-5 h-5 text-zinc-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-zinc-200 font-medium">Language</p>
                    <p className="text-xs text-zinc-500">Content language preference</p>
                  </div>
                </div>
                {isLoadingLanguages ? (
                  <div className="flex items-center gap-2 text-zinc-500 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading languages...
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-2">
                    {availableLanguages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => updateLanguage(lang.code)}
                        className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-all text-left ${
                          profile.language === lang.code
                            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                            : 'bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600'
                        }`}
                      >
                        <span className="text-sm">{lang.nativeName}</span>
                        {profile.language === lang.code && <Check className="w-4 h-4" />}
                      </button>
                    ))}
                  </div>
                )}
                {availableLanguages.length > 0 && !isLoadingLanguages && (
                  <p className="text-xs text-zinc-600 mt-2">
                    {availableLanguages.reduce((sum, l) => sum + l.translationCount, 0).toLocaleString()} translations available
                  </p>
                )}
              </div>
              <div className="border-t border-zinc-800 my-2" />
              <SettingsMenuItem
                icon={Bell}
                label="Notifications"
                description="Push notifications, email"
              />
              <SettingsMenuItem
                icon={Shield}
                label="Privacy & Security"
                description="Data, permissions"
              />
              <SettingsMenuItem
                icon={HelpCircle}
                label="Help & Support"
                description="FAQ, contact us"
              />
              {isLoggedIn ? (
                <div className="pt-2 mt-2 border-t border-zinc-800">
                  <button
                    onClick={() => {
                      logout();
                      window.location.reload();
                    }}
                    className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-red-500/10 transition-colors text-left text-red-400"
                  >
                    <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
                      <LogOut className="w-5 h-5" />
                    </div>
                    <span className="font-medium">Sign Out</span>
                  </button>
                </div>
              ) : (
                <div className="pt-2 mt-2 border-t border-zinc-800">
                  <Link
                    href="/login"
                    className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-emerald-500/10 transition-colors text-left text-emerald-400"
                  >
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5" />
                    </div>
                    <span className="font-medium">Sign In</span>
                  </Link>
                </div>
              )}
            </div>
          </CollapsibleSection>
        </div>
      </div>
    </main>
  );
}
