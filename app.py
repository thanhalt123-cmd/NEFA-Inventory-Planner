import streamlit as st
import pandas as pd
import numpy as np
import sqlite3, math, base64, calendar
from io import BytesIO
from datetime import datetime, date, timedelta
from pathlib import Path

VERSION = "V2.3"
DB_PATH = Path('nefa_inventory_v2.db')
LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAYAAAA+VemSAAAXcElEQVR4nO3deXhU5aHH8d97ZstkX8i+LyCLEBEElKUioLaKWltoaxUX6lK7aPvce61P61PbWh9vb597W7WleFugUatFW1tRuRgWUaCAbLIlkEwChOyQPZnMzJnz3j9ilCUzWZgk8w6/z/PMP5CZc5KZ75wz57zvGSGlBBGpSRvtFSCioWPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKY8BECmPARApjwEQKM4/2CgyURzdQvK9G7ihphEc3cFV+PG6dkZEWFW6pHc7l6t6e5W4/2rPcwrw43DozMz863FLR3307dD1ua0Nj06muLkg5nGvZQ0Ii3GTGjIQ4TIqJEQO5z6HKZvl/e6pR2+wEJDCgOw1x3ew2M2aNT8RN09KF1XLp2469x8/IzQfrUNfkRHyUDXMmJWHulclC04brtwg+Qo7EK+sSnW1z3fq93+9at2F/DQwpISAgITE1Lx4rvjPLeUVmTPhwLLep3bXw+yt2F6/fW33ecgtz4rHiu7MwIct3JA3droeeKyldeby9HUKM3AtKSgmrpuHu7CzcmZnhd8HP/7NE/vpvR9Du9ECMwIteSglNCCwoTMXvvjNzWWJM2MtDeZxOpx72VNF+5+sfVcLp9kIIASklLCYNN01Nw68fnP5Ycpz9+UCvfzAK+oANKfHoizvla1tPINJ+/g5Dl0vHjLFj8Pef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"
GROUP_ORDER = [
    'QUẠT THÔNG GIÓ NEFA','QUẠT INOX VUÔNG NEFA','QTG ÂM TRẦN NEFA','MÁNG HÚT MÙI',
    'PHỤ KIỆN QTG','QTG CÔNG NGHIỆP','QUẠT ĐIỀU HÒA NEFA','QUẠT CẮT GIÓ','ĐỒ GIA DỤNG','HÀNG THÊM'
]
GROUP_RANK={g:i for i,g in enumerate(GROUP_ORDER)}

st.set_page_config(page_title='Phần mềm quản trị mua hàng Nefa Group', page_icon='📦', layout='wide')

def conn(): return sqlite3.connect(DB_PATH)
def cols(table):
    with conn() as c: return {r[1] for r in c.execute(f'PRAGMA table_info({table})').fetchall()}
def addcol(table, definition):
    name=definition.split()[0]
    if name not in cols(table):
        with conn() as c: c.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')

