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
    pass

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
    
    