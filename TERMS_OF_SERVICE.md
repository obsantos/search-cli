# Terms of Service for search-cli

**Last Updated:** August 20, 2026

Please read these Terms of Service ("Terms") carefully before using `search-cli` ("the application", "the tool", "we", "our").

---

## 1. Acceptance of Terms

By installing, downloading, authenticating, or using `search-cli`, you agree to be bound by these Terms. If you do not agree to these Terms, do not use the application.

---

## 2. Description of the Tool

`search-cli` is an open-source command-line tool that allows users to query Google Search Console APIs, retrieve search performance analytics, view sitemaps, and inspect URL index statuses from their local environment.

The tool executes requests locally on your machine and communicates directly with Google's official API servers using your authenticated Google account or Service Account.

---

## 3. Google API Services Compliance

Your use of `search-cli` is subject to:
1. [Google Terms of Service](https://policies.google.com/terms)
2. [Google API Terms of Service](https://developers.google.com/terms)
3. [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy)

You agree that you will only use `search-cli` with Google Search Console properties that you own or have explicit authorization to access.

---

## 4. User Responsibilities & Security

* **Credential Management:** You are solely responsible for securing your local machine, OAuth client secrets, access tokens (`~/.config/search-cli/token.json`), and Service Account key files.
* **Lawful Use:** You agree not to use the application to violate applicable laws, breach third-party rights, or attempt to circumvent Google API rate limits and quotas.

---

## 5. Disclaimer of Warranties

`search-cli` is provided **"AS IS"** and **"AS AVAILABLE"**, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement.

We do not guarantee that the tool will be uninterrupted, error-free, or compatible with future Google API changes or deprecations.

---

## 6. Limitation of Liability

To the maximum extent permitted by applicable law, in no event shall the authors, maintainers, or contributors of `search-cli` be liable for any direct, indirect, incidental, special, consequential, or punitive damages arising from:
* The use or inability to use the tool.
* Any unauthorized access to or alteration of your Google account data.
* Google API rate limit exhaustion, account suspension, or service downtime.

---

## 7. Termination & Revocation

You may terminate these Terms at any time by discontinuing use of the application and removing stored tokens:
1. Run `search-cli auth logout` on your machine.
2. Revoke `search-cli` access in your [Google Account Permissions](https://myaccount.google.com/permissions).

---

## 8. Open Source License

`search-cli` is distributed under the **MIT License**. The full text of the license is available in the repository.

---

## 9. Changes to These Terms

We reserve the right to modify these Terms at any time. Any changes will be posted to the project repository with an updated "Last Updated" date.

---

## 10. Contact

For questions or issues regarding these Terms, please open an issue on the GitHub repository:  
[https://github.com/obsantos/search-cli/issues](https://github.com/obsantos/search-cli/issues)
