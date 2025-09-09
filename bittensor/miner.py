import os, asyncio, signal, sys
from loguru import logger as log
import httpx

# ----- Config
GATEWAY = os.getenv("PX_GATEWAY_URL", "http://localhost:8080")
SCHEDULER = os.getenv("PX_SCHEDULER_URL", "http://localhost:9090")
API_KEY = os.getenv("PX_API_KEY", "dev_key_123")
PRVX_ADDR = os.getenv("PX_PRVX_ADDRESS", "")
# Mode SHIM (par défaut) : pas de binding à Bittensor
USE_BITTENSOR = os.getenv("USE_BITTENSOR", "0") in ("1","true","TRUE","yes","on")

# ----- Helpers
async def infer_image_from_url(url: str, vip: bool=False) -> dict:
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    if vip and PRVX_ADDR:
        headers["x-prvx-address"] = PRVX_ADDR
    async with httpx.AsyncClient(timeout=30.0) as cx:
        r = await cx.post(f"{GATEWAY}/v1/detect/image", headers=headers, json={"source_url": url})
        r.raise_for_status()
        return r.json()

async def _demo_loop():
    # Démo simple : boucle d'inférence périodique (SHIM)
    img = "https://picsum.photos/seed/px-miner-demo/512.jpg"
    while True:
        try:
            res = await infer_image_from_url(img, vip=bool(PRVX_ADDR))
            log.info(f"[MINER SHIM] result={res}")
        except Exception as e:
            log.error(f"shim infer error: {e}")
        await asyncio.sleep(5.0)

def _setup_signals(loop: asyncio.AbstractEventLoop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, loop.stop)
        except NotImplementedError:
            pass

async def main():
    log.info(f"Miner starting | GATEWAY={GATEWAY} | VIP={'yes' if PRVX_ADDR else 'no'} | SHIM={'on' if not USE_BITTENSOR else 'off'}")
    if not USE_BITTENSOR:
        await _demo_loop()
    else:
        # Esquisse du mode Bittensor (désactivé par défaut)
        try:
            import bittensor as bt  # noqa: F401
            log.info("Bittensor detected, but binding not configured in this MVP script.")
            while True:
                await asyncio.sleep(60)
        except Exception as e:
            log.error(f"Bittensor import failed: {e}. Falling back to SHIM loop.")
            await _demo_loop()

if __name__ == "__main__":
    if sys.platform != "win32":
        try:
            import uvloop  # type: ignore
            uvloop.install()
        except Exception as _e:
            pass  # uvloop optionnel
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _setup_signals(loop)
    loop.run_until_complete(main())

