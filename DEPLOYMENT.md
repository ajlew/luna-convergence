# Deploy the Customer MVP

## 1. Test locally

On Windows, double-click:

```text
run_customer_windows.bat
```

The customer site opens in your browser.

For the full local admin/fulfilment console, double-click:

```text
run_admin_windows.bat
```

## 2. Create the two Stripe products

Create two Stripe Payment Links:

- Monthly Strategic Report — A$9.95
- Year-Ahead Strategic Report — A$29.95

Copy the URLs.

## 3. Configure secrets locally

Create:

```text
.streamlit/secrets.toml
```

Copy the structure from:

```text
.streamlit/secrets.toml.example
```

Insert the real payment links and contact email.

Do not publish the live `secrets.toml` file.

## 4. Deploy through GitHub and Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload the contents of the `convergence_astrology` folder.
3. In Streamlit Community Cloud, choose **Create app**.
4. Select the repository and set the main file to `app.py`.
5. Add the secret values through the app's settings.
6. Deploy.

## 5. First validation phase

Keep fulfilment manual:

1. Customer pays.
2. Customer submits report details.
3. Open the local admin console.
4. Generate the monthly or yearly report.
5. Review it.
6. Send it by email.

Automate delivery only after paid demand is established.
