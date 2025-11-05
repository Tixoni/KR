from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import csv, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_storage_dir():
    """Получает путь к папке storage из переменной окружения"""
    return os.getenv("STORAGE_DIR", "/app/storage")

@app.get("/analyze/{filename}")
async def analyze_file(filename: str, columns: str = Query(None, description="Номера столбцов через запятую, начиная с 1")):
    file_path = os.path.join(get_storage_dir(), filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")

    selected_columns = None
    if columns:
        try:
            selected_columns = [int(i) - 1 for i in columns.split(",") if i.strip().isdigit()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный формат параметра columns")

    with open(file_path, "r", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile)
        preview_lines = []
        header = next(reader, None)

        if header is None:
            raise HTTPException(status_code=400, detail="Файл пустой")

        col_count = len(header)
        
        # Проверяем корректность номеров столбцов после чтения заголовка
        if selected_columns:
            for col in selected_columns:
                if col < 0 or col >= col_count:
                    raise HTTPException(status_code=400, detail="Некорректный номер столбца")
        
        numeric_sums = [0.0] * col_count
        numeric_counts = [0] * col_count
        numeric_max = [float("-inf")] * col_count
        has_non_numeric = [False] * col_count

        preview_lines.append(", ".join(header))

        for row in reader:
            preview_lines.append(", ".join(row))
            for j, value in enumerate(row):
                if selected_columns and j not in selected_columns:
                    continue

                try:
                    num = float(value)
                    numeric_sums[j] += num
                    numeric_counts[j] += 1
                    if num > numeric_max[j]:
                        numeric_max[j] = num
                except (ValueError, TypeError):
                    has_non_numeric[j] = True
                    continue

        # Вычисления
        results = []
        for j in range(col_count):
            if selected_columns and j not in selected_columns:
                continue

            if numeric_counts[j] == 0:
                results.append({
                    "column": header[j] if header else f"Колонка {j+1}",
                    "sum": "невозможно определить" if has_non_numeric[j] else 0,
                    "average": "невозможно определить",
                    "max": "невозможно определить"
                })
            else:
                results.append({
                    "column": header[j] if header else f"Колонка {j+1}",
                    "sum": round(numeric_sums[j], 2),
                    "average": round(numeric_sums[j] / numeric_counts[j], 2),
                    "max": round(numeric_max[j], 2)
                })

        return {
            "filename": filename,
            "columns_total": col_count,
            "columns_selected": [header[i] for i in selected_columns] if selected_columns else "Все",
            "preview": "\n".join(preview_lines),
            "analysis": results
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "processing-service"}