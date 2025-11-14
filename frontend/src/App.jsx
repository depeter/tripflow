import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { TripProvider } from './context/TripContext';
import TripFlowWizard from './pages/TripFlowWizard';
import './App.css';

function App() {
  return (
    <Router>
      <TripProvider>
        <div className="App">
          <Routes>
            <Route path="/" element={<TripFlowWizard />} />
          </Routes>
        </div>
      </TripProvider>
    </Router>
  );
}

export default App;
