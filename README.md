# lastcoffee

巴哈耳機普查表單專案。

## Run

本機預覽與 F5 啟動都使用 Streamlit 主線：

```powershell
python -m streamlit run streamlit_app.py
```

啟動後開啟：

```text
http://localhost:8501
```

## Supabase

1. 在 Supabase SQL Editor 執行 `supabase/schema.sql`。
2. 在 Streamlit Cloud Secrets 貼上：

```toml
SUPABASE_URL = "你的 Supabase Project URL"
SUPABASE_SERVICE_ROLE_KEY = "你的 Supabase service_role key"
GOOGLE_API_KEY = "你的 Google API key"
```

若沒有設定 Supabase secrets，程式會退回本機 `data/census.json`。
