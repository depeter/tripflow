import React from 'react';
import './ProgressBar.css';

const steps = [
  { number: 1, label: 'Trip Type' },
  { number: 2, label: 'Duration & Route' },
  { number: 3, label: 'Preferences' },
  { number: 4, label: 'Recommendations' },
  { number: 5, label: 'Customize' },
  { number: 6, label: 'Review' }
];

const ProgressBar = ({ currentStep, completedSteps = [] }) => {
  return (
    <div className="progress-bar">
      <div className="progress-steps">
        {steps.map((step, index) => {
          const isCompleted = completedSteps.includes(step.number);
          const isCurrent = currentStep === step.number;
          const isAccessible = step.number <= currentStep;

          return (
            <React.Fragment key={step.number}>
              <div className={`progress-step ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''} ${isAccessible ? 'accessible' : ''}`}>
                <div className="step-circle">
                  {isCompleted ? (
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M13.3333 4L6 11.3333L2.66667 8" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  ) : (
                    <span>{step.number}</span>
                  )}
                </div>
                <div className="step-label">{step.label}</div>
              </div>

              {index < steps.length - 1 && (
                <div className={`progress-line ${isCompleted ? 'completed' : ''}`}></div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default ProgressBar;
