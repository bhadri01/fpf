from tempfile import NamedTemporaryFile
from fastapi.responses import FileResponse
import pandas as pd

# =====================================================
# Function to generate a CSV file from the provided data
# and return it as a downloadable file response.
# =====================================================
def csv_file_response(data, filename: str):
    df = pd.DataFrame(data)

    with NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="") as tmp_file:
        df.to_csv(tmp_file.name, index=False, encoding="utf-8")

    headers = {
        "Content-Disposition": f"attachment; filename={filename}.csv",
        "Content-Type": "text/csv"
    }

    return FileResponse(tmp_file.name, headers=headers, filename=f"{filename}.csv")
