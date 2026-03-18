with open("frontend/src/App.tsx", "r") as f:
    code = f.read()

search_state = """  const [excludedLines, setExcludedLines] = useState<any[]>([]);"""
replace_state = """  const [excludedLines, setExcludedLines] = useState<any[]>([]);
  const [excludedEdges, setExcludedEdges] = useState<any[]>([]);"""
code = code.replace(search_state, replace_state)

search_api = """        excluded_lines: excludedLines.map(l => l.value)"""
replace_api = """        excluded_lines: excludedLines.map(l => l.value),
        excluded_edges: excludedEdges.map(e => e.value)"""
code = code.replace(search_api, replace_api)

search_edge_options = """  const lineOptions = lines.map(l => ({ value: l.lineid, label: l.linename }));"""
replace_edge_options = """  const lineOptions = lines.map(l => ({ value: l.lineid, label: l.linename }));

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
  const edgeOptions = Array.from(edgeOptionsMap.values()).sort((a, b) => a.label.localeCompare(b.label));"""
code = code.replace(search_edge_options, replace_edge_options)

search_bg_polyline = """  const excludedSet = new Set(excludedLines.map(l => l.value));

  for (const edge of graphEdges) {
    if (edge.nid === 0) continue; // Skip transfers in background draw
    if (excludedSet.has(edge.nid)) continue; // Don't draw excluded lines"""
replace_bg_polyline = """  const excludedSet = new Set(excludedLines.map(l => l.value));
  const excludedEdgeSet = new Set(excludedEdges.map(e => {
    const sorted = [e.value.source, e.value.target].sort();
    return sorted.join('|');
  }));

  for (const edge of graphEdges) {
    if (edge.nid === 0) continue; // Skip transfers in background draw
    if (excludedSet.has(edge.nid)) continue; // Don't draw excluded lines

    const edgeKey = [edge.source, edge.target].sort().join('|');
    if (excludedEdgeSet.has(edgeKey)) continue; // Don't draw excluded individual edges"""
code = code.replace(search_bg_polyline, replace_bg_polyline)


search_jsx = """        <div className="form-group">
          <label>Exclude Lines</label>
          <Select
            isMulti
            options={lineOptions}
            value={excludedLines}
            onChange={(val) => setExcludedLines(val as any)}
            placeholder="Select lines to exclude..."
          />
        </div>"""
replace_jsx = """        <div className="form-group">
          <label>Exclude Lines</label>
          <Select
            isMulti
            options={lineOptions}
            value={excludedLines}
            onChange={(val) => setExcludedLines(val as any)}
            placeholder="Select lines to exclude..."
          />
        </div>

        <div className="form-group">
          <label>Exclude Specific Connections</label>
          <Select
            isMulti
            options={edgeOptions}
            value={excludedEdges}
            onChange={(val) => setExcludedEdges(val as any)}
            placeholder="Select connections to avoid..."
          />
        </div>"""
code = code.replace(search_jsx, replace_jsx)

with open("frontend/src/App.tsx", "w") as f:
    f.write(code)
