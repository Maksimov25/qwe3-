from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from typing import Dict, Any
import math

app = FastAPI(title="API преобразования координат")

# Включение CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def transform_coordinates(x: float, y: float, z: float) -> Dict[str, float]:
    """
    Преобразование координат согласно алгоритму из практической работы №7
    """
    # Пример преобразования (замените на вашу логику преобразования)
    transformed_x = x * math.cos(math.radians(45)) - y * math.sin(math.radians(45))
    transformed_y = x * math.sin(math.radians(45)) + y * math.cos(math.radians(45))
    transformed_z = z + 100  # Пример смещения
    
    return {
        "transformed_x": round(transformed_x, 3),
        "transformed_y": round(transformed_y, 3),
        "transformed_z": round(transformed_z, 3)
    }

@app.post("/transform")
async def transform_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Преобразование координат из загруженного Excel-файла
    """
    try:
        # Чтение Excel-файла
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Проверка необходимых столбцов
        required_columns = ['x', 'y', 'z']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="Excel-файл должен содержать столбцы x, y, z")
        
        # Преобразование координат
        transformed_data = []
        for _, row in df.iterrows():
            transformed = transform_coordinates(row['x'], row['y'], row['z'])
            transformed_data.append({
                'original_x': row['x'],
                'original_y': row['y'],
                'original_z': row['z'],
                **transformed
            })
        
        # Генерация отчета в формате markdown
        markdown_report = generate_markdown_report(transformed_data)
        
        return {
            "status": "success",
            "transformed_data": transformed_data,
            "markdown_report": markdown_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_markdown_report(data: list) -> str:
    """
    Генерация отчета в формате markdown из преобразованных данных
    """
    report = "# Отчет о преобразовании координат\n\n"
    report += "## Результаты преобразования\n\n"
    report += "| Исходный X | Исходный Y | Исходный Z | Преобразованный X | Преобразованный Y | Преобразованный Z |\n"
    report += "|------------|------------|------------|-------------------|-------------------|-------------------|\n"
    
    for row in data:
        report += f"| {row['original_x']:.3f} | {row['original_y']:.3f} | {row['original_z']:.3f} | "
        report += f"{row['transformed_x']:.3f} | {row['transformed_y']:.3f} | {row['transformed_z']:.3f} |\n"
    
    return report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 