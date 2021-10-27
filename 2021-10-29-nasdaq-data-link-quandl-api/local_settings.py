polygon = {
    'api_key':'YOUR_API_KEY'
}

postgresql = {'pguser':'alpha',
              'pgpasswd':'password',
              'pghost':'localhost',
              'pgport': 5432,
              'pgdb': 'alpha'
             }

quandl = {
    'api_key': 'YOUR_API_KEY',
    'number_of_retries': 5,
    'max_wait_between_retries': 8,
    'retry_backoff_factor': 1,
    'retry_status_codes': [429, 500, 501, 502, 503,
                           504, 505, 506, 507, 508,
                           509, 510, 511]
}

