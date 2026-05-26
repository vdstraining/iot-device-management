from fastapi import FastAPI
from backend.src.routes.firmwareSchedules import router as firmware_router
from backend.src.services.scheduler import SchedulerService

app = FastAPI()
app.include_router(firmware_router, prefix="/api/firmware")

scheduler = SchedulerService()

@app.on_event("startup")
async def startup():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    await scheduler.stop()
