from omada.omada_api import Omada
import json
import gc
import html
from datetime import datetime


# 🔹 Helpers
def getConfig(config_file):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print(f"Config {config_file} file error")
        return {}
    
def getAPI(api_config_file):
    try:
        with open(api_config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print(f"Config {api_config_file} file error")
        return {}


# 🔹 Formatting helpers
def format_bytes(n):
    if not isinstance(n, (int, float)):
        return n
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024


def format_value(col, val):
    if val is None:
        return ""

    if col == "lastSeen" and isinstance(val, (int, float)):
        return datetime.fromtimestamp(val / 1000).strftime("%Y-%m-%d %H:%M:%S")

    if col in ["trafficDown", "trafficUp"]:
        return format_bytes(val)

    if col == "rssi" and isinstance(val, (int, float)):
        if val > -60:
            color = "limegreen"
        elif val > -75:
            color = "orange"
        else:
            color = "red"
        return f'<span style="color:{color};font-weight:bold">{val}</span>'

    if isinstance(val, (list, dict)):
        val = str(val)

    return html.escape(str(val))


# 🔹 MAIN TABLE GENERATOR
def generate_html_table(data, column_map, output_file):
    if not isinstance(data, list):
        data = [data]

    # Filter active devices
    data = [d for d in data if d.get("active", True)]

    # Sort by signal (worst first)
    data.sort(key=lambda x: x.get("rssi", -100))

    columns = list(column_map.keys())

    html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="10">
<title>Omada Dashboard</title>

<style>
body { font-family: Arial; background:#111; color:#eee; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #333; padding: 6px; font-size: 12px; }
th { background: #222; position: sticky; top: 0; }
tr:nth-child(even) { background: #1a1a1a; }
tr:hover { background: #333; }
td { white-space: nowrap; }
input { margin: 10px; padding: 5px; width: 300px; }
</style>
</head>

<body>

<h2>Omada Devices</h2>

<input type="text" id="search" placeholder="Search..." onkeyup="filterTable()">

<table id="deviceTable">
<thead><tr>
"""

    # Headers
    for col in columns:
        html_content += f"<th>{html.escape(column_map.get(col, col))}</th>"

    html_content += "</tr></thead><tbody>"

    # Rows
    for row in data:
        html_content += "<tr>"
        for col in columns:
            val = format_value(col, row.get(col))
            html_content += f"<td>{val}</td>"
        html_content += "</tr>"

    html_content += """
</tbody>
</table>

<script>
function filterTable() {
    const input = document.getElementById("search").value.toLowerCase();
    const rows = document.querySelectorAll("#deviceTable tbody tr");

    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(input) ? "" : "none";
    });
}
</script>

</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)


# 🔹 MAIN
def main(config_file, api_file):
    try:
        config = getConfig(config_file)
        api_config = getAPI(api_file)

        omada = Omada(**config)

        mapping = api_config.get("mapping", {})  # 👈 your column map
        output_file = api_config.get("output", "/var/www/html/omada.html")

        mod_name = api_config.get("mod")
        mod = omada.mod[mod_name]

        api = api_config["api"].format(omada=omada)

        omada._logger.info("[ MG Omada Reports ]")

        result = omada.Commad(mod, api)

        # 🔹 IMPORTANT: extract actual data
        data = result.get("data", result)

        # 🔹 Generate HTML
        generate_html_table(data, mapping, output_file)

        omada.Logout()

        gc.collect()

    except Exception as e:
        print(f"Error: {e}")


# 🔹 ENTRY
if __name__ == "__main__":
    path = "/opt/LMG-local-services/omada_scripts"
    config_file = f"{path}/config.yaml"
    api_config_file = f"{path}/report_config.yaml"

    main(config_file, api_config_file)