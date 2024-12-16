socat TCP-LISTEN:1337,reuseaddr,fork exec:"python3 -u ./challenge.py" &
uvicorn ctf_server:anvil_proxy --host 0.0.0.0 --port 28545 