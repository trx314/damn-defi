from pathlib import Path
from brownie import ZERO_ADDRESS, accounts, WalletRegistry, DamnValuableToken, project, Wei
import eth_account


def test_backdoor():
    before()
    exploit()
    after()
    
    
def before():
    DEPLOYER = accounts[-1]
    new_account = eth_account.Account().create()
    global attacker_key
    attacker_key = new_account.privateKey.hex()
    print(f"attacker address: {new_account.address}, private key: {attacker_key}")
    global ATTACKER
    # Creating new account,you can access the priv key of this account
    # using the ATTACKER object if you need to (hint: not necessary to solve)
    ATTACKER = accounts.add(attacker_key)
    new_account = accounts.add()
     
    
    
    global wallet_users
    wallet_users = [accounts[0], accounts[1], accounts[2], accounts[3]]
    gnosis_package_path = Path(Path.home()/ ".brownie" /"packages"/"curiousdweller"/"safe-contracts@1.3.0")
    # Load the gnosis contracts for use
    global Gnosis
    Gnosis = project.load(gnosis_package_path)
    global GnosisSafe
    GnosisSafe = Gnosis.GnosisSafe
    global GnosisSafeProxyFactory
    GnosisSafeProxyFactory = Gnosis.GnosisSafeProxyFactory
    # Deploy Gnosis contracts
    gnosis_safe = GnosisSafe.deploy({"from": DEPLOYER})
    gnosis_safe_proxy_factory = GnosisSafeProxyFactory.deploy({"from": DEPLOYER})
    
    dv_token = DamnValuableToken.deploy({"from": DEPLOYER})
    wallet_registry = WalletRegistry.deploy(gnosis_safe.address,
                                            gnosis_safe_proxy_factory.address,
                                            dv_token.address,
                                            wallet_users,
                                            {"from": DEPLOYER})
    for i in wallet_users:
        assert wallet_registry.beneficiaries(i.address) == True
    dv_token.transfer(wallet_registry.address, Wei("40 ether"), {"from": DEPLOYER})
    assert dv_token.balanceOf(wallet_registry.address) == Wei("40 ether")
    
    
    
def exploit():
    pass

def after():
    assert DamnValuableToken[-1].balanceOf(ATTACKER) >= Wei("39 ether")
    