import flask


flask_app = flask.Flask(__name__)

@flask_app.route('/items/<articleid>/versions/1', methods=['PUT'])
def items(articleid):
    return flask.Response(flask.request.data, mimetype="application/xml")


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=8090)
