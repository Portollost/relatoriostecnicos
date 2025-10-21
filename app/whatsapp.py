# app/whatsapp.py ou mesmo whatsapp.py na raiz

import os

def get_headers():
    token = os.environ.get("WHATSAPP_TOKEN", "EAG0T5mPOlhcBPisAgdSBkKqm72XgZBnr9v3eK6ox88leBoVW4v3fRFaGkhZCp8AF2sZBBjjLfrhfYW0r9umFSzA3fE8ByziCirIZAcjKnAZBQ4LsQS670z3twxxhsQ15NuNEjhSmpLVtZA7WSSSZAMX7mxVycF9Cwmy39lxCy8Nwc7mHaGCUKFLtUN4p0BoQsFcIQZDZD")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def get_number_id():
    return os.environ.get("WHATSAPP_NUMBER_ID", "795215293676591")
