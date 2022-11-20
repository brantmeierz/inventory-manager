import os
import flask
from flask import request, Response
from datetime import datetime
import pymongo
import uuid

mongodb_host = os.environ.get("MONGODB_HOST", "localhost")
mongodb_port = int(os.environ.get("MONGODB_PORT", "27017"))

flask_host = os.environ.get("FLASK_HOST", "0.0.0.0")
flask_port = int(os.environ.get("FLASK_PORT", "5000"))

mongo_client = pymongo.MongoClient(mongodb_host, mongodb_port)
mongo_db = mongo_client.get_database('inventory')
type_col = mongo_db.get_collection('types')
item_col = mongo_db.get_collection('items')

length_units = ["mm", "cm", "m", "in", "ft", "yd"]
volume_units = ["L", "gal", "qt", "cup", "tbsp", "tsp"]
weight_units = ["g", "kg", "lb", "oz"]

app = flask.Flask(__name__)

def new_uuid():
    return str(uuid.uuid4())

@app.route("/", method=["GET"])
def index():
    return "Hello World!"

#
# ITEM
#

@app.route("/item", method=["POST"])
def post_item():
    json_body = request.get_json()

    if not "measure" in json_body:
        return Response(status=400, response="Missing 'measure'")

    measure = json_body["measure"]
    if not "type" in measure:
        return Response(status=400, response="Missing 'measure.type'")
    measure_type = measure["type"]
    if measure_type not in ["quantity", "length", "volume", "weight"]:
        return Response(status=400, response="Invalid 'measure.type'")
    if not "value" in measure:
        return Response(status=400, response="Missing 'measure.value'")
    measure_value = measure["value"]
    measure_unit = measure["unit"] if "unit" in measure else None
    if measure != "quantity" and measure_unit is None:
        return Response(status=400, response="Missing 'measure.unit'")
    if measure_type == "length":
        if measure_unit not in length_units:
            return Response(status=400, response="Invalid 'measure.unit'")
    elif measure_type == "volume":
        if measure_unit not in volume_units:
            return Response(status=400, response="Invalid 'measure.unit'")
    elif measure_type == "weight":
        if measure_unit not in weight_units:
            return Response(status=400, response="Invalid 'measure.unit'")

    new_item = {
        "uuid": new_uuid(),
        "name": json_body["name"],
        "description": json_body["description"],
        "measure": {
            "type": measure_type,
            "value": measure_value,
            "unit": measure_unit
        },
        "tags": json_body["tags"],
        "created": str(datetime.utcnow()),
        "last_audit": str(datetime.utcnow()),
        "expiration_date": json_body["expiration_date"]
    }
    item_col.insert_one(new_item)
    return Response(status=200, response="{\"uuid\": uuid}")

@app.route("/item/<uuid>", method=["GET"])
def get_one_item(uuid):
    result = item_col.find_one({"uuid": uuid})
    if result is None:
        return Response(status=404)
    return Response(status=200, response=result)

#
# TYPE
#

if __name__ == "__main__":
    app.run(host=flask_host, port=flask_port, debug=True)