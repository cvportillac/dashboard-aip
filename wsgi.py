from app import app
server = app.server

if __name__ == "__main__":
    server.run(host='0.0.0.0', port=10000)
