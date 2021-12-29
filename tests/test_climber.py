from brownie import (accounts, 
                     ClimberVault, 
                     ClimberTimelock,
                     Encoder,
                     project,
                     Contract,
                     DamnValuableToken,
                     Wei,
                     )
from pathlib import Path

from brownie.network import contract

def test_climber():
    before()
    exploit()
    after()

def before():
    global ATTACKER
    ATTACKER = accounts[-1]
    DEPLOYER = accounts[0]
    path_to_proxy = Path(Path.home() / ".brownie" / "packages" / "OpenZeppelin" / "openzeppelin-contracts@4.3.3")
    open_zeppelin = project.load(path_to_proxy)
    temporary_vault = ClimberVault.deploy({"from": DEPLOYER})
    Proxy = open_zeppelin.ERC1967Proxy
    encoder = Encoder.deploy({"from": DEPLOYER})
    data = encoder.getEncoded(accounts[1], accounts[2], accounts[3], {"from": DEPLOYER})
    proxy = Proxy.deploy(temporary_vault.address, data, {"from": DEPLOYER})
    global vault
    vault = Contract.from_abi("ClimberVault", proxy.address, ClimberVault.abi)
    global time_lock
    time_lock = ClimberTimelock.at(vault.owner())
    dv_token = DamnValuableToken.deploy({"from": DEPLOYER})
    dv_token.transfer(vault.address , Wei("1000000 ether"), {"from": DEPLOYER})
    assert dv_token.balanceOf(proxy.address) == Wei("1000000 ether")
  
    
def exploit():
    pass

  
def after():
    assert DamnValuableToken[-1].balanceOf(ATTACKER) == Wei("1000000 ether")