# Privacy Policy for search-cli

**Last Updated:** August 20, 2026

`search-cli` ("we", "our", or "the application") is an open-source command-line interface tool designed to interact with Google Search Console APIs directly from the user's local environment.

This Privacy Policy explains how `search-cli` accesses, uses, stores, and protects your information when you authenticate with Google services.

---

## 1. Information Accessed and Collected

When you authenticate `search-cli` with your Google account, the application requests access to the following Google API scopes:

* **`https://www.googleapis.com/auth/webmasters.readonly`** (View Search Console data for your verified sites)
* **`https://www.googleapis.com/auth/webmasters`** (Manage Search Console properties and sitemaps)

Through these permissions, the application accesses:
* List of verified Search Console sites and properties.
* Search Analytics metrics (clicks, impressions, CTR, average ranking position, search queries, landing page URLs, country, device, and date dimensions).
* Sitemap index and submission status.
* URL inspection status (indexing and crawl states).

---

## 2. How Your Information Is Used

`search-cli` uses the accessed data exclusively to execute the commands you run in your terminal (such as querying search performance, listing sites, inspecting URLs, or exporting reports).

**The application does NOT:**
* Transfer, upload, or sync your data to any external server or cloud service.
* Store your analytics data in any remote database.
* Sell, rent, lease, or monetize your personal or analytics information.
* Use your Google user data for advertising, tracking, or training AI models.

All API requests are sent directly between your local machine and Google's official API servers (`https://www.googleapis.com`).

---

## 3. Local Storage of Credentials

* **OAuth Tokens:** When you authenticate via OAuth 2.0, your OAuth access token and refresh token are saved **strictly locally** on your machine in:
  `~/.config/search-cli/token.json` (or your OS equivalent `$XDG_CONFIG_HOME/search-cli/token.json`).
* **Service Account Keys:** If you use a Google Cloud Service Account, the JSON key file remains on your local file system and is never transmitted anywhere other than Google's authentication endpoints.
* **Configuration:** Local preference files (`~/.config/search-cli/config.json`) store only local CLI defaults (e.g., default site URL).

---

## 4. Google API Services User Data Policy Compliance

`search-cli` complies with the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the **Limited Use** requirements.

> **Limited Use Disclosure:**  
> `search-cli`'s use and transfer to any other app of information received from Google APIs will adhere to the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements.

---

## 5. Revocation and Data Deletion

You can revoke `search-cli`'s access and delete all stored tokens at any time:

1. **Via CLI:** Run `search-cli auth logout` to immediately delete local tokens and configurations from your machine.
2. **Via Google Account:** Remove `search-cli` access directly in your [Google Account Permissions](https://myaccount.google.com/permissions).

---

## 6. Open Source Transparency

`search-cli` is open-source software. You can inspect the source code and verify our network calls and credential handling at:
[https://github.com/obsantos/search-cli](https://github.com/obsantos/search-cli)

---

## 7. Contact and Inquiries

If you have any questions or concerns regarding this Privacy Policy, please open an issue on GitHub:
[https://github.com/obsantos/search-cli/issues](https://github.com/obsantos/search-cli/issues)
