from flask import Blueprint, request, jsonify, send_file
from db.connection import fetch_all, execute
import os

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/add-device", methods=["POST"])
def add_device():
    data = request.json

    query = """
        INSERT INTO data_source_map
        (source_id, location_description, location_cor_1, location_cor_2, type_id)
        VALUES (%s, %s, %s, %s, %s)
    """

    execute(query, (
        data["deviceName"],
        data["location"],
        data["cor1"],
        data["cor2"],
        data["imageValue"]
    ))

    return jsonify({"success": True})


@devices_bp.route("/change-device", methods=["POST"])
def change_device():
    data = request.json

    query = """
        UPDATE data_source_map
        SET
            location_description = %s,
            location_cor_1 = %s,
            location_cor_2 = %s,
            type_id = %s
        WHERE source_id = %s
    """

    execute(query, (
        data["location"],
        data["cor1"],
        data["cor2"],
        data["imageValue"],
        data["deviceName"]
    ))

    return jsonify({"success": True})


@devices_bp.route("/get-device-cards", methods=["GET"])
def get_device_cards():
    device_name = request.args.get("device")

    if not device_name:
        return jsonify({"error": "Device parameter is required"}), 400

    query = """
        WITH latest_data AS (
            SELECT 
                t1.data_source_name,
                t1.properties_id,
                t1.value,
                t1.datetime,
                ROW_NUMBER() OVER (PARTITION BY t1.data_source_name, t1.properties_id 
                                ORDER BY t1.datetime DESC) as rn
            FROM data_sources t1
        )
        SELECT DISTINCT
            dsm.source_id,
            dsm.type_id,
            p.properties_id,
            p.property_name_rus,
            p.min_range,
            p.max_range,
            ld.value
        FROM data_source_map dsm
        LEFT JOIN properties p ON dsm.type_id = p.type_id
        LEFT JOIN latest_data ld ON dsm.source_id = ld.data_source_name 
            AND p.properties_id = ld.properties_id
            AND ld.rn = 1
        WHERE dsm.source_id = %s
        ORDER BY p.properties_id;
    """

    data = fetch_all(query, (device_name,))
    return jsonify(data)

@devices_bp.route("/get-data-to-fill-fields", methods=["POST"])
def get_data_to_fill_fields():
    device_name = request.json
    
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400
    
    query = "SELECT * FROM data_source_map WHERE source_id = %s"
    data = fetch_all(query, (device_name,))
    
    if data:
        return jsonify(data[0])
    return jsonify({}), 404

@devices_bp.route("/delete-device", methods=["POST"])
def delete_device():
    device_name = request.json
    
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400
    
    query = "DELETE FROM data_source_map WHERE source_id = %s"
    execute(query, (device_name,))
    
    return jsonify({"success": True})

@devices_bp.route("/devices/update-cards-data/<device_name>", methods=["GET"])
def update_cards_data(device_name):
    query = """
        SELECT
            dm.source_id,
            dm.location_description,
            dm.location_cor_1,
            dm.location_cor_2,
            pr.property_name,
            pr.min_range,
            pr.max_range,
            pr.properties_id,
            pr.column_id,
            pr.property_name_rus,
            pr.type_id,
            ds.value,
            ds.datetime
        FROM data_source_map dm
        LEFT JOIN properties pr ON (dm.type_id = pr.type_id)
        LEFT JOIN (
            SELECT
                t1.data_source_name,
                t1.properties_id,
                t1.value,
                t1.datetime,
                t1.type_id,
                ROW_NUMBER() OVER (
                    PARTITION BY t1.data_source_name, t1.properties_id 
                    ORDER BY t1.datetime DESC
                ) as rn
            FROM monitoring_db.data_sources t1
        ) ds ON (dm.source_id = ds.data_source_name 
                AND pr.properties_id = ds.properties_id 
                AND ds.rn = 1)
        WHERE dm.type_id IN (1, 2, 3, 4)
            AND dm.source_id = %s
        ORDER BY dm.id, pr.properties_id ASC;
    """
    
    data = fetch_all(query, (device_name,))
    return jsonify(data)

@devices_bp.route("/devices/get-reference-table/<pattern>", methods=["GET"])
def get_reference_table(pattern):
    pattern = pattern.replace('*', '')
    
    query = "SELECT * FROM monitoring_db.data_source_map WHERE source_id LIKE %s"
    data = fetch_all(query, (f"%{pattern}%",))
    
    return jsonify(data)

@devices_bp.route("/devices/get-location-source", methods=["GET"])
def get_location_source():
    query = """
        SELECT
            dm.id,
            dm.source_id,
            dm.location_description,
            dm.location_cor_1,
            dm.location_cor_2,
            pr.property_name,
            pr.min_range,
            pr.max_range,
            pr.properties_id,
            pr.column_id,
            pr.property_name_rus,
            ds.type_id,
            GROUP_CONCAT(DISTINCT CAST(ds.value AS CHAR) SEPARATOR '') AS value,
            ds.datetime
        FROM data_source_map dm
        LEFT JOIN properties pr ON (dm.type_id = pr.type_id)
        LEFT JOIN (
            SELECT
                t1.data_source_name,
                t1.type_id,
                t1.properties_id,
                t1.value,
                t1.datetime
            FROM monitoring_db.data_sources t1
            INNER JOIN (
                SELECT
                    data_source_name,
                    MAX(datetime) AS max_datetime
                FROM monitoring_db.data_sources
                GROUP BY data_source_name
            ) t2 ON t1.data_source_name = t2.data_source_name
                AND t1.datetime = t2.max_datetime
        ) ds ON (dm.source_id = ds.data_source_name AND pr.properties_id = ds.properties_id)
        WHERE dm.type_id IN (1, 2, 3, 4)
        GROUP BY dm.id,
            dm.source_id,
            dm.location_description,
            dm.location_cor_1,
            dm.location_cor_2,
            pr.property_name,
            pr.min_range,
            pr.max_range,
            pr.properties_id,
            pr.column_id,
            pr.property_name_rus,
            ds.type_id,
            ds.datetime
        ORDER BY id,
            source_id,
            location_description,
            property_name ASC
    """
    
    data = fetch_all(query)
    return jsonify(data)

@devices_bp.route("/get-range-source", methods=["GET"])
def get_range_source():
    return get_location_source()

@devices_bp.route("/images/doc8.svg", methods=["GET"])
def get_svg_image():
    """Возвращает сгенерированный SVG файл"""
    svg_path = "static/images/doc8.svg"
    if os.path.exists(svg_path):
        return send_file(svg_path, mimetype='image/svg+xml')
    return jsonify({"error": "SVG not found"}), 404