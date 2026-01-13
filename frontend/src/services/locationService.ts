// Geolocation service for getting user's current position

export interface Position {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

// Get current position using browser geolocation
export function getCurrentPosition(): Promise<Position> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by your browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
      },
      (error) => {
        reject(error);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes
      }
    );
  });
}

// Watch position changes
export function watchPosition(
  onUpdate: (position: Position) => void,
  onError?: (error: GeolocationPositionError) => void
): number | null {
  if (!navigator.geolocation) {
    return null;
  }

  return navigator.geolocation.watchPosition(
    (position) => {
      onUpdate({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
      });
    },
    onError,
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000, // 1 minute
    }
  );
}

// Stop watching position
export function clearWatch(watchId: number): void {
  navigator.geolocation.clearWatch(watchId);
}

// Calculate distance between two points (Haversine formula)
export function calculateDistance(
  from: Position,
  to: Position
): number {
  const R = 6371; // Earth's radius in km
  const dLat = toRad(to.latitude - from.latitude);
  const dLon = toRad(to.longitude - from.longitude);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(from.latitude)) *
      Math.cos(toRad(to.latitude)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

function toRad(deg: number): number {
  return deg * (Math.PI / 180);
}

// Get weather data from Open-Meteo (free, no API key needed)
export interface WeatherData {
  temperature: number;
  condition: string;
  icon: string;
  humidity?: number;
  wind_speed?: number;
}

export async function getWeather(latitude: number, longitude: number): Promise<WeatherData> {
  try {
    const response = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=auto`
    );
    const data = await response.json();

    const weatherCode = data.current.weather_code;
    const { condition, icon } = weatherCodeToCondition(weatherCode);

    return {
      temperature: Math.round(data.current.temperature_2m),
      condition,
      icon,
      humidity: data.current.relative_humidity_2m,
      wind_speed: data.current.wind_speed_10m,
    };
  } catch (error) {
    console.error('Failed to fetch weather:', error);
    return {
      temperature: 0,
      condition: 'Unknown',
      icon: 'cloud',
    };
  }
}

// Convert WMO weather codes to human-readable conditions
function weatherCodeToCondition(code: number): { condition: string; icon: string } {
  const conditions: Record<number, { condition: string; icon: string }> = {
    0: { condition: 'Clear sky', icon: 'sun' },
    1: { condition: 'Mainly clear', icon: 'sun' },
    2: { condition: 'Partly cloudy', icon: 'cloud-sun' },
    3: { condition: 'Overcast', icon: 'cloud' },
    45: { condition: 'Foggy', icon: 'cloud-fog' },
    48: { condition: 'Depositing rime fog', icon: 'cloud-fog' },
    51: { condition: 'Light drizzle', icon: 'cloud-drizzle' },
    53: { condition: 'Moderate drizzle', icon: 'cloud-drizzle' },
    55: { condition: 'Dense drizzle', icon: 'cloud-drizzle' },
    61: { condition: 'Slight rain', icon: 'cloud-rain' },
    63: { condition: 'Moderate rain', icon: 'cloud-rain' },
    65: { condition: 'Heavy rain', icon: 'cloud-rain' },
    71: { condition: 'Slight snow', icon: 'cloud-snow' },
    73: { condition: 'Moderate snow', icon: 'cloud-snow' },
    75: { condition: 'Heavy snow', icon: 'cloud-snow' },
    80: { condition: 'Slight showers', icon: 'cloud-rain' },
    81: { condition: 'Moderate showers', icon: 'cloud-rain' },
    82: { condition: 'Violent showers', icon: 'cloud-rain' },
    95: { condition: 'Thunderstorm', icon: 'cloud-lightning' },
    96: { condition: 'Thunderstorm with hail', icon: 'cloud-lightning' },
    99: { condition: 'Thunderstorm with heavy hail', icon: 'cloud-lightning' },
  };

  return conditions[code] || { condition: 'Unknown', icon: 'cloud' };
}
