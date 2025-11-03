# TripFlow Frontend

React-based frontend for TripFlow travel planning application.

## Setup

```bash
npm install
npm start
```

The app will run on `http://localhost:3000`

## Features (To Be Implemented)

- Flow-based trip planning interface
- Interactive map with location markers
- Personalized recommendations display
- Trip waypoint management
- Event discovery
- User preference configuration

## Development

This is a React app created with Create React App. The main components to implement:

1. **TripFlow Component**: Step-by-step trip planning wizard
2. **MapView Component**: Interactive map with Leaflet
3. **LocationCard Component**: Display location details
4. **RecommendationsList Component**: Show personalized suggestions
5. **TripSummary Component**: Display trip stats and route

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000/api/v1`

See `src/services/api.js` for API client implementation.
