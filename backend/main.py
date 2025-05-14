from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import math
import numpy as np
import json
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_parameters(path="parameters.json"):
    """Загружает параметры из JSON"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Ошибка чтения параметров: {str(e)}")

def apply_transformation(x, y, z, params):
    """Применяет преобразование по формулам из практической работы"""
    dx, dy, dz = params["ΔX"], params["ΔY"], params["ΔZ"]
    wx, wy, wz = params["ωx"], params["ωy"], params["ωz"]
    m = params["m"]

    # Преобразование координат
    new_x = (1 + m) * (x - wz * y + wy * z) + dx
    new_y = (1 + m) * (wz * x + y - wx * z) + dy
    new_z = (1 + m) * (-wy * x + wx * y + z) + dz

    return round(new_x, 3), round(new_y, 3), round(new_z, 3)

@app.post("/transform")
async def transform_file(file: UploadFile = File(...)):
    try:
        # Чтение файла
        df = pd.read_excel(await file.read())

        # Проверка столбцов
        if not all(col in df.columns for col in ['x', 'y', 'z']):
            raise HTTPException(status_code=400, detail="Файл должен содержать колонки x, y, z")

        # Загрузка параметров
        params = load_parameters()
        initial_system = "СК-42"
        target_system = "ПЗ-90.11"

        from_params = params[initial_system]
        to_params = params[target_system]

        # Преобразование
        transformed_data = []
        for _, row in df.iterrows():
            x, y, z = float(row['x']), float(row['y']), float(row['z'])
            tx, ty, tz = apply_transformation(x, y, z, from_params)
            tx, ty, tz = apply_transformation(tx, ty, tz, to_params)
            transformed_data.append({
                "original_x": x,
                "original_y": y,
                "original_z": z,
                "new_x": tx,
                "new_y": ty,
                "new_z": tz
            })

        # Генерация отчета
        report = f"# Отчет о преобразовании\n"
        report += f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        report += "| X | Y | Z | Новый X | Новый Y | Новый Z |\n"
        report += "|---|---|---|---------|---------|---------|\n"

        for item in transformed_data[:5]:  # Только первые 5 записей для отчета
            report += f"|{item['original_x']}|{item['original_y']}|{item['original_z']}|{item['new_x']}|{item['new_y']}|{item['new_z']}|\n"

        return {
            "status": "success",
            "data": transformed_data,
            "report": report
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}