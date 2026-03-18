import { useEffect, useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet';
import Select from 'react-select';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Fix leaflet icon issue in react
import L from 'leaflet';

interface Station {
  stationid: number;
  stationname: string;
  lat: number;
  lng: number;
}

interface Line {
  lineid: number;
  linename: string;
  fullnames: string;
}

interface GraphEdge {
  source: string;
  target: string;
  nid: number;
  distance: number;
  duration: number;
}

interface GraphNode {
  id: string;
  station_id: number;
  name: string;
  lat: number;
  lng: number;
  line_id: number;
}

const colors = [
  '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9'
];

function getLineColor(lineId: number) {
  return colors[lineId % colors.length];
}

function MapUpdater({ path }: { path: any[] }) {
  const map = useMap();
  useEffect(() => {
    if (path.length > 0) {
      const bounds = L.latLngBounds(path.map((p: any) => [p.lat, p.lng]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [path, map]);
  return null;
}

function App() {
  const [stations, setStations] = useState<Station[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);

  const [startStation, setStartStation] = useState<any>(null);
  const [endStation, setEndStation] = useState<any>(null);
  const [metric, setMetric] = useState<string>('duration');
  const [excludedLines, setExcludedLines] = useState<any[]>([]);

  const [routePath, setRoutePath] = useState<any[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [stationsRes, linesRes, graphRes] = await Promise.all([
          axios.get('http://localhost:8000/stations'),
          axios.get('http://localhost:8000/lines'),
          axios.get('http://localhost:8000/graph')
        ]);
        setStations(stationsRes.data);
        setLines(linesRes.data);
        setGraphNodes(graphRes.data.nodes);
        setGraphEdges(graphRes.data.edges);
      } catch (err) {
        console.error("Failed to load initial data", err);
      }
    };
    fetchData();
  }, []);

  const stationOptions = stations.map(s => ({ value: s.stationname, label: s.stationname }));
  const lineOptions = lines.map(l => ({ value: l.lineid, label: l.linename }));

  const calculateRoute = async () => {
    if (!startStation || !endStation) {
      setError("Please select both start and end stations.");
      return;
    }
    setError('');
    setRoutePath([]);

    try {
      const response = await axios.post('http://localhost:8000/route', {
        start_station: startStation.value,
        end_station: endStation.value,
        metric: metric,
        excluded_lines: excludedLines.map(l => l.value)
      });
      setRoutePath(response.data.path);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred calculating the route.");
    }
  };

  const getRouteSteps = () => {
    if (routePath.length === 0) return [];
    const steps = [];
    let currentLine = routePath[0].line_id;
    let currentStart = routePath[0].name;

    for (let i = 1; i < routePath.length; i++) {
      if (routePath[i].line_id !== currentLine) {
        steps.push(`Take Line ${currentLine} from ${currentStart} to ${routePath[i-1].name}`);
        steps.push(`Transfer at ${routePath[i-1].name} to Line ${routePath[i].line_id}`);
        currentLine = routePath[i].line_id;
        currentStart = routePath[i-1].name;
      }
    }
    steps.push(`Take Line ${currentLine} from ${currentStart} to ${routePath[routePath.length-1].name}`);
    return steps;
  };

  // Pre-calculate polyline segments for the background map
  const backgroundPolylines = [];
  const excludedSet = new Set(excludedLines.map(l => l.value));

  for (const edge of graphEdges) {
    if (edge.nid === 0) continue; // Skip transfers in background draw
    if (excludedSet.has(edge.nid)) continue; // Don't draw excluded lines

    const sourceNode = graphNodes.find(n => n.id === edge.source);
    const targetNode = graphNodes.find(n => n.id === edge.target);
    if (sourceNode && targetNode) {
      backgroundPolylines.push(
        <Polyline
          key={`${edge.source}-${edge.target}-${edge.nid}`}
          positions={[[sourceNode.lat, sourceNode.lng], [targetNode.lat, targetNode.lng]]}
          color={getLineColor(edge.nid)}
          weight={3}
          opacity={0.5}
        />
      );
    }
  }

  // Calculate route polyline
  const routePolylines = [];
  if (routePath.length > 0) {
    for (let i = 0; i < routePath.length - 1; i++) {
      const p1 = routePath[i];
      const p2 = routePath[i+1];
      if (p1.name === p2.name) continue; // It's a transfer step, coordinates are the same

      routePolylines.push(
        <Polyline
          key={`route-${i}`}
          positions={[[p1.lat, p1.lng], [p2.lat, p2.lng]]}
          color="#000" // Black for highlighted route
          weight={6}
          opacity={1}
        />
      );

      // Draw inner colored line
      routePolylines.push(
        <Polyline
          key={`route-inner-${i}`}
          positions={[[p1.lat, p1.lng], [p2.lat, p2.lng]]}
          color={getLineColor(p1.line_id)}
          weight={4}
          opacity={1}
        />
      );
    }
  }

  return (
    <div className="app-container">
      <div className="sidebar">
        <h2>Shanghai Subway Router</h2>

        <div className="form-group">
          <label>Start Station</label>
          <Select
            options={stationOptions}
            value={startStation}
            onChange={setStartStation}
            isClearable
          />
        </div>

        <div className="form-group">
          <label>End Station</label>
          <Select
            options={stationOptions}
            value={endStation}
            onChange={setEndStation}
            isClearable
          />
        </div>

        <div className="form-group">
          <label>Optimize For</label>
          <div className="radio-group">
            <label>
              <input type="radio" value="duration" checked={metric === 'duration'} onChange={(e) => setMetric(e.target.value)} />
              Fastest (Duration)
            </label>
            <label>
              <input type="radio" value="distance" checked={metric === 'distance'} onChange={(e) => setMetric(e.target.value)} />
              Shortest (Distance)
            </label>
            <label>
              <input type="radio" value="transfers" checked={metric === 'transfers'} onChange={(e) => setMetric(e.target.value)} />
              Min Transfers
            </label>
          </div>
        </div>

        <div className="form-group">
          <label>Exclude Lines</label>
          <Select
            isMulti
            options={lineOptions}
            value={excludedLines}
            onChange={(val) => setExcludedLines(val as any)}
            placeholder="Select lines to exclude..."
          />
        </div>

        <button className="button" onClick={calculateRoute}>Find Route</button>

        {error && <div className="error-message">{error}</div>}

        {routePath.length > 0 && (
          <div className="route-steps">
            <h3>Route Steps</h3>
            <ol>
              {getRouteSteps().map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
            <p style={{marginTop: '10px'}}><strong>Total Stops:</strong> {routePath.length - 1}</p>
          </div>
        )}
      </div>

      <div className="map-container">
        <MapContainer center={[31.23, 121.47]} zoom={11} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
          {backgroundPolylines}
          {routePolylines}

          {/* Draw stations as small dots */}
          {stations.map(s => (
            <CircleMarker
              key={s.stationid}
              center={[s.lat, s.lng]}
              radius={3}
              color="#666"
              fillColor="#fff"
              fillOpacity={1}
            >
              <Popup>{s.stationname}</Popup>
            </CircleMarker>
          ))}

          <MapUpdater path={routePath} />
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
