# Copy this file to env.sh, fill in the values, then run: source env.sh
# env.sh is in .gitignore, so your secrets never get committed.

# Django
export DJANGO_SECRET_KEY='change-me'
export DEBUG='True'

# Database (Supabase -> Project Settings -> Database -> Connection string -> Session pooler)
# Leave empty to use local SQLite.
export DATABASE_URL='postgresql://postgres.vnlsttiwtftazwtfvibs:[YOUR-PASSWORD]@aws-1-eu-west-3.pooler.supabase.com:5432/postgres'

# AI (free key from https://console.groq.com/keys)
export GROQ_API_KEY=''
