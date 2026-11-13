from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SERVICES = {
    "catalog": "http://127.0.0.1:8001",
    "rooms": "http://127.0.0.1:8002"
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        return JSONResponse(status_code=404, content={"error": "Service not found"})
        
    target_url = f"{SERVICES[service]}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    try:
        async with httpx.AsyncClient() as client:
            body = await request.body()
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                content=body,
                timeout=10.0  # Добавили таймаут
            )
            
        # Безопасный возврат (не падаем, если пришел не JSON)
        try:
            content = response.json()
        except:
            content = {"detail": response.text}
            
        return JSONResponse(status_code=response.status_code, content=content)
        
    except Exception as e:
        print(f"Ошибка шлюза: {e}")
        return JSONResponse(status_code=500, content={"error": f"Gateway error: {str(e)}"})