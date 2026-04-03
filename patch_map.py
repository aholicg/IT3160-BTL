import re

with open("frontend/src/App.tsx", "r") as f:
    code = f.read()

search_tiles = """<TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />"""

# Use standard OSM tiles which are colored (green parks, blue water, tan roads, grey buildings)
# Alternatively, Wikimedia's or OpenTopoMap tiles can provide rich topographical colors.
# OSM standard is reliable and has the classic colorful "Google Maps-like" geography.
replace_tiles = """<TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />"""

code = code.replace(search_tiles, replace_tiles)

with open("frontend/src/App.tsx", "w") as f:
    f.write(code)
