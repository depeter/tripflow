import React, { useState } from 'react';
import { useTripContext } from '../context/TripContext';
import MapView from '../components/MapView';
import SafeHtml from '../components/SafeHtml';
import { format } from 'date-fns';
import { createTrip } from '../services/tripsService';
import { generateTripPDF } from '../services/pdfService';
import './Step6_ReviewFinalize.css';

const Step6_ReviewFinalize = ({ onBack }) => {
  const { tripData, resetTrip } = useTripContext();
  const [tripName, setTripName] = useState('My Amazing Trip');
  const [startDate, setStartDate] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const waypoints = tripData.selected_waypoints || [];
  const isMultiDay = tripData.trip_type === 'multi_day';

  const handleSaveTrip = async () => {
    setIsSaving(true);
    try {
      const tripPayload = {
        ...tripData,
        tripName: tripName,
        startDate: startDate || null
      };

      const savedTrip = await createTrip(tripPayload);
      console.log('Trip saved successfully:', savedTrip);

      // Store trip ID in context if needed
      // updateTripData({ trip_id: savedTrip.id });

      setIsSaved(true);
    } catch (error) {
      console.error('Failed to save trip:', error);
      alert('Failed to save trip. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPDF = () => {
    try {
      generateTripPDF(tripData, tripName, startDate);
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Failed to generate PDF. Please try again.');
    }
  };

  const handleShareTrip = () => {
    const shareUrl = `${window.location.origin}/trip/${Date.now()}`;
    navigator.clipboard.writeText(shareUrl);
    alert('Trip link copied to clipboard!');
  };

  const handleEmailItinerary = () => {
    alert('Email functionality would be implemented here');
  };

  const handleStartNew = () => {
    if (window.confirm('Are you sure you want to start a new trip? This will clear your current planning.')) {
      resetTrip();
    }
  };

  const calculateTotalCost = () => {
    let total = 0;
    waypoints.forEach(wp => {
      if (wp.price_per_night && wp.price_per_night > 0) {
        total += wp.price_per_night;
      }
    });
    return total;
  };

  // Build map markers
  const buildMapMarkers = () => {
    const markers = [];

    if (tripData.start_coordinates) {
      markers.push({
        id: 'start',
        position: [tripData.start_coordinates.lat, tripData.start_coordinates.lng],
        popup: tripData.start_address
      });
    }

    waypoints.forEach((wp, idx) => {
      markers.push({
        id: `wp-${idx}`,
        position: [wp.coordinates.lat, wp.coordinates.lng],
        popup: wp.name,
        numbered: true,
        number: idx + 1
      });
    });

    return markers;
  };

  const markers = buildMapMarkers();
  const mapCenter = tripData.start_coordinates
    ? [tripData.start_coordinates.lat, tripData.start_coordinates.lng]
    : [50.8503, 4.3517];

  const totalCost = calculateTotalCost();

  return (
    <div className="step6-container">
      <div className="review-layout">
        {/* Left Side - Trip Details */}
        <div className="review-details">
          <div className="review-header">
            <h2>Review Your Trip</h2>
            <p className="review-subtitle">Everything looks good? Save and share your adventure!</p>
          </div>

          {/* Trip Name & Dates */}
          <section className="review-section">
            <h3 className="section-title">Trip Information</h3>
            <div className="form-row">
              <div className="form-group full-width">
                <label>Trip Name</label>
                <input
                  type="text"
                  value={tripName}
                  onChange={(e) => setTripName(e.target.value)}
                  className="text-input"
                  placeholder="Give your trip a name"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Start Date (optional)</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="text-input"
                />
              </div>
              <div className="form-group">
                <label>Duration</label>
                <div className="readonly-field">
                  {isMultiDay ? `${tripData.duration_days} days` : `${tripData.duration_hours} hours`}
                </div>
              </div>
            </div>
          </section>

          {/* Route Overview */}
          <section className="review-section">
            <h3 className="section-title">Route Overview</h3>
            <div className="itinerary">
              <div className="itinerary-item">
                <div className="itinerary-marker start">Start</div>
                <div className="itinerary-content">
                  <div className="itinerary-title">{tripData.start_address}</div>
                  {startDate && <div className="itinerary-date">{format(new Date(startDate), 'MMMM d, yyyy')}</div>}
                </div>
              </div>

              {waypoints.map((wp, idx) => (
                <div key={wp.id} className="itinerary-item">
                  <div className="itinerary-marker">{idx + 1}</div>
                  <div className="itinerary-content">
                    <div className="itinerary-title">{wp.name}</div>
                    <div className="itinerary-meta">
                      {wp.type} • ⭐{wp.rating}
                      {wp.price_per_night > 0 && ` • €${wp.price_per_night}/night`}
                    </div>
                    {wp.description && (
                      <SafeHtml html={wp.description} className="itinerary-description" />
                    )}
                    {wp.tags && (
                      <div className="itinerary-tags">
                        {wp.tags.map((tag, tagIdx) => (
                          <span key={tagIdx} className="itinerary-tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {tripData.is_round_trip && (
                <div className="itinerary-item">
                  <div className="itinerary-marker end">End</div>
                  <div className="itinerary-content">
                    <div className="itinerary-title">Return to {tripData.start_address}</div>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Trip Stats */}
          <section className="review-section">
            <h3 className="section-title">Trip Summary</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-icon">🗺️</span>
                <div>
                  <div className="summary-label">Stops</div>
                  <div className="summary-value">{waypoints.length}</div>
                </div>
              </div>
              <div className="summary-item">
                <span className="summary-icon">📏</span>
                <div>
                  <div className="summary-label">Distance</div>
                  <div className="summary-value">{tripData.route_stats?.total_distance_km || 0} km</div>
                </div>
              </div>
              <div className="summary-item">
                <span className="summary-icon">⏱️</span>
                <div>
                  <div className="summary-label">Driving</div>
                  <div className="summary-value">{tripData.route_stats?.estimated_driving_hours || 0} hrs</div>
                </div>
              </div>
              <div className="summary-item">
                <span className="summary-icon">💰</span>
                <div>
                  <div className="summary-label">Est. Cost</div>
                  <div className="summary-value">€{totalCost}</div>
                </div>
              </div>
            </div>
          </section>

          {/* Actions */}
          <section className="review-section">
            <h3 className="section-title">Save & Share</h3>
            <div className="action-buttons">
              <button
                className={`btn ${isSaved ? 'btn-success' : 'btn-primary'} large`}
                onClick={handleSaveTrip}
                disabled={isSaving}
              >
                {isSaving ? '💾 Saving...' : isSaved ? '✓ Saved!' : '💾 Save Trip'}
              </button>
              <button className="btn btn-outline" onClick={handleDownloadPDF}>
                📄 Download PDF
              </button>
              <button className="btn btn-outline" onClick={handleEmailItinerary}>
                📧 Email Itinerary
              </button>
              <button className="btn btn-outline" onClick={handleShareTrip}>
                🔗 Share Trip
              </button>
            </div>
          </section>
        </div>

        {/* Right Side - Map Preview */}
        <div className="review-map">
          <div className="map-wrapper">
            <MapView
              center={mapCenter}
              zoom={6}
              markers={markers}
            />
          </div>

          <div className="trip-badge">
            <div className="badge-header">
              <span className="badge-icon">✨</span>
              <span className="badge-title">Your Trip is Ready!</span>
            </div>
            <p className="badge-text">
              {waypoints.length} amazing {waypoints.length === 1 ? 'location' : 'locations'} to explore
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="step6-footer">
        <button className="btn btn-outline" onClick={onBack}>
          ← Back to Edit
        </button>
        <button className="btn btn-secondary" onClick={handleStartNew}>
          ✨ Plan Another Trip
        </button>
      </div>
    </div>
  );
};

export default Step6_ReviewFinalize;
