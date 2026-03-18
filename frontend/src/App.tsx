import { useEffect, useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap, useMapEvents } from 'react-leaflet';
import Select from 'react-select';
import 'leaflet/dist/leaflet.css';
import './App.css';

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

function ClickHandler({ onMapClick }: { onMapClick: (latlng: L.LatLng) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng);
    }
  });
  return null;
}

function App() {
  const [stations, setStations] = useState<Station[]>([]);
  const [lines, setLines] = useState<Line[]>([]);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);

  const [useCoordinate, setUseCoordinate] = useState<boolean>(false);
  const [startStation, setStartStation] = useState<any>(null);
  const [startCoord, setStartCoord] = useState<{lat: number, lng: number} | null>(null);
  const [endStation, setEndStation] = useState<any>(null);
  const [metric, setMetric] = useState<string>('duration');
  const [excludedLines, setExcludedLines] = useState<any[]>([]);
  const [excludedEdges, setExcludedEdges] = useState<any[]>([]);

  const [routePath, setRoutePath] = useState<any[]>([]);
  const [actualStartStation, setActualStartStation] = useState<string>('');
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

  // Generate edge options
  const edgeOptionsMap = new Map<string, any>();
  graphEdges.forEach(edge => {
    if (edge.nid === 0) return; // Don't allow excluding transfers here
    const sNode = graphNodes.find(n => n.id === edge.source);
    const tNode = graphNodes.find(n => n.id === edge.target);
    if (!sNode || !tNode) return;

    // Create a unique key for the undirected edge to avoid duplicates (A->B and B->A)
    const sortedIds = [edge.source, edge.target].sort();
    const key = sortedIds.join('|');

    if (!edgeOptionsMap.has(key)) {
      const lineName = lines.find(l => l.lineid === edge.nid)?.linename || `Line ${edge.nid}`;
      edgeOptionsMap.set(key, {
        value: { source: edge.source, target: edge.target },
        label: `${lineName}: ${sNode.name} ↔ ${tNode.name}`
      });
    }
  });
  const edgeOptions = Array.from(edgeOptionsMap.values()).sort((a, b) => a.label.localeCompare(b.label));

  const calculateRoute = async () => {
    if (!useCoordinate && !startStation) {
      setError("Please select a start station.");
      return;
    }
    if (useCoordinate && !startCoord) {
      setError("Please select a start coordinate on the map.");
      return;
    }
    if (!endStation) {
      setError("Please select an end station.");
      return;
    }

    setError('');
    setRoutePath([]);
    setActualStartStation('');

    const payload: any = {
      end_station: endStation.value,
      metric: metric,
      excluded_lines: excludedLines.map(l => l.value),
      excluded_edges: excludedEdges.map(e => e.value)
    };

    if (useCoordinate) {
      payload.start_coord = startCoord;
    } else {
      payload.start_station = startStation.value;
    }

    try {
      const response = await axios.post('http://localhost:8000/route', payload);
      setRoutePath(response.data.path);
      setActualStartStation(response.data.start_station_used);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred calculating the route.");
    }
  };

  const getRouteSteps = () => {
    if (routePath.length === 0) return [];
    const steps = [];
    if (useCoordinate) {
      steps.push(`Walk to nearest station: ${actualStartStation}`);
    }

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
  const excludedEdgeSet = new Set(excludedEdges.map(e => {
    const sorted = [e.value.source, e.value.target].sort();
    return sorted.join('|');
  }));

  for (const edge of graphEdges) {
    if (edge.nid === 0) continue; // Skip transfers in background draw
    if (excludedSet.has(edge.nid)) continue; // Don't draw excluded lines

    const edgeKey = [edge.source, edge.target].sort().join('|');
    if (excludedEdgeSet.has(edgeKey)) continue; // Don't draw excluded individual edges

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

  const handleMapClick = (latlng: L.LatLng) => {
    if (useCoordinate) {
      setStartCoord({ lat: latlng.lat, lng: latlng.lng });
    }
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <h2>Shanghai Subway Router</h2>

        <div className="form-group">
          <label>Start Location Mode</label>
          <div className="radio-group">
            <label>
              <input type="radio" checked={!useCoordinate} onChange={() => setUseCoordinate(false)} />
              Select Station
            </label>
            <label>
              <input type="radio" checked={useCoordinate} onChange={() => setUseCoordinate(true)} />
              Use Coordinate (Click map)
            </label>
          </div>
        </div>

        {!useCoordinate ? (
          <div className="form-group">
            <label>Start Station</label>
            <Select
              options={stationOptions}
              value={startStation}
              onChange={setStartStation}
              isClearable
            />
          </div>
        ) : (
          <div className="form-group">
            <label>Selected Coordinate</label>
            <div>
              {startCoord ? `Lat: ${startCoord.lat.toFixed(4)}, Lng: ${startCoord.lng.toFixed(4)}` : "Click on the map to set start location"}
            </div>
          </div>
        )}

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
              Fastest
            </label>
            <label>
              <input type="radio" value="distance" checked={metric === 'distance'} onChange={(e) => setMetric(e.target.value)} />
              Shortest
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
            placeholder="Select lines..."
          />
        </div>

        <div className="form-group">
          <label>Exclude Specific Connections</label>
          <Select
            isMulti
            options={edgeOptions}
            value={excludedEdges}
            onChange={(val) => setExcludedEdges(val as any)}
            placeholder="Select connections..."
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
          <ClickHandler onMapClick={handleMapClick} />

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

          {/* Draw Start Coordinate Marker */}
          {useCoordinate && startCoord && (
             <CircleMarker
              center={[startCoord.lat, startCoord.lng]}
              radius={8}
              color="#000"
              fillColor="#007bff"
              fillOpacity={1}
            >
              <Popup>Selected Start Location</Popup>
            </CircleMarker>
          )}

          {useCoordinate && startCoord && routePath.length > 0 && (
            <Polyline
              positions={[[startCoord.lat, startCoord.lng], [routePath[0].lat, routePath[0].lng]]}
              color="#007bff"
              dashArray="5, 10"
              weight={3}
            />
          )}

          <MapUpdater path={routePath} />
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
