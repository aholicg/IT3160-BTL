# Shanghai Subway Router

A full-stack application simulating a "Google Maps"-like experience for the Shanghai subway network.
It supports pathfinding based on fastest time (duration), shortest distance, or minimum transfers. You can also filter out specific subway lines to exclude them from the route calculation.

## Components

The project consists of two main components:
1. **Backend (Python / FastAPI):**
   - Parses the `stations_sh.csv` and `lines_sh.csv` data to build location context.
   - Loads the `PrimalGraph_sh_2020.gml` graph into `networkx` for algorithmic pathfinding.
   - Exposes REST API endpoints (`/stations`, `/lines`, `/graph`, `/route`).
   - Uses Dijkstra's algorithm to calculate the optimal path, adding weights dynamically based on the requested optimization metric and accounting for transfer wait times and lengths.

2. **Frontend (React / TypeScript / Vite):**
   - Built with React and TypeScript.
   - Utilizes `react-leaflet` to render a geographical map layer based on OpenStreetMap.
   - Fetches and visualizes the network and coordinates.
   - Allows users to interactively search and pick `Start` and `End` stations with auto-completion.
   - Displays highlighted route polylines and step-by-step text instructions.

## Prerequisites

- **Python 3.8+**
- **Node.js 18+** & **npm**

## How to Run

### 1. Start the Backend

Open a terminal and navigate to the project root:

```bash
cd backend
# (Optional) Create and activate a virtual environment
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend server will run on `http://localhost:8000`.

### 2. Start the Frontend

Open another terminal and navigate to the project root:

```bash
cd frontend
npm install
npm run build
npm run preview
```

The terminal will provide a localhost link (e.g., `http://localhost:4173`). Open that URL in your web browser to use the application.

## Data Processing Details

- **Consistency:** The system confirms consistency between `stations_sh.csv` and `PrimalGraph_sh_2020.gml`.
- **The Maglev Line (Line 19):** Listed in the CSV data but excluded from routing since there are no node connections provided for it in the GML graph.
- **Transfers:** Transfers within a single station across different line platforms are modeled as explicit edges with `nid=0`. Transfers are naturally penalized when optimizing for "Minimum Transfers" or have an assumed penalty time (3 mins) when optimizing for "Duration" to realistically simulate foot-traffic delays.
