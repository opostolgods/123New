# html_report.py
def generate_html_report(api_data: dict) -> str:
    all_records = []
    if "List" in api_data:
        for _, db_obj in api_data["List"].items():
            if "Data" in db_obj:
                all_records.extend(db_obj["Data"])
    if not all_records:
        return """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Консоль поиска</title>
  <style>
    body { background-color: #000; color: #0f0; font-family: 'Courier New', monospace; padding: 20px; }
    .no-data { text-align: center; font-size: 1.2em; margin-top: 40px; }
    footer { text-align: center; margin-top: 30px; font-size: 0.9em; }
  </style>
</head>
<body>
  <div class="no-data">Данные не найдены</div>
  <footer>© 2025 Все @DuetSearch_Bot</footer>
</body>
</html>"""
    
    html_template = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Консоль поиска</title>
  <style>
    body {
      background-color: #000;
      color: #0f0;
      font-family: 'Courier New', monospace;
      padding: 20px;
      margin: 0;
    }
    .console {
      background-color: #111;
      padding: 20px;
      border: 1px solid #0f0;
      border-radius: 5px;
      box-shadow: 0 0 10px #0f0;
    }
    .record {
      margin-bottom: 10px;
    }
    .record .key {
      color: #0ff;
      font-weight: bold;
    }
    .record .value {
      color: #0f0;
    }
    footer {
      text-align: center;
      margin-top: 20px;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <div class="console">
    __RECORDS_PLACEHOLDER__
  </div>
  <footer>© 2025 @DuetSearch_Bot</footer>
</body>
</html>
"""
    records_html = ""
    for idx, record in enumerate(all_records, start=1):
        records_html += f"Результат #{idx}:<br>\n"
        for k, v in record.items():
            records_html += f"<span class='key'>{k}:</span> <span class='value'>{v}</span><br>\n"
        records_html += "<br>\n"
    final_html = html_template.replace("__RECORDS_PLACEHOLDER__", records_html)
    return final_html
