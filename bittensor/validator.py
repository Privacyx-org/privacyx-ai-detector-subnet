import os, asyncio, signal, sys, random
from typing import List
from loguru import logger as log
import httpx

VALIDATOR = os.getenv("PX_VALIDATOR_URL", "http://localhost:7070")
USE_BITTENSOR = os.getenv("USE_BITTENSOR", "0") in ("1","true","TRUE","yes","on")

async def assess(probs: List[float]) -> dict:
    payload = {
        "probs": probs,
        "latencies_ms": [random.randint(40,160) for _ in probs],
        "z_threshold": 2.0,
        "trim_ratio": 0.2
    }
    async with httpx.AsyncClient(timeout=10.0) as cx:
        r = await cx.post(f"{VALIDATOR}/assess", json=payload)
        r.raise_for_status()
        return r.json()

async def _demo_loop():
    while True:
        try:
            sims = [random.uniform(0.1,0.9) for _ in range(5)]
            res = await assess(sims)
            log.info(f"[VALIDATOR SHIM] in={sims}  out={res}")
        except Exception as e:
            log.error(f"validator shim error: {e}")
        await asyncio.sleep(6.0)

def _setup_signals(loop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, loop.stop)
        except NotImplementedError:
            pass

async def main():
    log.info(f"Validator starting | target={VALIDATOR} | SHIM={'on' if not USE_BITTENSOR else 'off'}")
    if not USE_BITTENSOR:
        await _demo_loop()
    else:
        try:
            import bittensor as bt  # noqa
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

