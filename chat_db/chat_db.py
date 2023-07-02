# Start server: python -m uvicorn chat_db:app --host 127.0.0.1 --port 8000 --reload
from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient
from routes import router as chat_router

config_params = dotenv_values("chat_db.env")
print(config_params["ATLAS_URI"])

app = FastAPI()

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(config_params["ATLAS_URI"],
                     tls=True,
                     tlsCertificateKeyFile='X509-cert-7039415990340640417.pem')

    app.database = app.mongodb_client[config_params["DB_NAME"]]
    print("Connected to the MongoDB database!")

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()

app.include_router(chat_router, tags=["chats"], prefix="/chat")