# GCP expense import

The Admin → Expenses → GCP import screen reads Google Cloud Billing data from
BigQuery and creates one expense per billing account, invoice month, and
currency.

## Prerequisites

1. Enable the **standard** or **detailed** Cloud Billing export to BigQuery.
2. Give the backend runtime identity:
   - `roles/bigquery.jobUser` on the query project.
   - `roles/bigquery.dataViewer` on the billing export dataset.
3. Set the backend environment variable:

   ```text
   GCP_BILLING_EXPORT_TABLE=project_id.dataset_id.gcp_billing_export_v1_XXXXXX_XXXXXX_XXXXXX
   ```

   `GCP_BILLING_QUERY_PROJECT` is optional. When unset, `GOOGLE_CLOUD_PROJECT`
   or `GCP_PROJECT_ID` is used.

Authentication uses Application Default Credentials. The existing
`GOOGLE_SERVICE_ACCOUNT_KEY` fallback is supported for environments that do not
have a workload identity.

## First-time setup

1. Open Admin → Expenses → GCP import.
2. Click **Discover billing accounts**.
3. Map each desired billing account to a vendor, paid-by entry, and category.
4. Save the account and click **Sync all active accounts**.

The sync re-reads the current and previous three invoice months. Stable
provider keys make it safe to run repeatedly.

## Scheduling

Call the following endpoint approximately every six hours:

```text
POST /api/admin/expense-integrations/gcp/cron/sync
X-Cron-Secret: <NUDGE_CRON_SECRET>
```

Example Cloud Scheduler configuration:

```bash
gcloud scheduler jobs create http astroroshni-gcp-expenses-sync \
  --location=asia-south1 \
  --schedule="17 */6 * * *" \
  --uri="https://astroroshni.com/api/admin/expense-integrations/gcp/cron/sync" \
  --http-method=POST \
  --headers="X-Cron-Secret=REDACTED"
```

Use Secret Manager or your deployment automation to supply the header; do not
commit the secret.

## Accounting behavior

- Current/recent invoice months are `provisional`; older months become
  `finalized` seven days after month-end.
- Cost includes Google billing credits and tax/adjustment cost rows present in
  the export.
- Daily project/service lines are retained for audit.
- Editing an imported expense amount records a manual adjustment. Later syncs
  update the provider amount while preserving that adjustment.
- Imported expenses cannot be deleted while managed by the integration.
