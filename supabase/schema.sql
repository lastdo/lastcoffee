-- 巴哈耳機普查 Supabase schema
-- 請在 Supabase SQL Editor 執行本檔。

create table if not exists public.census_brands (
  id text primary key,
  english_name text not null,
  chinese_name text not null default '',
  aliases text[] not null default '{}',
  status text not null default 'approved' check (status in ('approved', 'pending', 'rejected', 'merged')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.census_items (
  id text primary key,
  entry_id text not null,
  bahamut_id text not null,
  category text not null,
  brand_id text,
  brand text not null,
  canonical_brand text,
  model text not null,
  canonical_model text,
  item_note text,
  user_note text,
  status text not null default 'active' check (status in ('active', 'replaced', 'deleted')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create index if not exists census_items_entry_id_idx on public.census_items(entry_id);
create index if not exists census_items_bahamut_id_idx on public.census_items(bahamut_id);
create index if not exists census_items_brand_id_idx on public.census_items(brand_id);
create index if not exists census_items_status_idx on public.census_items(status);
create index if not exists census_items_category_idx on public.census_items(category);

alter table public.census_brands enable row level security;
alter table public.census_items enable row level security;

drop policy if exists "Public read census brands" on public.census_brands;
create policy "Public read census brands"
on public.census_brands
for select
using (true);

drop policy if exists "Public read active census items" on public.census_items;
create policy "Public read active census items"
on public.census_items
for select
using (status = 'active');

-- Streamlit 目前建議使用 server-side service_role key 寫入。
-- 若未來改成 anon key 寫入，請再補 insert/update/delete policy。
