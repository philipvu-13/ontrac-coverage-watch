import csv
from collections import defaultdict

import plotly.graph_objects as go

SRC = "out/map_coverage_rows.csv"
OUT = "docs/coverage_map.html"

ALL_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
    "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
    "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
    "WV", "WI", "WY",
]

with open(SRC, encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))

by_origin = defaultdict(list)
for row in rows:
    by_origin[row["sort_center"]].append(row)

origins = sorted(by_origin)
traces = []

for origin in origins:
    served_states, served_days = [], []
    grey_states, grey_labels = [], []

    for row in by_origin[origin]:
        outcome = row["outcome"]

        if outcome == "unserved":
            grey_states.append(row["state"])
            grey_labels.append("not served")
        elif outcome == "no_data":
            grey_states.append(row["state"])
            grey_labels.append("not drawn on the map, unknown")
        else:
            served_states.append(row["state"])
            served_days.append(int(outcome))

    covered = set(served_states) | set(grey_states)
    absent = sorted(state for state in ALL_STATES if state not in covered)

    visible = origin == origins[0]

    traces.append(go.Choropleth(
        locations=served_states,
        z=served_days,
        locationmode="USA-states",
        hovertemplate="%{location}<br>%{z} day transit<extra></extra>",
        colorscale="Viridis_r",
        zmin=1,
        zmax=7,
        marker_line_color="white",
        colorbar_title="Days",
        visible=visible,
    ))

    traces.append(go.Choropleth(
        locations=grey_states,
        z=[0] * len(grey_states),
        locationmode="USA-states",
        text=grey_labels,
        hovertemplate="%{location}<br>%{text}<extra></extra>",
        colorscale=[[0, "#d9d9d9"], [1, "#d9d9d9"]],
        showscale=False,
        marker_line_color="white",
        visible=visible,
    ))

    traces.append(go.Choropleth(
        locations=absent,
        z=[0] * len(absent),
        locationmode="USA-states",
        text=["OnTrac's coverage map does not include this state"] * len(absent),
        hovertemplate="%{location}<br>%{text}<extra></extra>",
        colorscale=[[0, "#f5f0e8"], [1, "#f5f0e8"]],
        showscale=False,
        marker_line_color="white",
        visible=visible,
    ))

buttons = []
for index, origin in enumerate(origins):
    buttons.append(dict(
        label=origin,
        method="update",
        args=[
            {"visible": [i // 3 == index for i in range(3 * len(origins))]},
            {"title": "OnTrac transit days from {}".format(origin)},
        ],
    ))

figure = go.Figure(data=traces)
figure.update_layout(
    title="OnTrac transit days from {}".format(origins[0]),
    geo=dict(scope="usa"),
    updatemenus=[dict(buttons=buttons, x=0.02, y=0.95, xanchor="left")],
)

figure.write_html(OUT, include_plotlyjs="cdn")
print("wrote {}".format(OUT))