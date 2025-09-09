import os
from web3 import Web3

RPC = os.getenv("PRVX_RPC_URL")
TOKEN = os.getenv("PRVX_TOKEN_ADDRESS")
THRESHOLD_WEI = int(os.getenv("PRVX_QOS_THRESHOLD_WEI","1000000000000000000000"))
ERC20_ABI = [{
  "constant": True,
  "inputs":[{"name":"_owner","type":"address"}],
  "name":"balanceOf",
  "outputs":[{"name":"balance","type":"uint256"}],
  "type":"function"
}]

_w3 = Web3(Web3.HTTPProvider(RPC)) if RPC else None
_contract = _w3.eth.contract(address=Web3.to_checksum_address(TOKEN), abi=ERC20_ABI) if (_w3 and TOKEN) else None

def get_balance(address: str) -> int:
    if not _contract:
        raise RuntimeError("PRVX RPC or token not configured")
    return int(_contract.functions.balanceOf(Web3.to_checksum_address(address)).call())

def is_eligible(address: str, threshold_wei: int | None = None) -> tuple[bool, int]:
    thr = THRESHOLD_WEI if threshold_wei is None else int(threshold_wei)
    bal = get_balance(address)
    return (bal >= thr, bal)
