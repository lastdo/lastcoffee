$ErrorActionPreference = "Stop"

$Port = 8501

$connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
  Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
}

python -m streamlit run streamlit_app.py --server.port $Port --server.headless false
