from flask import Blueprint, request, jsonify
from services.svg_generator import generate_svg

charts_bp = Blueprint("charts", __name__)


@charts_bp.route("/data-property", methods=["GET"])
def data_property():
    type_id = request.args.get("type_id")
    property_id = request.args.get("property_id")
    source = request.args.get("source")
    datetime_value = request.args.get("request")

    if not all([type_id, property_id, source]):
        return jsonify({"error": "Missing parameters"}), 400

    generate_svg(
        type_id=int(type_id),
        property_id=int(property_id),
        source_name=source,
        datetime_value=datetime_value
    )

    return jsonify({"success": True, "message": "SVG generated"})