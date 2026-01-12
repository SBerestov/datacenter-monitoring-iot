from db.connection import fetch_all
from pathlib import Path
import os

SVG_PATH = Path("../images/doc8.svg")

def convert_encoding(text, from_encoding='cp1252', to_encoding='utf-8'):
    """Конвертирует текст из одной кодировки в другую"""
    try:
        return text.encode(from_encoding).decode(to_encoding)
    except:
        return text

def date_to_months(month_value):
    """Конвертация номера месяца в русское название"""
    months = {
        '01': 'Янв.', '02': 'Фев.', '03': 'Мар.', '04': 'Апр.',
        '05': 'Май', '06': 'Июн.', '07': 'Июл.', '08': 'Авг.',
        '09': 'Сен.', '10': 'Окт.', '11': 'Ноя.', '12': 'Дек.'
    }
    return months.get(month_value, month_value)

def generate_svg(type_id, property_id, source_name, datetime_value=None):
    """Генерирует SVG график"""
    
    os.makedirs(SVG_PATH.parent, exist_ok=True)
    
    # Формируем запрос с параметрами
    query, params = build_query(type_id, property_id, source_name, datetime_value)
    
    data = fetch_all(query, params)
    
    if not data:
        svg_content = create_empty_svg()
        SVG_PATH.write_text(svg_content, encoding='utf-8')
        return
    
    # Получаем русское название свойства
    prop_query = """
        SELECT property_name_rus 
        FROM properties 
        WHERE type_id = %s AND column_id = %s
    """
    prop_data = fetch_all(prop_query, (type_id, property_id))
    
    property_name_rus = ""
    if prop_data:
        property_name_rus = convert_encoding(prop_data[0]["property_name_rus"])
    
    values = [float(row["field"]) for row in data]
    labels = [row["label"] for row in data]
    label_type = get_label_type(datetime_value)
    
    formatted_labels = format_labels(labels, label_type)
    
    svg_content = build_svg(values, formatted_labels, property_name_rus)
    
    # Сохраняем файл
    SVG_PATH.write_text(svg_content, encoding='utf-8')
    print(f"SVG сохранен в {SVG_PATH}")

def get_label_type(datetime_value):
    """Определяет тип подписей"""
    if not datetime_value:
        return "date_full"
    if "date=" in datetime_value:
        return "hour"
    if "week=" in datetime_value:
        return "date_short"
    if "month=" in datetime_value:
        return "day"
    return "date_full"

def build_query(type_id, property_id, source_name, datetime_value):
    """Формирует SQL запрос и параметры"""
    
    if not datetime_value:
        # По умолчанию - группировка по дням
        query = """
            SELECT 
                DATE_FORMAT(datetime, '%y-%m-%d') as label, 
                ROUND(AVG(value), 2) as field
            FROM data_sources
            WHERE type_id = %s 
              AND properties_id = %s
              AND data_source_name = %s
            GROUP BY DATE_FORMAT(datetime, '%y-%m-%d')
            ORDER BY DATE_FORMAT(datetime, '%y-%m-%d') ASC
        """
        return query, (type_id, property_id, source_name)
    
    if "date=" in datetime_value:
        day = datetime_value.split("=")[1]
        query = """
            SELECT 
                DATE_FORMAT(datetime, '%H') as label, 
                ROUND(AVG(value), 2) as field
            FROM data_sources
            WHERE DATE(datetime) = %s
              AND type_id = %s
              AND properties_id = %s
              AND data_source_name = %s
            GROUP BY DATE_FORMAT(datetime, '%H')
        """
        return query, (day, type_id, property_id, source_name)
    
    if "week=" in datetime_value:
        year_week = datetime_value.replace("week=", "")
        year, week = year_week.split("-W")
        query = """
            SELECT 
                DATE_FORMAT(datetime, '%m-%d') as label, 
                ROUND(AVG(value), 2) as field
            FROM data_sources
            WHERE YEAR(datetime) = %s
              AND WEEK(datetime, 1) = %s
              AND type_id = %s
              AND properties_id = %s
              AND data_source_name = %s
            GROUP BY DATE_FORMAT(datetime, '%m-%d')
            ORDER BY DATE_FORMAT(datetime, '%m-%d') ASC
        """
        return query, (int(year), int(week), type_id, property_id, source_name)
    
    if "month=" in datetime_value:
        year_month = datetime_value.replace("month=", "")
        year, month = year_month.split("-")
        query = """
            SELECT 
                DATE_FORMAT(datetime, '%d') as label, 
                ROUND(AVG(value), 2) as field
            FROM data_sources
            WHERE YEAR(datetime) = %s
              AND MONTH(datetime) = %s
              AND type_id = %s
              AND properties_id = %s
              AND data_source_name = %s
            GROUP BY DATE_FORMAT(datetime, '%d')
            ORDER BY DATE_FORMAT(datetime, '%d') ASC
        """
        return query, (int(year), int(month), type_id, property_id, source_name)
    
    # По умолчанию
    query = """
        SELECT 
            DATE_FORMAT(datetime, '%y-%m-%d') as label, 
            ROUND(AVG(value), 2) as field
        FROM data_sources
        WHERE type_id = %s 
          AND properties_id = %s
          AND data_source_name = %s
        GROUP BY DATE_FORMAT(datetime, '%y-%m-%d')
        ORDER BY DATE_FORMAT(datetime, '%y-%m-%d') ASC
    """
    return query, (type_id, property_id, source_name)

