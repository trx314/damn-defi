from brownie import (accounts,
                     DamnValuableNFT,
                     DamnValuableToken,
                     FreeRiderBuyer,
                     FreeRiderNFTMarketplace,
                     WETH9,
                     UniswapV2Router02,
                     UniswapV2Factory,
                     Wei,
                     chain,
                     Contract,
                     )
import time
import json



NFT_BUY_PRICE = Wei("15 ether")
UNISWAP_INITIAL_TOKEN_RESERVE = Wei("15000 ether")
    

def test_free_rider():
    before()
    exploit()
    after()

    
def before():
    global ATTACKER
    ATTACKER = accounts[3]
    global uni_factory
    uni_factory = UniswapV2Factory.deploy(accounts[0].address, {"from": accounts[0]})
    fee_to = uni_factory.feeToSetter()
    global weth
    weth = WETH9.deploy({"from": accounts[0]})
    uni_router = UniswapV2Router02.deploy(uni_factory.address, weth.address,
                                          {'from': accounts[0]})
    global dv_token
    dv_token = DamnValuableToken.deploy({"from": accounts[0]})
    dv_token.approve(uni_router.address, UNISWAP_INITIAL_TOKEN_RESERVE,
                     {"from": accounts[0]})
    uni_allowance_check = dv_token.allowance(accounts[0].address, uni_router.address)
    assert uni_allowance_check == UNISWAP_INITIAL_TOKEN_RESERVE
    deadline = chain.time() * 2
    uni_factory.setFeeTo(accounts[1].address,
                         {"from": accounts[0]})
    tx = uni_router.addLiquidityETH(dv_token.address, UNISWAP_INITIAL_TOKEN_RESERVE,
                               0,
                               0,
                               accounts[0].address,
                               deadline,
                               {"from": accounts[0],
                               "amount": Wei("9000 ether")})
    tx.wait(1)
    global nft_marketplace
    nft_marketplace = FreeRiderNFTMarketplace.deploy(6, {"from": accounts[0]})
    dvnft_address = nft_marketplace.token()
    global dv_nft
    dv_nft = DamnValuableNFT.at(dvnft_address)
    dv_nft.setApprovalForAll(nft_marketplace.address, True,
                             {"from": accounts[0]})
    nft_marketplace.offerMany([0,1,2,3,4,5], [NFT_BUY_PRICE for i in range(6)], {"from":accounts[0]})
    assert nft_marketplace.amountOfOffers() == 6
    FreeRiderBuyer.deploy(ATTACKER.address, dvnft_address,
                          {"amount": Wei("45 ether"),
                           "from": accounts[0]})
    

def exploit():
    pass
    
    
def after():
    assert FreeRiderBuyer[-1].balance() == 0
    
      
def get_pair(address):
    # Change path if on windows
    with open("build/contracts/UniswapV2Pair.json") as V2_pair:
        data = json.load(V2_pair)
        abi = data["abi"]
        v2_Pair = Contract.from_abi("UniswapV2Pair",address=address, abi=abi)
        return v2_Pair
        
    
    