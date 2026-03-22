import re

with open("frontend/src/App.tsx", "r") as f:
    code = f.read()

# Add state
search_state = "const [metric, setMetric] = useState<string>('duration');"
replace_state = """const [metric, setMetric] = useState<string>('duration');
  const [algorithm, setAlgorithm] = useState<string>('dijkstra');"""
code = code.replace(search_state, replace_state)

# Add payload
search_payload = """    const payload: any = {
      metric: metric,"""
replace_payload = """    const payload: any = {
      metric: metric,
      algorithm: algorithm,"""
code = code.replace(search_payload, replace_payload)

# Add UI
search_ui = """        <div className="form-group">
          <label>Exclude Lines</label>"""
replace_ui = """        <div className="form-group">
          <label>Algorithm</label>
          <div className="radio-group" style={{flexWrap: 'wrap'}}>
            <label><input type="radio" value="dijkstra" checked={algorithm === 'dijkstra'} onChange={(e) => setAlgorithm(e.target.value)} /> Dijkstra</label>
            <label><input type="radio" value="astar" checked={algorithm === 'astar'} onChange={(e) => setAlgorithm(e.target.value)} /> A* Search</label>
            <label><input type="radio" value="ucs" checked={algorithm === 'ucs'} onChange={(e) => setAlgorithm(e.target.value)} /> UCS</label>
            <label><input type="radio" value="bidirectional" checked={algorithm === 'bidirectional'} onChange={(e) => setAlgorithm(e.target.value)} /> Bidirectional Dijkstra</label>
            <label><input type="radio" value="dls" checked={algorithm === 'dls'} onChange={(e) => setAlgorithm(e.target.value)} /> DLS</label>
            <label><input type="radio" value="ids" checked={algorithm === 'ids'} onChange={(e) => setAlgorithm(e.target.value)} /> IDS</label>
          </div>
        </div>

        <div className="form-group">
          <label>Exclude Lines</label>"""
code = code.replace(search_ui, replace_ui)

with open("frontend/src/App.tsx", "w") as f:
    f.write(code)
