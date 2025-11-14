import React from 'react';
import { useTripContext } from '../context/TripContext';
import ProgressBar from '../components/ProgressBar';
import Step1_TripType from './Step1_TripType';
import Step2_Duration from './Step2_Duration';
import Step3_Preferences from './Step3_Preferences';
import Step4_Recommendations from './Step4_Recommendations';
import Step5_CustomizeRoute from './Step5_CustomizeRoute';
import Step6_ReviewFinalize from './Step6_ReviewFinalize';
import './TripFlowWizard.css';

const TripFlowWizard = () => {
  const { tripData, goToStep, completeStep } = useTripContext();

  const handleNext = () => {
    completeStep(tripData.current_step);
    goToStep(tripData.current_step + 1);
  };

  const handleBack = () => {
    goToStep(Math.max(1, tripData.current_step - 1));
  };

  const renderStep = () => {
    switch (tripData.current_step) {
      case 1:
        return <Step1_TripType onNext={handleNext} />;
      case 2:
        return <Step2_Duration onNext={handleNext} onBack={handleBack} />;
      case 3:
        return <Step3_Preferences onNext={handleNext} onBack={handleBack} />;
      case 4:
        return <Step4_Recommendations onNext={handleNext} onBack={handleBack} />;
      case 5:
        return <Step5_CustomizeRoute onNext={handleNext} onBack={handleBack} />;
      case 6:
        return <Step6_ReviewFinalize onBack={handleBack} />;
      default:
        return <Step1_TripType onNext={handleNext} />;
    }
  };

  // Show footer navigation for Step 2 only (other steps have their own navigation)
  const showNavigation = tripData.current_step === 2;

  return (
    <div className="wizard-container">
      <header className="wizard-header">
        <div className="wizard-logo">
          🗺️ TripFlow
        </div>
      </header>

      <ProgressBar currentStep={tripData.current_step} completedSteps={tripData.completed_steps} />

      <div className="wizard-content">
        {renderStep()}
      </div>

      {showNavigation && (
        <footer className="wizard-footer">
          <button className="btn btn-outline" onClick={handleBack}>
            ← Back
          </button>
          <button className="btn btn-primary" onClick={handleNext}>
            Continue →
          </button>
        </footer>
      )}
    </div>
  );
};

export default TripFlowWizard;
