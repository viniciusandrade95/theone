# main.py / app.py / server.py

from core.config import load_config

def bootstrap():
    load_config()        # ← AQUI
    start_http_server()  # framework / router / etc

# bootstrap()

# main.py

from core.config import load_config

def main():
    load_config()
    print("Application started successfully")

if __name__ == "__main__":
    main()

