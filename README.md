**Version 2.0**
This repo contains the challenges from https://www.damnvulnerabledefi.xyz/index.html ported to Python/Brownie.

All challenges have now been ported. Please find more information and challenge details in the link above.

Should just work out the box assuming you have brownie and pytest set up. 

Choose your challenge in the test folder and fill in run_exploit(). All tests should fail in the after() function before an exploit is implemented.

Command to run your test (using test_unstoppable_challenge.py) - 
```
$brownie test tests/test_unstoppable_challenge.py
```

---
## V2 notes
Updated contracts to solc version 0.8, modified config and tests accordingly.
Tests for the new levels will be out over the next few days.

VSCODE CONFIG
If you are using Vs code, you must add this to your setting.json (located in .vscode) if you are using the solc add on, which you most likely are:

```
{
    "solidity.remappings": ["@gnosis/=/users/CHANGE/.brownie/packages/gnosis/safe-contracts@1.3.0",
                            "@openzeppelin=/users/CHANGE/.brownie/packages/OpenZeppelin/openzeppelin-contracts@4.3.3",
                            "@zeppelinupgradeable=/Users/CHANGE/.brownie/packages/OpenZeppelin/openzeppelin-contracts-upgradeable@4.3.2"]
}
```

CHANGE --> add your mac username; if you use windows change as required.

