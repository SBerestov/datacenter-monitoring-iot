from flask import Blueprint, jsonify
from db.connection import fetch_all

tables_bp = Blueprint("tables", __name__)


@tables_bp.route("/devices/table-view")
def table_view():
    query = """
        SELECT t1.*, t3.location_description
        FROM data_sources t1
        INNER JOIN (
            SELECT data_source_name, MAX(datetime) AS max_datetime
            FROM data_sources
            GROUP BY data_source_name
        ) t2 ON t1.data_source_name = t2.data_source_name
           AND t1.datetime = t2.max_datetime
        LEFT JOIN data_source_map t3 ON t1.data_source_name = t3.source_id
        ORDER BY t1.datetime, t1.properties_id;
    """

    data = fetch_all(query)
    return jsonify(data)