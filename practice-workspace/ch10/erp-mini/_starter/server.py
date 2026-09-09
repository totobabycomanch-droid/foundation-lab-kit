from fastapi import FastAPI


app = FastAPI(title="Chapter 10 ERP Mini")


@app.get("/health")
def health():
    return {"status": "ok"}

