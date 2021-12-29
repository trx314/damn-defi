pragma solidity 0.8.7;

// HELPER CONTRACT
contract Encoder {
    function getEncoded(address admin, address proposer, address sweeper) public pure returns (bytes memory) {
       return (abi.encodeWithSignature("initialize(address,address,address)", admin, proposer, sweeper));
    }

}