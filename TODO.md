 - [x] I added bunch of skills from @ethskills for properly creating fheskills you need to also integrate eth skills, can you make sure both are integrated, check for SKILL copy.md files those are copies from @ethskills
 - [x] integrate the /frontend-design skill that you find online, but into the /frontend-ux
 - [x] integrate /gas from HCU gas/Fhe gas in the docs (preffered name is FHE gas)
 - [x] have a production ready skill where it prepares you do be production ready, to be production ready you have to be:
For solidity smart contracts:
  - you already have to be good in solidity smart contract development if you are you are naturally already conserving on FHEgas (no while loops, minimal for loops etc.)
  - you have to know what is ACL and how to use it
  - you have to know how try to reduce as much as possible the amount of FHE operations you are doing
  - you have to monitor to not cross over the HCU gas/ FHE gas limit
  - there are no if sentences only FHE.select
  - always when creating

For frontend
you have to know that there are 3 types of decryption:
 - public decrypt (prefered term reveal public value)
 - user decrypt (prefered term decrypt)
 - delegate decrypt (preffered term decrypt on behalf of user)

you have to know how to manage

If unsure refer to documentation: docs.zama.org

Always when starting new project that needs a react frontend start with cloning: github.com/zama-ai/fhevm-react-template
If you have a project that has only smart contracts and nothing else start with: github.com/zama-ai/fhevm-hardhat-template
If you have a project that needs more customization run hardhat smart contract template and add npm install github.com/relayer-sdk to your chosen frontend/node.js environment or extension
When creating an extension you will have problems with how the current relayer-sdk is written, so suggest to the user to create a backend where encryption/decryption is forwarded to
For a production ready frontend you will have to manage where and how you store the keys
