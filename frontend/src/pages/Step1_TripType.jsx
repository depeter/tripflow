import React from 'react';
import { useTripContext } from '../context/TripContext';
import './Step1_TripType.css';

const Step1_TripType = ({ onNext }) => {
  const { tripData, updateTripData } = useTripContext();

  const handleSelectType = (type) => {
    updateTripData({
      trip_type: type,
      is_camper: type === 'multi_day'
    });

    // Auto-advance after selection with a slight delay for visual feedback
    setTimeout(() => {
      onNext();
    }, 300);
  };

  return (
    <div className="step1-container">
      <div className="step1-content">
        <div className="step1-hero">
          <h1>Plan Your Next Adventure</h1>
          <p className="hero-subtitle">
            Whether it's a weekend getaway or a day exploration, we'll help you discover amazing places
          </p>
          <div className="stats">
            <span>1000+ locations</span>
            <span>•</span>
            <span>AI-powered recommendations</span>
          </div>
        </div>

        <div className="trip-type-selection">
          <div
            className={`trip-type-card ${tripData.trip_type === 'multi_day' ? 'selected' : ''}`}
            onClick={() => handleSelectType('multi_day')}
          >
            <div className="card-icon">🚐</div>
            <h2>Multi Day Trip</h2>
            <p>Multi-day adventures with overnight stays</p>
            <ul className="features-list">
              <li>Campsite recommendations</li>
              <li>Multi-stop routes</li>
              <li>Accommodation booking</li>
              <li>Day-by-day itinerary</li>
            </ul>
          </div>

          <div
            className={`trip-type-card ${tripData.trip_type === 'day_trip' ? 'selected' : ''}`}
            onClick={() => handleSelectType('day_trip')}
          >
            <div className="card-icon">🚗</div>
            <h2>Day Trip</h2>
            <p>Single day exploration and return</p>
            <ul className="features-list">
              <li>Quick getaway planning</li>
              <li>Local attractions</li>
              <li>Optimized routes</li>
              <li>Time-efficient scheduling</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step1_TripType;
