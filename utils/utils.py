import os

import supabase

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

async def get_supabase_client() -> supabase.AsyncClient:
    return await supabase.acreate_client(SUPABASE_URL, SUPABASE_KEY)
