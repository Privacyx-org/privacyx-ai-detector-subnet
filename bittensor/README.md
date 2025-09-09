# PrivacyX Subnet — Bittensor bridge (SHIM + ready-for-Bittensor)

Ce dossier fournit :
- `miner.py` : proxy mineur — en SHIM, il envoie des jobs via le Gateway / Scheduler déjà en place.
- `validator.py` : proxy validateur — en SHIM, il évalue des panels de probas via le service /assess.

## Lancement local (SHIM)
Pré-requis: docker-compose avec gateway/scheduler/validator/miner déjà lancé.

export PX_GATEWAY_URL=http://localhost:8080
export PX_SCHEDULER_URL=http://localhost:9090
export PX_VALIDATOR_URL=http://localhost:7070
export PX_API_KEY=dev_key_123
# option VIP
export PX_PRVX_ADDRESS=0xfbe27f21157a60184fe223d2c8e54ea2032a8189

pip3 install -r bittensor/requirements.txt
python3 bittensor/miner.py
# (dans un autre terminal)
# python3 bittensor/validator.py
