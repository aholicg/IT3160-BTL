import { useEffect, useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap, useMapEvents } from 'react-leaflet';
import Select from 'react-select';
import { AsyncPaginate } from 'react-select-async-paginate';
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

function MapUpdater({ path, startCoord, endCoord }: { path: any[], startCoord: any, endCoord: any }) {
  const map = useMap();
  useEffect(() => {
    const points: any[] = path.map((p: any) => [p.lat, p.lng]);
    if (startCoord) points.push([startCoord.lat, startCoord.lng]);
    if (endCoord) points.push([endCoord.lat, endCoord.lng]);

    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [path, startCoord, endCoord, map]);
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

  // Modes: 'station' | 'map'
  const [startMode, setStartMode] = useState<'station' | 'map'>('station');
  const [endMode, setEndMode] = useState<'station' | 'map'>('station');

  // State tracking which one is currently listening for map clicks
  const [activeMapSelector, setActiveMapSelector] = useState<'start' | 'end' | null>(null);

  const [startLocation, setStartLocation] = useState<any>(null); // from dropdown (Station or POI)
  const [endLocation, setEndLocation] = useState<any>(null); // from dropdown (Station or POI)
  const [startCoord, setStartCoord] = useState<{lat: number, lng: number} | null>(null); // from map click
  const [endCoord, setEndCoord] = useState<{lat: number, lng: number} | null>(null); // from map click

  const [metric, setMetric] = useState<string>('duration');
  const [excludedLines, setExcludedLines] = useState<any[]>([]);
  const [excludedEdges, setExcludedEdges] = useState<any[]>([]);

  const [routePath, setRoutePath] = useState<any[]>([]);
  const [actualStartStation, setActualStartStation] = useState<string>('');
  const [actualEndStation, setActualEndStation] = useState<string>('');
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

  const lineOptions = lines.map(l => ({ value: l.lineid, label: l.linename }));

  // Generate edge options
  const edgeOptionsMap = new Map<string, any>();
  graphEdges.forEach(edge => {
    if (edge.nid === 0) return; // Don't allow excluding transfers here
    const sNode = graphNodes.find(n => n.id === edge.source);
    const tNode = graphNodes.find(n => n.id === edge.target);
    if (!sNode || !tNode) return;
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

  const loadLocationOptions = async (search: string, _loadedOptions: any, { page }: any) => {
    // 1. Filter local subway stations
    const localStations = stations
      .filter(s => s.stationname.toLowerCase().includes(search.toLowerCase()))
      .map(s => ({
        value: s.stationname,
        label: `🚇 ${s.stationname} (Subway Station)`,
        type: 'station',
        lat: s.lat,
        lng: s.lng
      }));

    // 2. Fetch from Nominatim API if query is long enough
    let poiOptions: any[] = [];
    if (search.length > 2) {
      try {
        const response = await axios.get(`https://nominatim.openstreetmap.org/search`, {
          params: {
            q: search + ", Shanghai", // bias towards Shanghai
            format: 'json',
            limit: 5
          }
        });
        poiOptions = response.data.map((item: any) => ({
          value: item.display_name,
          label: `📍 ${item.display_name.split(',')[0]} (Place)`,
          type: 'poi',
          lat: parseFloat(item.lat),
          lng: parseFloat(item.lon)
        }));
      } catch (err) {
        console.error("Nominatim search failed", err);
      }
    }

    return {
      options: [...localStations, ...poiOptions],
      hasMore: false,
      additional: {
        page: page + 1
      }
    };
  };

  const calculateRoute = async () => {
    let finalStartCoord = null;
    let finalStartStation = null;
    let finalEndCoord = null;
    let finalEndStation = null;

    // Start evaluation
    if (startMode === 'station') {
      if (!startLocation) return setError("Please select a start location.");
      if (startLocation.type === 'station') finalStartStation = startLocation.value;
      else finalStartCoord = { lat: startLocation.lat, lng: startLocation.lng };
    } else {
      if (!startCoord) return setError("Please click on the map to set start location.");
      finalStartCoord = startCoord;
    }

    // End evaluation
    if (endMode === 'station') {
      if (!endLocation) return setError("Please select an end location.");
      if (endLocation.type === 'station') finalEndStation = endLocation.value;
      else finalEndCoord = { lat: endLocation.lat, lng: endLocation.lng };
    } else {
      if (!endCoord) return setError("Please click on the map to set end location.");
      finalEndCoord = endCoord;
    }

    setError('');
    setRoutePath([]);
    setActualStartStation('');
    setActualEndStation('');

    const payload: any = {
      metric: metric,
      excluded_lines: excludedLines.map(l => l.value),
      excluded_edges: excludedEdges.map(e => e.value)
    };

    if (finalStartStation) payload.start_station = finalStartStation;
    if (finalStartCoord) payload.start_coord = finalStartCoord;

    if (finalEndStation) payload.end_station = finalEndStation;
    if (finalEndCoord) payload.end_coord = finalEndCoord;

    try {
      const response = await axios.post('http://localhost:8000/route', payload);
      setRoutePath(response.data.path);
      setActualStartStation(response.data.start_station_used);
      setActualEndStation(response.data.end_station_used);
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred calculating the route.");
    }
  };

  const getRouteSteps = () => {
    if (routePath.length === 0) return [];
    const steps = [];

    let isStartPoi = (startMode === 'map' || (startMode === 'station' && startLocation?.type === 'poi'));
    let isEndPoi = (endMode === 'map' || (endMode === 'station' && endLocation?.type === 'poi'));

    if (isStartPoi) steps.push(`Walk to nearest station: ${actualStartStation}`);
    else steps.push(`Start at ${routePath[0].name}`);

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

    if (isEndPoi) steps.push(`Walk to your destination from: ${actualEndStation}`);
    else steps.push(`Arrive at ${actualEndStation}`);
    return steps;
  };

  // Background map lines
  const backgroundPolylines = [];
  const excludedSet = new Set(excludedLines.map(l => l.value));
  const excludedEdgeSet = new Set(excludedEdges.map(e => {
    const sorted = [e.value.source, e.value.target].sort();
    return sorted.join('|');
  }));

  for (const edge of graphEdges) {
    if (edge.nid === 0) continue;
    if (excludedSet.has(edge.nid)) continue;

    const edgeKey = [edge.source, edge.target].sort().join('|');
    if (excludedEdgeSet.has(edgeKey)) continue;

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

  // Route path polylines
  const routePolylines = [];
  if (routePath.length > 0) {
    for (let i = 0; i < routePath.length - 1; i++) {
      const p1 = routePath[i];
      const p2 = routePath[i+1];
      if (p1.name === p2.name) continue;

      routePolylines.push(
        <Polyline key={`route-${i}`} positions={[[p1.lat, p1.lng], [p2.lat, p2.lng]]} color="#000" weight={6} opacity={1} />
      );
      routePolylines.push(
        <Polyline key={`route-inner-${i}`} positions={[[p1.lat, p1.lng], [p2.lat, p2.lng]]} color={getLineColor(p1.line_id)} weight={4} opacity={1} />
      );
    }
  }

  const handleMapClick = (latlng: L.LatLng) => {
    if (activeMapSelector === 'start') {
      setStartCoord({ lat: latlng.lat, lng: latlng.lng });
      setActiveMapSelector(null);
    } else if (activeMapSelector === 'end') {
      setEndCoord({ lat: latlng.lat, lng: latlng.lng });
      setActiveMapSelector(null);
    }
  };

  // Compute absolute markers for drawing dashed lines
  const displayStartCoord = startMode === 'map' ? startCoord : (startMode === 'station' && startLocation?.type === 'poi' ? {lat: startLocation.lat, lng: startLocation.lng} : null);
  const displayEndCoord = endMode === 'map' ? endCoord : (endMode === 'station' && endLocation?.type === 'poi' ? {lat: endLocation.lat, lng: endLocation.lng} : null);

  return (
    <div className="app-container">
      <div className="sidebar">
        <h2>Shanghai Subway Router</h2>

        {/* START SECTION */}
        <div className="form-group" style={{border: '1px solid #ccc', padding: '10px', borderRadius: '4px'}}>
          <label>Start Location</label>
          <div className="radio-group" style={{marginBottom: '5px'}}>
            <label><input type="radio" checked={startMode === 'station'} onChange={() => setStartMode('station')} /> Type Place/Station</label>
            <label><input type="radio" checked={startMode === 'map'} onChange={() => setStartMode('map')} /> Click Map</label>
          </div>
          {startMode === 'station' ? (
            <AsyncPaginate
              value={startLocation}
              loadOptions={loadLocationOptions}
              onChange={setStartLocation}
              additional={{ page: 1 }}
              placeholder="Type a station or landmark..."
            />
          ) : (
            <div>
              {startCoord ? `Lat: ${startCoord.lat.toFixed(4)}, Lng: ${startCoord.lng.toFixed(4)}` : "No coordinate selected."}
              <br/>
              <button
                className="button"
                style={{marginTop: '5px', padding: '5px', fontSize: '14px', backgroundColor: activeMapSelector === 'start' ? 'green' : '#007bff'}}
                onClick={() => setActiveMapSelector(activeMapSelector === 'start' ? null : 'start')}>
                {activeMapSelector === 'start' ? "Click map now..." : "Set on map"}
              </button>
            </div>
          )}
        </div>

        {/* END SECTION */}
        <div className="form-group" style={{border: '1px solid #ccc', padding: '10px', borderRadius: '4px'}}>
          <label>End Location</label>
          <div className="radio-group" style={{marginBottom: '5px'}}>
            <label><input type="radio" checked={endMode === 'station'} onChange={() => setEndMode('station')} /> Type Place/Station</label>
            <label><input type="radio" checked={endMode === 'map'} onChange={() => setEndMode('map')} /> Click Map</label>
          </div>
          {endMode === 'station' ? (
            <AsyncPaginate
              value={endLocation}
              loadOptions={loadLocationOptions}
              onChange={setEndLocation}
              additional={{ page: 1 }}
              placeholder="Type a station or landmark..."
            />
          ) : (
            <div>
              {endCoord ? `Lat: ${endCoord.lat.toFixed(4)}, Lng: ${endCoord.lng.toFixed(4)}` : "No coordinate selected."}
              <br/>
              <button
                className="button"
                style={{marginTop: '5px', padding: '5px', fontSize: '14px', backgroundColor: activeMapSelector === 'end' ? 'green' : '#007bff'}}
                onClick={() => setActiveMapSelector(activeMapSelector === 'end' ? null : 'end')}>
                {activeMapSelector === 'end' ? "Click map now..." : "Set on map"}
              </button>
            </div>
          )}
        </div>

        <div className="form-group">
          <label>Optimize For</label>
          <div className="radio-group">
            <label><input type="radio" value="duration" checked={metric === 'duration'} onChange={(e) => setMetric(e.target.value)} /> Fastest</label>
            <label><input type="radio" value="distance" checked={metric === 'distance'} onChange={(e) => setMetric(e.target.value)} /> Shortest</label>
            <label><input type="radio" value="transfers" checked={metric === 'transfers'} onChange={(e) => setMetric(e.target.value)} /> Min Transfers</label>
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

      <div className="map-container" style={{cursor: activeMapSelector ? 'crosshair' : 'grab'}}>
        <MapContainer center={[31.23, 121.47]} zoom={11} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
          <ClickHandler onMapClick={handleMapClick} />

          {backgroundPolylines}
          {routePolylines}

          {stations.map(s => (
            <CircleMarker key={s.stationid} center={[s.lat, s.lng]} radius={3} color="#666" fillColor="#fff" fillOpacity={1}>
              <Popup>{s.stationname}</Popup>
            </CircleMarker>
          ))}

          {/* Start Marker & Polyline */}
          {displayStartCoord && (
             <CircleMarker center={[displayStartCoord.lat, displayStartCoord.lng]} radius={8} color="#000" fillColor="#007bff" fillOpacity={1}>
              <Popup>Start Location</Popup>
            </CircleMarker>
          )}
          {displayStartCoord && routePath.length > 0 && (
            <Polyline positions={[[displayStartCoord.lat, displayStartCoord.lng], [routePath[0].lat, routePath[0].lng]]} color="#007bff" dashArray="5, 10" weight={3} />
          )}

          {/* End Marker & Polyline */}
          {displayEndCoord && (
             <CircleMarker center={[displayEndCoord.lat, displayEndCoord.lng]} radius={8} color="#000" fillColor="#e6194B" fillOpacity={1}>
              <Popup>End Location</Popup>
            </CircleMarker>
          )}
          {displayEndCoord && routePath.length > 0 && (
            <Polyline positions={[[routePath[routePath.length-1].lat, routePath[routePath.length-1].lng], [displayEndCoord.lat, displayEndCoord.lng]]} color="#e6194B" dashArray="5, 10" weight={3} />
          )}

          <MapUpdater path={routePath} startCoord={displayStartCoord} endCoord={displayEndCoord} />
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
