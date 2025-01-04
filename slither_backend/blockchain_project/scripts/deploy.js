const hre = require("hardhat");

async function main() {
    // Get the contract factory
    const HelloWorld = await hre.ethers.getContractFactory("HelloWorld");

    console.log("Deploying the contract...");
    
    // Deploy the contract
    const helloWorld = await HelloWorld.deploy();

    console.log("Waiting for the contract to be mined...");
    
    // Log the deployed contract's address
    console.log("HelloWorld deployed to:", helloWorld.address);
}

// Catch errors and log them
main().catch((error) => {
    console.error("Error deploying the contract:", error);
    process.exitCode = 1;
});
