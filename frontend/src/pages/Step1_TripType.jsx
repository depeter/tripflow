import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTripContext } from '../context/TripContext';
import './Step1_TripType.css';

const Step1_TripType = ({ onNext }) => {
  const { t } = useTranslation(['wizard']);
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
          <h1>{t('step1.title')}</h1>
          <p className="hero-subtitle">
            {t('step1.subtitle')}
          </p>
          <div className="stats">
            <span>{t('step1.stats.locations', { count: 1000 })}</span>
            <span>•</span>
            <span>{t('step1.stats.aiPowered')}</span>
          </div>
        </div>

        <div className="trip-type-selection">
          <div
            className={`trip-type-card ${tripData.trip_type === 'multi_day' ? 'selected' : ''}`}
            onClick={() => handleSelectType('multi_day')}
          >
            <div className="card-icon">🚐</div>
            <h2>{t('step1.multiDay.title')}</h2>
            <p>{t('step1.multiDay.description')}</p>
            <ul className="features-list">
              <li>{t('step1.multiDay.features.campsites')}</li>
              <li>{t('step1.multiDay.features.multiStop')}</li>
              <li>{t('step1.multiDay.features.accommodation')}</li>
              <li>{t('step1.multiDay.features.itinerary')}</li>
            </ul>
          </div>

          <div
            className={`trip-type-card ${tripData.trip_type === 'day_trip' ? 'selected' : ''}`}
            onClick={() => handleSelectType('day_trip')}
          >
            <div className="card-icon">🚗</div>
            <h2>{t('step1.dayTrip.title')}</h2>
            <p>{t('step1.dayTrip.description')}</p>
            <ul className="features-list">
              <li>{t('step1.dayTrip.features.attractions')}</li>
              <li>{t('step1.dayTrip.features.optimizedRoutes')}</li>
              <li>{t('step1.dayTrip.features.timeManagement')}</li>
              <li>{t('step1.dayTrip.features.localSpots')}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step1_TripType;
