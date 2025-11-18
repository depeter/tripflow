import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { TripProvider } from './context/TripContext';
import Header from './components/Header';
import Login from './pages/Login';
import Register from './pages/Register';
import DiscoveryPage from './pages/DiscoveryPage';
import TripFlowWizard from './pages/TripFlowWizard';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <TripProvider>
          <div className="App">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Routes with header */}
              <Route
                path="/"
                element={
                  <>
                    <Header />
                    <DiscoveryPage />
                  </>
                }
              />

              <Route
                path="/plan-trip"
                element={
                  <>
                    <Header />
                    <TripFlowWizard />
                  </>
                }
              />

              {/* Placeholder routes for future implementation */}
              <Route
                path="/my-trips"
                element={
                  <>
                    <Header />
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                      <h1>My Trips</h1>
                      <p>Your saved trips will appear here (coming soon)</p>
                    </div>
                  </>
                }
              />

              <Route
                path="/profile"
                element={
                  <>
                    <Header />
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                      <h1>Profile</h1>
                      <p>Profile settings (coming soon)</p>
                    </div>
                  </>
                }
              />

              <Route
                path="/settings"
                element={
                  <>
                    <Header />
                    <div style={{ padding: '2rem', textAlign: 'center' }}>
                      <h1>Settings</h1>
                      <p>Account settings (coming soon)</p>
                    </div>
                  </>
                }
              />

              {/* Catch all - redirect to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </TripProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