def format_labels(labels, label_type):
    """Форматирует подписи для оси X"""
    formatted = []
    for label in labels:
        if label_type == "hour":
            formatted.append(f"{label} ч.")
        elif label_type == "day":
            formatted.append(f"{label}")
        elif label_type == "date_short":
            # Формат "mm-dd"
            if label and len(label) == 5:
                month, day = label.split('-')
                month_name = date_to_months(month)
                formatted.append(f"{day} {month_name}")
            else:
                formatted.append(str(label))
        elif label_type == "date_full":
            # Формат "yy-mm-dd"
            if label and len(label) == 8:
                year, month, day = label.split('-')
                month_name = date_to_months(month)
                formatted.append(f"{day}-{month_name}-{year} г.")
            else:
                formatted.append(str(label))
        else:
            formatted.append(str(label))
    return formatted

def build_svg(values, labels, title):
    """Строит SVG график"""
    
    if not values:
        return create_empty_svg()
    
    width = 720
    height = 420
    x_padding = 50
    y_padding = 30 
    
    max_val = max(values)
    min_val = min(values)

    if max_val == min_val:
        max_val = min_val + 1
    
    value_range = max_val - min_val
    if value_range == 0:
        value_range = 1
    
    points = []
    if len(values) == 1:
        x = x_padding + width // 2
        y = y_padding + height - ((values[0] - min_val) / value_range * height)
        points.append(f"{x},{y}")
    else:
        step = width / (len(values) - 1)
        for i, v in enumerate(values):
            x = x_padding + i * step
            y = y_padding + height - ((v - min_val) / value_range * height)
            points.append(f"{x},{y}")
    
    if points:
        path_d = f"M {' L '.join(points)}"
    else:
        path_d = ""
    
    y_labels = generate_y_labels(min_val, max_val, value_range, y_padding, height)

    svg_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 490" aria-labelledby="title" style="font-family: Open Sans, sans-serif;">
    <title id="title">{title}</title>
    <style>
        .grid {{ stroke: #838383; stroke-width: 1; }}
        .labels {{ font-size: 11px; }}
        .data-line {{ stroke: rgba(0,0,255,0.3); stroke-width: 3; fill: none; }}
        .data-point {{ fill: rgba(0,0,255,1.0); }}
        .y-label {{ text-anchor: end; }}
        text {{ font-size: 11px; }}
    </style>
    
    <!-- Сетка -->
    <line x1="{x_padding}" y1="{y_padding}" x2="{x_padding}" y2="{y_padding + height}" class="grid"/>
    <line x1="{x_padding}" y1="{y_padding + height}" x2="{x_padding + width}" y2="{y_padding + height}" class="grid"/>
    
    <!-- Название графика -->
    <text x="{x_padding + 15}" y="{y_padding - 15}" font-weight="bold" font-size="12">{title}</text>
    
    <!-- Ось Y -->
    {y_labels}
    
    <!-- Данные -->
    <path d="{path_d}" class="data-line"/>
    
    <!-- Подписи оси X -->
    {generate_x_labels(labels, len(values), width, x_padding, y_padding + height, y_padding)}

    <!-- Точки данных -->
    {generate_data_points(points)}
    
    <text x="{x_padding + width - 15}" y="{y_padding + height + 32}" font-weight="bold" font-size="12" text-anchor="end">Время</text>
</svg>'''
    
    return svg_template

def generate_y_labels(min_val, max_val, value_range, y_padding, height):
    """Генерирует подписи для оси Y"""
    y_labels = []
    num_labels = 7
    
    for i in range(num_labels):
        value = max_val - (value_range * i / (num_labels - 1))
        y = y_padding + (height * i / (num_labels - 1))
        
        y_labels.append(f'<line x1="45" y1="{y}" x2="770" y2="{y}" stroke="#ccc" stroke-width="0.7"/>')
        
        y_labels.append(f'<text x="40" y="{y + 4}" class="y-label">{value:.1f}</text>')
    
    return '\n    '.join(y_labels)

def generate_data_points(points):
    """Генерирует SVG элементы для точек данных"""
    points_svg = []
    for point in points:
        x, y = point.split(',')
        points_svg.append(f'<circle cx="{x}" cy="{y}" r="3" class="data-point"/>')
    return '\n    '.join(points_svg)

def generate_x_labels(labels, count, width, x_padding, y_base, y_padding):
    """Генерирует подписи для оси X"""
    if not labels or count == 0:
        return ""
    
    labels_svg = []
    
    if count == 1:
        x = x_padding + width // 2
        labels_svg.append(f'<line x1="{x}" y1="{y_base}" x2="{x}" y2="{y_padding}" stroke="#ccc" stroke-width="0.7"/>')
        labels_svg.append(f'<text x="{x}" y="{y_base + 20}" text-anchor="middle">{labels[0]}</text>')
    else:
        step = width / (count - 1)
        for i, label in enumerate(labels):
            x = x_padding + i * step
            labels_svg.append(f'<line x1="{x}" y1="{y_base}" x2="{x}" y2="{y_padding}" stroke="#ccc" stroke-width="0.7"/>')
            
            if count <= 13 or i % 3 == 0 or i == count - 1:
                labels_svg.append(f'<text x="{x}" y="{y_base + 20}" text-anchor="middle">{label}</text>')
    
    return '\n    '.join(labels_svg)

def create_empty_svg():
    """Создает пустой SVG при отсутствии данных"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 490">
    <text x="400" y="245" text-anchor="middle" font-size="16">Нет данных для отображения</text>
</svg>'''