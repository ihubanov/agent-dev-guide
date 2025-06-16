# Packaging and Publishing Your Agent

Follow this step-by-step guide to package and upload your agent.

---

## 1. Package Your Agent

1. Open your agent folder.
   *(Example: `agent-dev-guide/examples/personal-agent/pack.sh`)*

2. Run the packaging script in your terminal:

   ```bash
   bash pack.sh
   ```

3. After the script finishes, a file named `package.zip` will be created in the folder.

---

## 2. Upload Your Agent

1. Visit: [https://staging.eternalai.org/for-developers/create](https://staging.eternalai.org/for-developers/create)
2. Click **“Connect wallet”**.
3. Choose **MetaMask** and connect your wallet.
4. After connecting, select **CryptoAgent NFT**.
5. Fill out the required information:

   * **Display name**
   * **Source code** (upload the `package.zip` file)
6. Click **“Create”** to publish your agent.

---

## 3. Get Test Tokens (for Gas Fees)

1. Go to: [https://www.alchemy.com/faucets/base-sepolia](https://www.alchemy.com/faucets/base-sepolia)
2. Follow the instructions to receive test tokens for the Base Sepolia network.

---

## Bonus Tips

* Manage your agents at: [eternalai.org/your-agents](https://eternalai.org/your-agents)
* Show or hide your agent anytime
* Update the code whenever needed
* Edit your agent’s info at any time
