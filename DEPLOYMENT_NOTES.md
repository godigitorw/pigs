# Deployment Notes

## Recent Changes Requiring Migration

### Bank Module (Added: 2025-10-10)

New database tables have been added for the Bank/Finance module:
- `BankAccount` - Stores bank account information
- `BankTransaction` - Tracks deposits and withdrawals

**Required Action on Railway:**

After pulling the latest code, you MUST run migrations:

```bash
python manage.py migrate
```

Or if Railway doesn't auto-run migrations, you may need to:

1. Go to Railway dashboard
2. Open your project
3. Go to the service settings
4. Add or update the build command to include:
   ```
   python manage.py migrate && python manage.py collectstatic --no-input
   ```

### Migration File
- `farm/migrations/0025_bankaccount_banktransaction.py`

### New URLs Available
- `/farm/bank/accounts/` - Bank accounts list
- `/farm/bank/transactions/` - Transactions list
- `/farm/bank/accounts/add/` - Add bank account
- `/farm/bank/transactions/add/` - Add transaction

## Troubleshooting

### 500 Error on Bank Pages

If you get a 500 error when accessing bank pages:

1. **Check if migrations have run:**
   ```bash
   python manage.py showmigrations farm
   ```

   Look for:
   ```
   [X] 0025_bankaccount_banktransaction
   ```

2. **If migration is not applied:**
   ```bash
   python manage.py migrate farm
   ```

3. **Check database tables exist:**
   ```bash
   python manage.py dbshell
   .tables  # (for SQLite)
   # Look for: farm_bankaccount, farm_banktransaction
   ```

### Fresh Deployment

For a fresh deployment:
```bash
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py createsuperuser  # if needed
```

## Environment Variables

Ensure these are set in Railway:
- `DJANGO_SETTINGS_MODULE=pigfarm.settings`
- `DATABASE_URL` (if using PostgreSQL)
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS` (should include your Railway domain)
