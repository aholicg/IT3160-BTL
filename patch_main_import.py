with open("backend/main.py", "r") as f:
    code = f.read()

# Fix import to use relative path since we run from backend root
search_import = "from algorithms import run_dijkstra, run_astar, run_ucs, run_dls, run_ids, run_bidirectional_dijkstra"
replace_import = "from algorithms import run_dijkstra, run_astar, run_ucs, run_dls, run_ids, run_bidirectional_dijkstra"
# It's already there, let's just make sure it loads correctly by starting the server
