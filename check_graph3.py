import pandas as pd
stations = pd.read_csv('stations_sh.csv')
print("Unique lines in CSV:")
all_lines = set()
for linenames in stations['linenames']:
    names = eval(linenames)
    if isinstance(names, str):
        all_lines.add(names)
    else:
        all_lines.update(names)
print(all_lines)

print("\nUnique line ids in CSV:")
all_line_ids = set()
for lineids in stations['lineids']:
    if '{' in lineids:
        # e.g., "{1, 2}" or "{1}"
        ids = lineids.strip('{}').split(',')
        for i in ids:
            if i.strip():
                all_line_ids.add(int(i.strip()))
    else:
        all_line_ids.add(int(lineids))
print(sorted(list(all_line_ids)))
