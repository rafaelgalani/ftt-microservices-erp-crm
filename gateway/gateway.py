import json

from nameko.standalone.rpc import ClusterRpcProxy
from nameko.web.handlers import http
from werkzeug.wrappers import Response

from flask import Flask, request, jsonify
from pricing_service import PricingService
app = Flask(__name__)

CONFIG = {'AMQP_URI': "amqp://guest:guest@rabbitmq:5672"}

@app.errorhandler(403)
def unauthorized():
    return jsonify({"statusCode": 403, "description": "Unauthorized."}), 403

@app.errorhandler(404)
def not_found():
    return jsonify({"statusCode": 404, "description": "Resource not found."}), 404

@app.errorhandler(405)
def not_allowed(*args):
    return jsonify({"statusCode": 405, "description": "Invalid method."}), 405


@app.route('/quote/', methods=['POST', 'GET'])
def generate_quote():
    print(request.method)
    try:
        with ClusterRpcProxy(CONFIG) as rpc:
            if request.method == 'POST':
                quote_data = json.loads(request.get_data(as_text=True))

                data = PricingService(quote_data)
                quote_json = json.dumps(data, default=lambda x: x.__dict__)

                quote_id = rpc.quote_service.create(quote_json)
                data.id = quote_id

                response = {
                    "success": True,
                    "data": data,
                }

                return Response(
                    json.dumps(response, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=201
                )    
            else:
                quotes = rpc.quote_service.get_all()
                return Response(
                    json.dumps(quotes, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=200
                )
    except Exception as e:
        return Response(
            json.dumps({
                "error": "Unexpected exception occurred: {}".format(str(e))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )    
    except Exception as e:
        return Response(
            json.dumps({
                "error": "Unexpected exception occurred: {}".format(str(e))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )    

@app.route('/quote/<string:quote_id>', methods=['GET'])
def get_quote(quote_id):
    try:
        with ClusterRpcProxy(CONFIG) as rpc: 
            quote = rpc.quote_service.get(quote_id)
            if quote:
                return Response(
                    json.dumps(quote, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=200
                )
            else:
                return Response(
                    json.dumps({
                        "error": 'Id {} not found.'.format(quote_id),
                    }, default=lambda x: x.__dict__),
                    mimetype='application/json',
                    status=404
                )
    except Exception as e:
        return Response(
            json.dumps({
                "error": "Unexpected exception occurred: {}".format(str(e))
            }, default=lambda x: x.__dict__),
            mimetype='application/json',
            status=500
        )

       
@app.route('/', methods=['GET'])
def get_home():
    return Response(
        json.dumps({"success": True}, default=lambda x: x.__dict__),
        mimetype='application/json',
        status=200
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)