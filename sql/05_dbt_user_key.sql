-- The public key comes from running make_snowflake_key.py, which prints this
-- statement with the real value filled in.
ALTER USER <your_user> SET RSA_PUBLIC_KEY='<paste the key printed by make_snowflake_key.py>';

DESC USER <your_user>;