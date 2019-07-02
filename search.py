import flask


flask_app = flask.Flask(__name__)

@flask_app.route('/reindex', methods=['POST'])
def reindex():
    return flask.Response("search reindexed all items")


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=8099)