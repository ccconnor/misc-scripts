from flask import Flask
from flask_restful import Resource, Api


app = Flask(__name__)
api = Api(app)


class GetSeed(Resource):
    def post(self):
        return {
            'succeed': True,
            'seed': '3af29c97ae94a45788c170d052a7d115cd838d51790aa0b68747af1a53b1b241a6d02a502196e6db10ea7cb9d5ffe510bee2a689e915dc8feeb30d3ad1f4cc0c'
        }


api.add_resource(GetSeed, '/seed/get_seed')

if __name__ == '__main__':
    app.run(debug=True)