def init_db():
    with conn() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS snapshots(id INTEGER PRIMARY KEY AUTOINCREMENT,upload_time TEXT,report_name TEXT,report_days INTEGER,report_end TEXT,sku TEXT,product_name TEXT,product_group TEXT,opening REAL,receipts REAL,outbound REAL,ending REAL,daily_sales REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS product_groups(name TEXT PRIMARY KEY,created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS suppliers(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,phone TEXT,address TEXT,notes TEXT,created_at TEXT,active INTEGER DEFAULT 1)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,product_group TEXT,sku TEXT UNIQUE,product_name TEXT,created_at TEXT,updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sku_policy(sku TEXT PRIMARY KEY,lead_time INTEGER DEFAULT 30,target_after_arrival INTEGER DEFAULT 30,pack_size INTEGER DEFAULT 1,supplier TEXT DEFAULT '')''')
        c.execute('''CREATE TABLE IF NOT EXISTS po_headers(id INTEGER PRIMARY KEY AUTOINCREMENT,po_code TEXT UNIQUE,supplier TEXT,order_date TEXT,payment_date TEXT,production_date TEXT,eta TEXT,status TEXT,freight REAL DEFAULT 0,customs REAL DEFAULT 0,other_cost REAL DEFAULT 0,created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS po_items(id INTEGER PRIMARY KEY AUTOINCREMENT,po_id INTEGER,sku TEXT,qty REAL,cny_price REAL DEFAULT 0,usd_price REAL DEFAULT 0,cny_rate REAL DEFAULT 0,usd_rate REAL DEFAULT 0,unit_weight REAL DEFAULT 0,FOREIGN KEY(po_id) REFERENCES po_headers(id))''')
        # Keep legacy table readable for old deployments.
        c.execute('''CREATE TABLE IF NOT EXISTS purchase_orders(id INTEGER PRIMARY KEY AUTOINCREMENT,po_code TEXT,supplier TEXT,sku TEXT,qty REAL,unit_price REAL,unit_weight REAL,order_date TEXT,eta TEXT,status TEXT,freight REAL DEFAULT 0,customs REAL DEFAULT 0,other_cost REAL DEFAULT 0,allocation_method TEXT DEFAULT 'Theo giá trị',created_at TEXT)''')
init_db()
addcol('products','active INTEGER DEFAULT 1')
with conn() as _c:
    for _g in GROUP_ORDER:
        _c.execute('INSERT OR IGNORE INTO product_groups(name,created_at) VALUES(?,?)',(_g,datetime.now().isoformat(timespec='seconds')))

# Compact, fixed application header and MISA-inspired table layout
st.markdown("""<style>
:root{--brand:#205DA8;--cyan:#50BEC5;--ink:#183252}
.stApp{background:#f7f9fc}
.block-container{padding-top:3.95rem!important;padding-bottom:1.5rem!important;max-width:100%!important;padding-left:1.4rem!important;padding-right:1.4rem!important}
section[data-testid="stSidebar"]{width:190px!important;min-width:190px!important;background:#edf4f9;border-right:1px solid #d9e5ef}
section[data-testid="stSidebar"]>div{width:190px!important}
[data-testid="stMetric"]{background:white;border:1px solid #dbe4ed;border-radius:8px;padding:10px}
.stButton>button[kind="primary"]{background:#205DA8;border-color:#205DA8}
.stButton>button{border-radius:5px}
.stDataFrame{background:#fff}
.nefa-topbar{position:fixed;top:2.8rem;left:190px;right:0;height:58px;z-index:999;background:white;border-bottom:1px solid #dce6ef;display:flex;align-items:center;gap:18px;padding:5px 26px;box-shadow:0 1px 3px #dce5ee}
.nefa-topbar img{width:100px;max-height:42px;object-fit:contain}
.nefa-topbar strong{color:#183252;font-size:17px}.nefa-topbar span{font-size:12px;color:#637d96;margin-left:auto}
h1,h2,h3{color:#183252}
</style>""",unsafe_allow_html=True)
st.markdown(f"""<div class='nefa-topbar'><img src='data:image/png;base64,{LOGO_B64}'/><strong>Phần mềm quản trị mua hàng Nefa Group</strong><span>Phiên bản {VERSION}</span></div>""",unsafe_allow_html=True)

# ---------- helpers ----------
def load_table(name):
    with conn() as c: return pd.read_sql_query(f'SELECT * FROM {name}',c)
def normalize_text(v): return str(v).strip().upper() if pd.notna(v) else ''
def group_rank(g): return GROUP_RANK.get(normalize_text(g),999)
def sync_product(group,sku,name):
    sku=str(sku).strip(); group=str(group).strip(); name=str(name).strip(); now=datetime.now().isoformat(timespec='seconds')
    if not sku: return
    with conn() as c:
        c.execute('''INSERT INTO products(product_group,sku,product_name,created_at,updated_at) VALUES(?,?,?,?,?)
        ON CONFLICT(sku) DO UPDATE SET product_group=excluded.product_group,product_name=excluded.product_name,updated_at=excluded.updated_at''',(group,sku,name,now,now))
        c.execute('''INSERT INTO sku_policy(sku,lead_time,target_after_arrival,pack_size,supplier) VALUES(?,30,30,1,'') ON CONFLICT(sku) DO NOTHING''',(sku,))
def sync_products_from_df(df):
    for _,r in df.iterrows(): sync_product(r['NHÓM HÀNG HÓA'],r['Mã SKU'],r['Tên hàng hóa'])
def normalize_source(file):
    raw=pd.read_excel(file,header=None); header_idx=None
    for i in range(min(len(raw),40)):
        if any(str(v).strip()=='Mã SKU' for v in raw.iloc[i].tolist()): header_idx=i; break
    if header_idx is None: raise ValueError('Không tìm thấy dòng tiêu đề "Mã SKU".')
    file.seek(0); df=pd.read_excel(file,header=header_idx); df.columns=[str(c).strip() for c in df.columns]
    sku_col=next((c for c in df.columns if 'Mã SKU' in c),None); name_col=next((c for c in df.columns if 'Tên hàng hóa' in c),None); group_col=next((c for c in df.columns if 'Nhóm hàng hóa' in c),None)
    if not all([sku_col,name_col,group_col]): raise ValueError('Thiếu SKU/Tên hàng/Nhóm hàng.')
    base=df.columns.get_loc(group_col)+1; qty=[df.columns[base+i] for i in [0,2,4,6] if base+i<len(df.columns)]
    if len(qty)<4: raise ValueError('Không nhận diện đủ Tồn đầu/Nhập/Xuất/Tồn cuối.')
    out=pd.DataFrame({'NHÓM HÀNG HÓA':df[group_col],'Mã SKU':df[sku_col],'Tên hàng hóa':df[name_col],'Tồn đầu kỳ':pd.to_numeric(df[qty[0]],errors='coerce'),'Nhập trong kỳ':pd.to_numeric(df[qty[1]],errors='coerce'),'Xuất trong kỳ':pd.to_numeric(df[qty[2]],errors='coerce'),'Tồn cuối kỳ':pd.to_numeric(df[qty[3]],errors='coerce')})
    return out.dropna(subset=['Mã SKU'])
def save_snapshot(df,name,days,report_end):
    now=datetime.now().isoformat(timespec='seconds'); rows=[]
    for _,r in df.iterrows():
        rows.append((now,name,int(days),str(report_end),str(r['Mã SKU']),str(r['Tên hàng hóa']),str(r['NHÓM HÀNG HÓA']),float(r['Tồn đầu kỳ']),float(r['Nhập trong kỳ']),float(r['Xuất trong kỳ']),float(r['Tồn cuối kỳ']),float(r['Xuất trong kỳ'])/days))
    with conn() as c: c.executemany('''INSERT INTO snapshots(upload_time,report_name,report_days,report_end,sku,product_name,product_group,opening,receipts,outbound,ending,daily_sales) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',rows)
    sync_products_from_df(df)
def weighted_forecast(sku,fallback=0):
    h=load_table('snapshots'); h=h[h['sku'].astype(str)==str(sku)].copy()
    if h.empty:return fallback
    h['d']=pd.to_datetime(h['report_end'],errors='coerce'); h=h.sort_values(['d','id'],ascending=False).head(8); vals=h['daily_sales'].astype(float).to_numpy(); weights=np.array([0.72**i for i in range(len(vals))]); return float(np.average(vals,weights=weights))
def active_po_items():
    h=load_table('po_headers'); i=load_table('po_items')
    if h.empty or i.empty:return pd.DataFrame()
    x=i.merge(h,left_on='po_id',right_on='id',suffixes=('_item','_po')); return x[~x['status'].isin(['Đã nhận','Đã hủy'])].copy()
def open_po_maps():
    x=active_po_items();
    if x.empty:return {},{}
    qty=x.groupby('sku')['qty'].sum().to_dict(); eta={}
    for sku,g in x.groupby('sku'):
        d=pd.to_datetime(g['eta'],errors='coerce').dropna(); eta[sku]=d.min().date() if len(d) else None
    return qty,eta
def latest_base():
    hist=load_table('snapshots')
    if hist.empty:return pd.DataFrame(),date.today()
    hist['d']=pd.to_datetime(hist['report_end'],errors='coerce'); latest=hist.sort_values(['d','id']).groupby('sku').tail(1)
    base=pd.DataFrame({'Nhóm':latest['product_group'],'SKU':latest['sku'],'Tên hàng':latest['product_name'],'Tồn hiện tại':pd.to_numeric(latest['ending'],errors='coerce').fillna(0),'Xuất kỳ gần nhất':pd.to_numeric(latest['outbound'],errors='coerce').fillna(0),'Số ngày kỳ':pd.to_numeric(latest['report_days'],errors='coerce').fillna(1)})
    end=latest['d'].max().date() if latest['d'].notna().any() else date.today(); return base,end
def build_plan():
    base,report_end=latest_base()
    if base.empty:return pd.DataFrame(),report_end
    pol=load_table('sku_policy'); pol=pol.set_index('sku') if not pol.empty else pd.DataFrame(); po_qty,po_eta=open_po_maps(); rows=[]
    for _,r in base.iterrows():
        sku=str(r['SKU']); current=float(r['Tồn hiện tại']); fallback=float(r['Xuất kỳ gần nhất'])/max(float(r['Số ngày kỳ']),1); daily=weighted_forecast(sku,fallback)
        lead=int(pol.loc[sku,'lead_time']) if not pol.empty and sku in pol.index else 30; target_days=int(pol.loc[sku,'target_after_arrival']) if not pol.empty and sku in pol.index else 30; pack=int(pol.loc[sku,'pack_size']) if not pol.empty and sku in pol.index else 1
        incoming=float(po_qty.get(sku,0)); eta=po_eta.get(sku); reorder=math.ceil(daily*lead); target=math.ceil(daily*(lead+target_days)); inv=current+incoming; suggested=max(0,target-inv); rounded=int(math.ceil(suggested/pack)*pack) if suggested>0 and pack>0 else 0; cover=current/daily if daily>0 else 999; stockout=report_end+timedelta(days=math.floor(cover)) if daily>0 else None; gap=max(0,(eta-stockout).days) if eta and stockout else 0
        if current<=reorder:status='🔴 ĐẶT HÀNG NGAY'
        elif current<=math.ceil(reorder*1.2):status='🟠 SẮP PHẢI ĐẶT'
        elif gap>0:status='🟡 PO VỀ TRỄ'
        elif current>target*1.5 and target>0:status='🔵 DƯ TỒN'
        else:status='🟢 ĐỦ HÀNG'
        rows.append([r['Nhóm'],sku,r['Tên hàng'],current,daily,cover,lead,reorder,incoming,eta,target,suggested,pack,rounded,stockout,gap,status])
    p=pd.DataFrame(rows,columns=['Nhóm','SKU','Tên hàng','Tồn hiện tại','Forecast bán/ngày','Ngày còn hàng','Lead time N','Ngưỡng đặt hàng','Hàng đang đặt','ETA gần nhất','Target','SL cần đặt','Quy cách','PO làm tròn','Dự kiến hết hàng','Số ngày thiếu trước ETA','Trạng thái'])
    p['_gr']=p['Nhóm'].map(group_rank); p['_name']=p['Tên hàng'].astype(str).str.upper(); p=p.sort_values(['_gr','_name','SKU']).drop(columns=['_gr','_name']); return p,report_end

def donut(title,value,total,label=''):
    total=max(float(total),1); value=max(float(value),0); pct=min(value/total,1.0)
    st.markdown(f'''<div style="background:white;border:1px solid #DDE8F0;border-radius:16px;padding:14px;text-align:center;min-height:210px"><div style="font-weight:700;color:#153250;min-height:44px">{title}</div><div style="margin:8px auto;width:108px;height:108px;border-radius:50%;background:conic-gradient(#2464AE {pct*360:.0f}deg,#E5F1F4 0);display:grid;place-items:center"><div style="width:72px;height:72px;background:white;border-radius:50%;display:grid;place-items:center;font-weight:800;color:#2464AE">{pct*100:.0f}%</div></div><div style="font-size:20px;font-weight:800;color:#153250">{value:,.0f}</div><div class="small-note">{label}</div></div>''',unsafe_allow_html=True)

# ---------- navigation ----------
page=st.sidebar.radio('Chức năng',['📊 Dashboard','🚦 Kế hoạch đặt hàng','📤 Upload XNT','📚 Danh mục sản phẩm','🏷️ Nhóm sản phẩm','🏭 Nhà cung cấp','🚢 Đơn hàng nhập','⚙️ Chính sách tồn kho','🕘 Lịch sử'])

if page=='📤 Upload XNT':
    st.header('Upload báo cáo XNT'); uploaded=st.file_uploader('File XNT (.xlsx)',type=['xlsx']); c1,c2=st.columns(2); days=c1.number_input('Số ngày XNT của file',1,366,7); end=c2.date_input('Ngày cuối kỳ báo cáo',value=date.today())
    if uploaded:
        try:
            df=normalize_source(uploaded)
            for c in ['Tồn đầu kỳ','Nhập trong kỳ','Xuất trong kỳ','Tồn cuối kỳ']:df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0)
            st.dataframe(df,use_container_width=True,height=430)
            if st.button('💾 Lưu XNT vào lịch sử',type='primary'):save_snapshot(df,uploaded.name,days,end);st.success(f'Đã lưu {len(df)} SKU. Sản phẩm mới cũng đã tự động thêm vào Danh mục và Chính sách tồn kho.')
        except Exception as e:st.error(str(e))

elif page=='🏷️ Nhóm sản phẩm':
    st.header('Quản lý nhóm sản phẩm')
    with st.form('new_group'):
        group_name=st.text_input('Tên nhóm sản phẩm mới')
        if st.form_submit_button('➕ Tạo nhóm',type='primary'):
            group_name=group_name.strip().upper()
            if not group_name: st.error('Nhập tên nhóm.')
            else:
                with conn() as cx:cx.execute('INSERT OR IGNORE INTO product_groups(name,created_at) VALUES(?,?)',(group_name,datetime.now().isoformat(timespec='seconds')))
                st.rerun()
    groups=load_table('product_groups')
    st.dataframe(groups.rename(columns={'name':'Tên nhóm','created_at':'Ngày tạo'}),hide_index=True,use_container_width=True)
    st.caption('Các nhóm gốc giữ thứ tự ưu tiên; nhóm mới được xếp tiếp theo.')

elif page=='🏭 Nhà cung cấp':
    title,actions=st.columns([5,1.4],vertical_alignment='center')
    title.header('Danh mục nhà cung cấp')
    if actions.button('➕ Thêm mới',type='primary',use_container_width=True):st.session_state['supplier_add']=not st.session_state.get('supplier_add',False)
    if st.session_state.get('supplier_add'):
        with st.form('supplier_new',clear_on_submit=True):
            a,b=st.columns(2);name=a.text_input('Tên nhà cung cấp *');phone=b.text_input('Số điện thoại')
            address=st.text_input('Địa chỉ');notes=st.text_area('Ghi chú',height=75)
            if st.form_submit_button('Lưu nhà cung cấp',type='primary'):
                if not name.strip():st.error('Cần nhập tên nhà cung cấp.')
                else:
                    try:
                        with conn() as cx:cx.execute('INSERT INTO suppliers(name,phone,address,notes,created_at) VALUES(?,?,?,?,?)',(name.strip(),phone,address,notes,datetime.now().isoformat(timespec='seconds')))
                        st.session_state['supplier_add']=False;st.rerun()
                    except sqlite3.IntegrityError:st.error('Tên nhà cung cấp đã tồn tại.')
    df=load_table('suppliers');df=df[df['active']==1].copy()
    st.subheader('Danh sách nhà cung cấp')
    if not df.empty:
        f=st.columns([1,2,2,2,2]);keys=['created_at','name','phone','address','notes'];terms=[]
        for col,key,label in zip(f,keys,['Ngày tạo','Tên NCC','SĐT','Địa chỉ','Ghi chú']):terms.append(col.text_input(label,placeholder='Lọc '+label,key='sf_'+key))
        for key,term in zip(keys,terms):
            if term:df=df[df[key].fillna('').astype(str).str.contains(term,case=False,regex=False)]
        show=df[['id','created_at','name','phone','address','notes']].copy();show.insert(0,'STT',range(1,len(show)+1))
        show=show.rename(columns={'created_at':'Ngày tạo','name':'Tên nhà cung cấp','phone':'SĐT','address':'Địa chỉ','notes':'Ghi chú'})
        edited=st.data_editor(show,hide_index=True,use_container_width=True,disabled=['id','STT','Ngày tạo'],column_config={'id':None},key='supplier_editor')
        c1,c2=st.columns([1,3]);
        if c1.button('💾 Lưu chỉnh sửa',type='primary'):
            try:
                with conn() as cx:
                    for _,r in edited.iterrows():cx.execute('UPDATE suppliers SET name=?,phone=?,address=?,notes=? WHERE id=?',(r['Tên nhà cung cấp'],r['SĐT'],r['Địa chỉ'],r['Ghi chú'],int(r['id'])))
                st.rerun()
            except sqlite3.IntegrityError:st.error('Trùng tên nhà cung cấp.')
        target=c2.selectbox('Ngừng sử dụng NCC',['']+[f"{r['id']} · {r['name']}" for _,r in df.iterrows()])
        if target:
            if c2.checkbox('Xác nhận ngừng sử dụng nhà cung cấp') and c2.button('Ngừng sử dụng'):
                with conn() as cx:cx.execute('UPDATE suppliers SET active=0 WHERE id=?',(int(target.split(' · ')[0]),))
                st.rerun()
    else:st.info('Chưa có nhà cung cấp phù hợp.')

elif page=='📚 Danh mục sản phẩm':
    title,actions=st.columns([5,2],vertical_alignment='center')
    title.header('Danh mục sản phẩm')
    with actions:
        c1,c2=st.columns(2)
        if c1.button('➕ Thêm mới',type='primary',use_container_width=True):st.session_state['product_add_mode']='manual'
        if c2.button('📥 Upload file',use_container_width=True):st.session_state['product_add_mode']='upload'
    mode=st.session_state.get('product_add_mode')
    if mode=='manual':
        with st.container(border=True):
            st.subheader('Thêm mới sản phẩm')
            groups=load_table('product_groups')['name'].tolist()
            with st.form('add_product_23',clear_on_submit=True):
                a,b,c=st.columns([1.4,1,2]);g=a.selectbox('Nhóm sản phẩm',groups+['➕ TẠO NHÓM MỚI']);new_group=a.text_input('Tên nhóm mới (nếu chọn tạo nhóm)') if g=='➕ TẠO NHÓM MỚI' else ''
                sku=b.text_input('SKU');name=c.text_input('Tên hàng hóa')
                if st.form_submit_button('Lưu sản phẩm',type='primary'):
                    g=(new_group.strip().upper() if g=='➕ TẠO NHÓM MỚI' else g)
                    if not g or not sku.strip() or not name.strip():st.error('Nhập đủ nhóm, SKU và tên hàng.')
                    else:
                        existing=load_table('products');sku=sku.strip();name=name.strip()
                        if (existing['sku'].str.upper()==sku.upper()).any() or (existing['product_name'].str.upper()==name.upper()).any():st.error('SKU hoặc tên hàng đã tồn tại.')
                        else:
                            with conn() as cx:cx.execute('INSERT OR IGNORE INTO product_groups(name,created_at) VALUES(?,?)',(g,datetime.now().isoformat(timespec='seconds')))
                            sync_product(g,sku,name);st.session_state['product_add_mode']=None;st.rerun()
            if st.button('Đóng',key='close_prod'):st.session_state['product_add_mode']=None;st.rerun()
    elif mode=='upload':
        with st.container(border=True):
            st.subheader('Upload danh mục sản phẩm')
            sample=pd.DataFrame([{'STT':1,'Nhóm sản phẩm':'QUẠT THÔNG GIÓ NEFA','SKU':'QTG.150','Tên hàng hóa':'Quạt thông gió HF150'}]);out=BytesIO()
            with pd.ExcelWriter(out,engine='openpyxl') as w:sample.to_excel(w,index=False)
            st.download_button('⬇️ Tải file mẫu',out.getvalue(),'NEFA_Mau_Danh_Muc.xlsx')
            file=st.file_uploader('Chọn file danh mục',type=['xlsx'])
            if file:
                try:
                    imported=pd.read_excel(file);needed=['Nhóm sản phẩm','SKU','Tên hàng hóa']
                    if not all(c in imported.columns for c in needed):raise ValueError('Thiếu cột nhóm, SKU hoặc tên hàng hóa.')
                    st.dataframe(imported,use_container_width=True,hide_index=True)
                    if st.button('Lưu sản phẩm mới',type='primary'):
                        existing=load_table('products');skus=set(existing['sku'].astype(str).str.upper());names=set(existing['product_name'].astype(str).str.upper());count=0
                        for _,r in imported.iterrows():
                            g=str(r['Nhóm sản phẩm']).strip().upper();sku=str(r['SKU']).strip();name=str(r['Tên hàng hóa']).strip()
                            if sku.upper() in skus or name.upper() in names or not g or not sku or not name or sku.lower()=='nan':continue
                            with conn() as cx:cx.execute('INSERT OR IGNORE INTO product_groups(name,created_at) VALUES(?,?)',(g,datetime.now().isoformat(timespec='seconds')))
                            sync_product(g,sku,name);skus.add(sku.upper());names.add(name.upper());count+=1
                        st.success(f'Đã thêm {count} sản phẩm.');st.session_state['product_add_mode']=None;st.rerun()
                except Exception as e:st.error(str(e))
            if st.button('Đóng',key='close_upload_23'):st.session_state['product_add_mode']=None;st.rerun()
    st.subheader('Danh sách sản phẩm')
    df=load_table('products');df=df[df['active']==1].copy()
    if not df.empty:
        f1,f2,f3=st.columns([2,1.3,3]);fg=f1.text_input('Nhóm sản phẩm',placeholder='Lọc theo nhóm');fs=f2.text_input('SKU',placeholder='Lọc SKU');fn=f3.text_input('Tên hàng hóa',placeholder='Lọc tên hàng')
        for field,term in [('product_group',fg),('sku',fs),('product_name',fn)]:
            if term:df=df[df[field].fillna('').astype(str).str.contains(term,case=False,regex=False)]
        df['_gr']=df['product_group'].map(group_rank);df['_name']=df['product_name'].str.upper();df=df.sort_values(['_gr','_name','sku'])
        show=df[['id','product_group','sku','product_name']].rename(columns={'product_group':'Nhóm sản phẩm','sku':'SKU','product_name':'Tên hàng hóa'}).copy();show.insert(0,'STT',range(1,len(show)+1))
        st.caption(f'Hiển thị {len(show)} sản phẩm')
        edited=st.data_editor(show,hide_index=True,use_container_width=True,height=520,disabled=['id','STT'],column_config={'id':None},key='prod_editor_23')
        c1,c2=st.columns([1,3])
        if c1.button('💾 Lưu chỉnh sửa',type='primary'):
            try:
                with conn() as cx:
                    for _,r in edited.iterrows():
                        old=show.loc[show['id']==r['id'],'SKU'].iloc[0];new=str(r['SKU']).strip()
                        cx.execute('UPDATE products SET product_group=?,sku=?,product_name=?,updated_at=? WHERE id=?',(r['Nhóm sản phẩm'],new,r['Tên hàng hóa'],datetime.now().isoformat(timespec='seconds'),int(r['id'])))
                        if old!=new:
                            cx.execute('UPDATE sku_policy SET sku=? WHERE sku=?',(new,old))
                            cx.execute('UPDATE snapshots SET sku=? WHERE sku=?',(new,old))
                            cx.execute('UPDATE po_items SET sku=? WHERE sku=?',(new,old))
                st.success('Đã lưu.');st.rerun()
            except Exception as e:st.error(str(e))
        target=c2.selectbox('Ngừng sử dụng sản phẩm',['']+[f"{int(r['id'])} · {r['SKU']} · {r['Tên hàng hóa']}" for _,r in show.iterrows()])
        if target and c2.checkbox('Xác nhận ngừng sử dụng, giữ lịch sử XNT/PO') and c2.button('Ngừng sử dụng sản phẩm'):
            with conn() as cx:cx.execute('UPDATE products SET active=0 WHERE id=?',(int(target.split(' · ')[0]),))
            st.rerun()
    else:st.info('Chưa có sản phẩm phù hợp. Có thể thêm mới hoặc upload file.')

elif page=='🚢 Đơn hàng nhập':
    st.header('Đơn hàng nhập'); products=load_table('products')
    if products.empty:st.warning('Cần có Danh mục sản phẩm trước khi tạo đơn hàng.')
    else:
        labels={f"{r['product_name']}  |  {r['sku']}":r['sku'] for _,r in products.sort_values(['product_group','product_name']).iterrows()}
        with st.form('po_header'):
            a,b,c=st.columns(3); code=a.text_input('Mã đơn hàng',value=f'PO-{date.today():%Y%m%d}-'); supplier=b.selectbox('Nhà cung cấp', ['']+load_table('suppliers').query('active == 1')['name'].tolist()); status=c.selectbox('Trạng thái',['Đang sản xuất','Đang vận chuyển','Sắp nhận','Đã nhận','Đã hủy'])
            a,b,c,d=st.columns(4); od=a.date_input('Ngày đặt hàng',date.today()); pay=b.date_input('Ngày thanh toán thành công',date.today()); prod=c.date_input('Ngày dự kiến sản xuất',date.today()+timedelta(days=10)); eta=d.date_input('Ngày dự kiến về kho',date.today()+timedelta(days=30))
            a,b,c=st.columns(3); freight=a.number_input('Vận chuyển',0.0,step=100000.0); customs=b.number_input('Hải quan/thuế phí',0.0,step=100000.0); other=c.number_input('Chi phí khác',0.0,step=100000.0)
            if st.form_submit_button('Tạo đầu đơn hàng',type='primary'):
                try:
                    with conn() as cx:cx.execute('INSERT INTO po_headers(po_code,supplier,order_date,payment_date,production_date,eta,status,freight,customs,other_cost,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(code,supplier,str(od),str(pay),str(prod),str(eta),status,freight,customs,other,datetime.now().isoformat(timespec='seconds')))
                    st.success('Đã tạo đơn. Chọn đơn ở dưới để thêm nhiều sản phẩm.')
                except Exception as e:st.error(f'Không tạo được đơn: {e}')
        headers=load_table('po_headers')
        if not headers.empty:
            selected=st.selectbox('Đơn hàng đang thao tác',headers.sort_values('id',ascending=False)['po_code'].tolist()); h=headers[headers['po_code']==selected].iloc[0]; po_id=int(h['id'])
            st.subheader('Thêm sản phẩm vào đơn')
            with st.form('add_item',clear_on_submit=True):
                product_label=st.selectbox('Tên sản phẩm',list(labels.keys())); sku=labels[product_label]
                a,b,c,d=st.columns(4); qty=a.number_input('Số lượng',0.0,step=1.0); cny=b.number_input('Đơn giá Tệ',0.0,step=1.0); usd=c.number_input('Đơn giá USD',0.0,step=1.0); weight=d.number_input('Khối lượng/SP (kg)',0.0,step=.1)
                a,b=st.columns(2); cny_rate=a.number_input('Tỷ giá Tệ (VND)',0.0,step=100.0); usd_rate=b.number_input('Tỷ giá USD (VND)',0.0,step=100.0)
                if st.form_submit_button('➕ Thêm sản phẩm'):
                    if qty<=0:st.error('Số lượng phải > 0.')
                    else:
                        with conn() as cx:cx.execute('INSERT INTO po_items(po_id,sku,qty,cny_price,usd_price,cny_rate,usd_rate,unit_weight) VALUES(?,?,?,?,?,?,?,?)',(po_id,sku,qty,cny,usd,cny_rate,usd_rate,weight))
                        st.success('Đã thêm sản phẩm vào đơn.')
            items=load_table('po_items'); items=items[items['po_id']==po_id].copy()
            if not items.empty:
                names=products.set_index('sku')['product_name'].to_dict(); items['Tên sản phẩm']=items['sku'].map(names); items['Đơn giá quy đổi']=items['cny_price']*items['cny_rate']+items['usd_price']*items['usd_rate']; items['Tiền hàng']=items['qty']*items['Đơn giá quy đổi']; items['Tổng kg']=items['qty']*items['unit_weight']; total_goods=items['Tiền hàng'].sum(); total_kg=items['Tổng kg'].sum(); extra=float(h['freight'])+float(h['customs'])+float(h['other_cost']); items['CP phát sinh/SP']=np.where(total_kg>0,extra*items['unit_weight']/total_kg,0); items['CP phát sinh dòng']=items['CP phát sinh/SP']*items['qty']; items['Tổng sau CP']=items['Tiền hàng']+items['CP phát sinh dòng']
                st.dataframe(items[['Tên sản phẩm','sku','qty','cny_price','usd_price','cny_rate','usd_rate','Đơn giá quy đổi','Tiền hàng','unit_weight','Tổng kg','CP phát sinh/SP','CP phát sinh dòng','Tổng sau CP']],use_container_width=True)
                c1,c2,c3=st.columns(3);c1.metric('Tổng tiền hàng',f"{total_goods:,.0f} đ");c2.metric('Tổng khối lượng',f"{total_kg:,.1f} kg");c3.metric('Tổng giá trị đơn hàng',f"{total_goods+extra:,.0f} đ")
        st.subheader('Danh sách đơn hàng');
        if not headers.empty:st.dataframe(headers.sort_values('id',ascending=False),use_container_width=True)

elif page=='⚙️ Chính sách tồn kho':
    st.header('Chính sách tồn kho theo SKU'); products=load_table('products'); pol=load_table('sku_policy')
    if products.empty:st.info('Chưa có Danh mục sản phẩm.')
    else:
        m=products.merge(pol,on='sku',how='left'); m['lead_time']=m['lead_time'].fillna(30).astype(int);m['target_after_arrival']=m['target_after_arrival'].fillna(30).astype(int);m['pack_size']=m['pack_size'].fillna(1).astype(int);m['supplier']=m['supplier'].fillna('');m['_gr']=m['product_group'].map(group_rank);m=m.sort_values(['_gr','product_name','sku']).drop(columns='_gr')
        edit=m[['product_group','sku','product_name','lead_time','target_after_arrival','pack_size','supplier']].rename(columns={'product_group':'Nhóm sản phẩm','sku':'SKU','product_name':'Tên hàng','lead_time':'Lead Time (ngày)','target_after_arrival':'Ngày tồn mục tiêu','pack_size':'Quy cách đóng gói','supplier':'NCC'})
        edited=st.data_editor(edit,use_container_width=True,height=560,hide_index=True,disabled=['Nhóm sản phẩm','SKU','Tên hàng'])
        if st.button('💾 Lưu chính sách',type='primary'):
            with conn() as cx:
                for _,r in edited.iterrows():cx.execute('''INSERT INTO sku_policy(sku,lead_time,target_after_arrival,pack_size,supplier) VALUES(?,?,?,?,?) ON CONFLICT(sku) DO UPDATE SET lead_time=excluded.lead_time,target_after_arrival=excluded.target_after_arrival,pack_size=excluded.pack_size,supplier=excluded.supplier''',(r['SKU'],int(r['Lead Time (ngày)']),int(r['Ngày tồn mục tiêu']),int(r['Quy cách đóng gói']),r['NCC']))
            st.success('Đã lưu chính sách.')

elif page=='🕘 Lịch sử':
    st.header('Lịch sử XNT'); hist=load_table('snapshots'); st.dataframe(hist.sort_values('id',ascending=False),use_container_width=True,height=600) if not hist.empty else st.info('Chưa có dữ liệu lịch sử.')

elif page=='📊 Dashboard':
    st.header('Dashboard báo cáo mua hàng'); plan,_=build_plan(); hist=load_table('snapshots'); headers=load_table('po_headers'); items=load_table('po_items')
    if plan.empty:st.warning('Chưa có dữ liệu XNT để lập Dashboard.')
    else:
        total=len(plan); today=date.today(); month_start=today.replace(day=1)
        overdue=int((plan['Trạng thái']=='🔴 ĐẶT HÀNG NGAY').sum()); soon=int((plan['Trạng thái']=='🟠 SẮP PHẢI ĐẶT').sum()); longlead=int((plan['Lead time N']>=45).sum()); delayed=int((plan['Số ngày thiếu trước ETA']>0).sum())
        newpo=0
        if not headers.empty:
            d=pd.to_datetime(headers['order_date'],errors='coerce');newpo=int(((d.dt.date>=month_start)&(d.dt.date<=today)).sum())
        cols6=st.columns(3)
        with cols6[0]:donut('Sản phẩm sắp phải nhập',soon,total,'SKU')
        with cols6[1]:donut('Quá hạn cần nhập',overdue,total,'SKU')
        with cols6[2]:donut('Lead time dài ≥45 ngày',longlead,total,'SKU')
        cols6=st.columns(3)
        with cols6[0]:donut('Đơn có nguy cơ/chậm kế hoạch',delayed,max(newpo,1),'SKU/đơn cảnh báo')
        with cols6[1]:donut('Đơn hàng nhập mới tháng',newpo,max(newpo,1),'đơn')
        with cols6[2]:donut('SKU đang theo dõi',total,total,'mã hàng')
        st.subheader('Sản phẩm bán chạy')
        c1,c2=st.columns(2); c1.markdown('**Theo ngày – Forecast hiện tại**');c1.dataframe(plan.nlargest(10,'Forecast bán/ngày')[['SKU','Tên hàng','Forecast bán/ngày']],hide_index=True,use_container_width=True)
        if not hist.empty:
            hh=hist.copy();hh['d']=pd.to_datetime(hh['report_end'],errors='coerce');hh=hh[(hh['d'].dt.year==today.year)&(hh['d'].dt.month==today.month)];monthly=hh.groupby(['sku','product_name'],as_index=False)['outbound'].sum().nlargest(10,'outbound');c2.markdown('**Theo tháng – Xuất trong tháng**');c2.dataframe(monthly.rename(columns={'sku':'SKU','product_name':'Tên hàng','outbound':'SL xuất tháng'}),hide_index=True,use_container_width=True)
        st.subheader('Báo cáo vận hành')
        a,b,c=st.tabs(['Lead time dài','Sắp/đã phải nhập','Đơn hàng chậm'])
        with a:st.dataframe(plan.nlargest(20,'Lead time N')[['Nhóm','SKU','Tên hàng','Lead time N']],hide_index=True,use_container_width=True)
        with b:st.dataframe(plan[plan['Trạng thái'].isin(['🔴 ĐẶT HÀNG NGAY','🟠 SẮP PHẢI ĐẶT'])][['Nhóm','SKU','Tên hàng','Ngày còn hàng','Ngưỡng đặt hàng','Tồn hiện tại','Trạng thái']],hide_index=True,use_container_width=True)
        with c:st.dataframe(plan[plan['Số ngày thiếu trước ETA']>0][['SKU','Tên hàng','ETA gần nhất','Dự kiến hết hàng','Số ngày thiếu trước ETA']],hide_index=True,use_container_width=True)
        st.subheader('Sản phẩm nhập mới trong tháng theo mã hàng')
        if not headers.empty and not items.empty:
            x=items.merge(headers[['id','order_date','status']],left_on='po_id',right_on='id');x['d']=pd.to_datetime(x['order_date'],errors='coerce');x=x[(x['d'].dt.year==today.year)&(x['d'].dt.month==today.month)];agg=x.groupby('sku',as_index=False)['qty'].sum().sort_values('qty',ascending=False);st.dataframe(agg.rename(columns={'sku':'SKU','qty':'Tổng SL đặt trong tháng'}),hide_index=True,use_container_width=True)
        else:st.info('Chưa có đơn hàng nhập trong tháng.')

else:
    st.header('Kế hoạch đặt hàng'); plan,_=build_plan()
    if plan.empty:st.warning('Chưa có XNT đã lưu. Vào Upload XNT để tạo kế hoạch.')
    else:
        c1,c2,c3,c4,c5=st.columns(5);c1.metric('Tổng SKU',len(plan));c2.metric('Cần đặt ngay',int((plan['Trạng thái']=='🔴 ĐẶT HÀNG NGAY').sum()));c3.metric('PO về trễ',int((plan['Số ngày thiếu trước ETA']>0).sum()));c4.metric('Tổng SL PO đề xuất',f"{plan['PO làm tròn'].sum():,.0f}");c5.metric('Hàng đang đặt',f"{plan['Hàng đang đặt'].sum():,.0f}")
        st.subheader('Danh sách thứ tự ưu tiên theo dải sản phẩm')
        st.dataframe(plan,use_container_width=True,height=600,hide_index=True,column_config={'Forecast bán/ngày':st.column_config.NumberColumn(format='%.2f'),'Ngày còn hàng':st.column_config.NumberColumn(format='%.1f')})
        buf=BytesIO();
        with pd.ExcelWriter(buf,engine='openpyxl') as w:plan.to_excel(w,index=False,sheet_name='Ke_hoach_V21')
        st.download_button('⬇️ Xuất kế hoạch',buf.getvalue(),'NEFA_Ke_hoach_nhap_hang_V21.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')
