import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import math
from io import BytesIO
from datetime import datetime, date, timedelta
from pathlib import Path

st.set_page_config(page_title='NEFA Inventory Planner V2', page_icon='📦', layout='wide')
DB_PATH = Path('nefa_inventory_v2.db')

# ---------- Database ----------
def conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with conn() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, upload_time TEXT, report_name TEXT,
            report_days INTEGER, report_end TEXT, sku TEXT, product_name TEXT, product_group TEXT,
            opening REAL, receipts REAL, outbound REAL, ending REAL, daily_sales REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sku_policy (
            sku TEXT PRIMARY KEY, lead_time INTEGER DEFAULT 30, target_after_arrival INTEGER DEFAULT 30,
            pack_size INTEGER DEFAULT 1, supplier TEXT DEFAULT '')''')
        c.execute('''CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, po_code TEXT, supplier TEXT, sku TEXT, qty REAL,
            unit_price REAL, unit_weight REAL, order_date TEXT, eta TEXT, status TEXT,
            freight REAL DEFAULT 0, customs REAL DEFAULT 0, other_cost REAL DEFAULT 0,
            allocation_method TEXT DEFAULT 'Theo giá trị', created_at TEXT)''')
init_db()

st.markdown('''<style>
.block-container{padding-top:1.1rem;max-width:1600px}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:14px}
.hero{background:linear-gradient(120deg,#0f172a,#1e3a5f);padding:22px 26px;border-radius:18px;color:white;margin-bottom:14px}
.hero h1{margin:0;font-size:29px}.hero p{margin:6px 0 0;color:#cbd5e1}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>NEFA Inventory Planner V2</h1><p>Lịch sử XNT → Weighted Forecast → PO/ETA → Days of Cover → Reorder Point → Target Stock → Suggested PO</p></div>', unsafe_allow_html=True)

# ---------- Source parsing ----------
def demo_data():
    return pd.DataFrame([
        ['QUẠT THÔNG GIÓ NEFA','QTG.110','Quạt thông gió hút mùi Nefa HF100',0,45,45,0],
        ['QUẠT THÔNG GIÓ NEFA','QTG.125','Quạt thông gió hút mùi Nefa HF125',0,25,25,0],
        ['QUẠT THÔNG GIÓ NEFA','QTG.150','Quạt thông gió hút mùi Nefa HF150',3,282,283,2],
        ['QUẠT THÔNG GIÓ NEFA','QTG.200','Quạt thông gió hút mùi Nefa HF200',0,172,170,2],
        ['QUẠT INOX VUÔNG NEFA','QUẠT.HV.INOX.FD150','Quạt thông gió - hút mùi vuông Nefa - inox FD150',0,59,59,0],
        ['QUẠT INOX VUÔNG NEFA','QUAT.HV.FD200.INOX','Quạt thông gió - hút mùi vuông Nefa - inox FD200',0,19,19,0],
    ], columns=['NHÓM HÀNG HÓA','Mã SKU','Tên hàng hóa','Tồn đầu kỳ','Nhập trong kỳ','Xuất trong kỳ','Tồn cuối kỳ'])

def normalize_source(file):
    raw = pd.read_excel(file, header=None)
    header_idx = None
    for i in range(min(len(raw), 40)):
        vals = raw.iloc[i].astype(str).str.strip().tolist()
        if any(v == 'Mã SKU' for v in vals): header_idx = i; break
    if header_idx is None: raise ValueError('Không tìm thấy dòng tiêu đề "Mã SKU".')
    file.seek(0)
    df = pd.read_excel(file, header=header_idx)
    df.columns = [str(c).strip() for c in df.columns]
    sku_col = next((c for c in df.columns if 'Mã SKU' in c), None)
    name_col = next((c for c in df.columns if 'Tên hàng hóa' in c), None)
    group_col = next((c for c in df.columns if 'Nhóm hàng hóa' in c), None)
    if not all([sku_col,name_col,group_col]): raise ValueError('Thiếu SKU/Tên hàng/Nhóm hàng.')
    base = df.columns.get_loc(group_col)+1
    qty_cols = [df.columns[base+i] for i in [0,2,4,6] if base+i < len(df.columns)]
    if len(qty_cols)<4: raise ValueError('Không nhận diện đủ Tồn đầu/Nhập/Xuất/Tồn cuối.')
    out = pd.DataFrame({'NHÓM HÀNG HÓA':df[group_col], 'Mã SKU':df[sku_col], 'Tên hàng hóa':df[name_col],
        'Tồn đầu kỳ':pd.to_numeric(df[qty_cols[0]],errors='coerce'), 'Nhập trong kỳ':pd.to_numeric(df[qty_cols[1]],errors='coerce'),
        'Xuất trong kỳ':pd.to_numeric(df[qty_cols[2]],errors='coerce'), 'Tồn cuối kỳ':pd.to_numeric(df[qty_cols[3]],errors='coerce')})
    return out.dropna(subset=['Mã SKU'])

def load_table(name):
    with conn() as c:
        return pd.read_sql_query(f'SELECT * FROM {name}', c)

def save_snapshot(df, name, days, report_end):
    rows=[]
    now=datetime.now().isoformat(timespec='seconds')
    for _,r in df.iterrows():
        rows.append((now,name,int(days),str(report_end),str(r['Mã SKU']),str(r['Tên hàng hóa']),str(r['NHÓM HÀNG HÓA']),
                     float(r['Tồn đầu kỳ']),float(r['Nhập trong kỳ']),float(r['Xuất trong kỳ']),float(r['Tồn cuối kỳ']),float(r['Xuất trong kỳ'])/days))
    with conn() as c:
        c.executemany('''INSERT INTO snapshots(upload_time,report_name,report_days,report_end,sku,product_name,product_group,opening,receipts,outbound,ending,daily_sales)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',rows)

def weighted_forecast(sku, fallback):
    hist=load_table('snapshots')
    h=hist[hist['sku']==sku].sort_values(['report_end','id'],ascending=False).head(8)
    if h.empty: return fallback
    vals=h['daily_sales'].astype(float).to_numpy()
    # Exponential recency weighting: newest observations carry most weight.
    weights=np.array([0.72**i for i in range(len(vals))])
    return float(np.average(vals,weights=weights))

def open_po_by_sku():
    po=load_table('purchase_orders')
    if po.empty: return {},{}
    active=po[~po['status'].isin(['Đã nhận','Đã hủy'])].copy()
    qty=active.groupby('sku')['qty'].sum().to_dict() if not active.empty else {}
    eta={}
    for sku,g in active.groupby('sku'):
        valid=pd.to_datetime(g['eta'],errors='coerce').dropna()
        eta[sku]=valid.min().date() if len(valid) else None
    return qty,eta

# ---------- Navigation ----------
page=st.sidebar.radio('Chức năng',['📊 Kế hoạch đặt hàng','📤 Upload XNT','🚢 Đơn hàng nhập','⚙️ Chính sách SKU','🕘 Lịch sử'])

if page=='📤 Upload XNT':
    st.header('Upload báo cáo XNT')
    uploaded=st.file_uploader('File XNT (.xlsx)',type=['xlsx'])
    c1,c2=st.columns(2)
    report_days=c1.number_input('Số ngày XNT của file',1,366,7,help='Nhập đúng số ngày dữ liệu thực tế trong file.')
    report_end=c2.date_input('Ngày cuối kỳ báo cáo',value=date.today())
    if uploaded:
        try:
            base=normalize_source(uploaded)
            for col in ['Tồn đầu kỳ','Nhập trong kỳ','Xuất trong kỳ','Tồn cuối kỳ']:
                base[col]=pd.to_numeric(base[col],errors='coerce').fillna(0)
            st.dataframe(base,use_container_width=True,height=420)
            if st.button('💾 Lưu XNT vào lịch sử',type='primary'):
                save_snapshot(base,uploaded.name,report_days,report_end)
                st.success(f'Đã lưu {len(base)} SKU vào lịch sử. Forecast sẽ ưu tiên dữ liệu gần nhất.')
        except Exception as e: st.error(str(e))
    else: st.info('Chọn file XNT và khai báo số ngày dữ liệu của file.')

elif page=='🚢 Đơn hàng nhập':
    st.header('Đơn hàng nhập / Hàng đang đặt')
    with st.form('po_form',clear_on_submit=True):
        a,b,c=st.columns(3)
        po_code=a.text_input('Mã PO',value=f'PO-{date.today():%Y%m%d}-')
        supplier=b.text_input('Nhà cung cấp')
        sku=c.text_input('Mã SKU')
        a,b,c=st.columns(3)
        qty=a.number_input('Số lượng',min_value=0.0,step=1.0)
        unit_price=b.number_input('Giá trị 1 sản phẩm',min_value=0.0,step=1000.0)
        unit_weight=c.number_input('Khối lượng 1 sản phẩm (kg)',min_value=0.0,step=0.1)
        a,b,c=st.columns(3)
        order_date=a.date_input('Ngày đặt hàng',value=date.today())
        eta=b.date_input('Ngày dự kiến về kho VN',value=date.today()+timedelta(days=30))
        status=c.selectbox('Trạng thái',['Đang sản xuất','Đang vận chuyển','Sắp nhận','Đã nhận','Đã hủy'])
        a,b,c,d=st.columns(4)
        freight=a.number_input('Vận chuyển',min_value=0.0,step=100000.0)
        customs=b.number_input('Hải quan/thuế phí',min_value=0.0,step=100000.0)
        other=c.number_input('Chi phí khác',min_value=0.0,step=100000.0)
        allocation=d.selectbox('Phân bổ chi phí',['Theo giá trị','Theo số lượng','Theo khối lượng'])
        submitted=st.form_submit_button('➕ Lưu đơn hàng',type='primary')
        if submitted:
            if not po_code or not sku or qty<=0: st.error('Cần nhập Mã PO, Mã SKU và số lượng > 0.')
            else:
                with conn() as cx:
                    cx.execute('''INSERT INTO purchase_orders(po_code,supplier,sku,qty,unit_price,unit_weight,order_date,eta,status,freight,customs,other_cost,allocation_method,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(po_code,supplier,sku,qty,unit_price,unit_weight,str(order_date),str(eta),status,freight,customs,other,allocation,datetime.now().isoformat(timespec='seconds')))
                st.success('Đã lưu đơn hàng nhập.')
    po=load_table('purchase_orders')
    if not po.empty:
        po['Giá trị hàng']=po['qty']*po['unit_price']; po['Tổng kg']=po['qty']*po['unit_weight']
        po['Tổng chi phí']=po['freight']+po['customs']+po['other_cost']; po['Tổng tiền PO']=po['Giá trị hàng']+po['Tổng chi phí']
        po['Landed cost/SP']=np.where(po['qty']>0,po['Tổng tiền PO']/po['qty'],0)
        st.dataframe(po[['po_code','supplier','sku','qty','unit_price','Tổng kg','eta','status','allocation_method','Tổng tiền PO','Landed cost/SP']],use_container_width=True)

elif page=='⚙️ Chính sách SKU':
    st.header('Chính sách tồn kho theo SKU')
    st.caption('N = Lead time sản xuất + vận chuyển về kho VN. Target = N + số ngày tồn mục tiêu sau khi hàng về.')
    with st.form('policy'):
        a,b,c,d,e=st.columns(5)
        sku=a.text_input('Mã SKU')
        lead=b.number_input('Lead time N (ngày)',1,365,30)
        target=c.number_input('Tồn mục tiêu sau khi về (ngày)',1,180,30)
        pack=d.number_input('Quy cách đóng gói (SP)',1,100000,1)
        supplier=e.text_input('NCC mặc định')
        if st.form_submit_button('💾 Lưu chính sách',type='primary'):
            if sku:
                with conn() as cx:
                    cx.execute('''INSERT INTO sku_policy(sku,lead_time,target_after_arrival,pack_size,supplier) VALUES(?,?,?,?,?)
                    ON CONFLICT(sku) DO UPDATE SET lead_time=excluded.lead_time,target_after_arrival=excluded.target_after_arrival,pack_size=excluded.pack_size,supplier=excluded.supplier''',(sku,lead,target,pack,supplier))
                st.success('Đã lưu chính sách SKU.')
    pol=load_table('sku_policy')
    st.dataframe(pol,use_container_width=True)

elif page=='🕘 Lịch sử':
    st.header('Lịch sử XNT')
    hist=load_table('snapshots')
    if hist.empty: st.info('Chưa có dữ liệu lịch sử.')
    else:
        st.metric('Số bản ghi lịch sử',len(hist))
        st.dataframe(hist.sort_values('id',ascending=False),use_container_width=True,height=520)

else:
    st.header('Kế hoạch đặt hàng & Dashboard')
    hist=load_table('snapshots')
    if hist.empty:
        st.warning('Chưa có XNT đã lưu. Dashboard đang dùng dữ liệu DEMO. Hãy vào Upload XNT để tạo lịch sử thật.')
        base=demo_data(); report_end=date.today()
    else:
        # latest row per SKU by report_end/id
        hist['report_end_dt']=pd.to_datetime(hist['report_end'],errors='coerce')
        latest=hist.sort_values(['report_end_dt','id']).groupby('sku').tail(1)
        base=pd.DataFrame({'NHÓM HÀNG HÓA':latest['product_group'],'Mã SKU':latest['sku'],'Tên hàng hóa':latest['product_name'],
            'Tồn đầu kỳ':latest['opening'],'Nhập trong kỳ':latest['receipts'],'Xuất trong kỳ':latest['outbound'],'Tồn cuối kỳ':latest['ending']})
        report_end=latest['report_end_dt'].max().date() if latest['report_end_dt'].notna().any() else date.today()
    for col in ['Tồn đầu kỳ','Nhập trong kỳ','Xuất trong kỳ','Tồn cuối kỳ']:
        base[col]=pd.to_numeric(base[col],errors='coerce').fillna(0)
    policies=load_table('sku_policy').set_index('sku') if not load_table('sku_policy').empty else pd.DataFrame()
    po_qty,po_eta=open_po_by_sku()
    rows=[]
    for _,r in base.iterrows():
        sku=str(r['Mã SKU']); current=float(r['Tồn cuối kỳ'])
        fallback=float(r['Xuất trong kỳ'])/7 if float(r['Xuất trong kỳ'])>0 else 0
        daily=weighted_forecast(sku,fallback)
        lead=int(policies.loc[sku,'lead_time']) if not policies.empty and sku in policies.index else 30
        target_days=int(policies.loc[sku,'target_after_arrival']) if not policies.empty and sku in policies.index else 30
        pack=int(policies.loc[sku,'pack_size']) if not policies.empty and sku in policies.index else 1
        incoming=float(po_qty.get(sku,0)); eta=po_eta.get(sku)
        reorder=math.ceil(daily*lead)
        target=math.ceil(daily*(lead+target_days))
        inv_position=current+incoming
        suggested=max(0,target-inv_position)
        rounded=int(math.ceil(suggested/pack)*pack) if suggested>0 and pack>0 else 0
        days_cover=current/daily if daily>0 else 999
        stockout=(report_end+timedelta(days=math.floor(days_cover))) if daily>0 else None
        gap=0
        if eta and stockout: gap=max(0,(eta-stockout).days)
        days_left_month=(date(report_end.year,report_end.month+1,1)-report_end).days if report_end.month<12 else (date(report_end.year+1,1,1)-report_end).days
        demand_rest_month=math.ceil(daily*max(days_left_month-1,0))
        if current<=reorder: status='🔴 ĐẶT HÀNG NGAY'
        elif current<=math.ceil(reorder*1.2): status='🟠 CHUẨN BỊ ĐẶT'
        elif gap>0: status='🟡 PO VỀ SAU STOCKOUT'
        elif current>target*1.5 and target>0: status='🔵 DƯ TỒN'
        else: status='🟢 ĐỦ HÀNG'
        rows.append([r['NHÓM HÀNG HÓA'],sku,r['Tên hàng hóa'],current,daily,days_cover,lead,reorder,incoming,eta,demand_rest_month,target,suggested,pack,rounded,stockout,gap,status])
    plan=pd.DataFrame(rows,columns=['Nhóm','SKU','Tên hàng','Tồn hiện tại','Forecast bán/ngày','Ngày còn hàng','Lead time N','Ngưỡng đặt hàng','Hàng đang đặt','ETA gần nhất','Dự kiến bán còn lại tháng','Target (N + ngày tồn mục tiêu)','SL cần đặt','Quy cách','PO làm tròn','Dự kiến hết hàng','Số ngày thiếu trước ETA','Trạng thái'])
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric('Tổng SKU',len(plan)); c2.metric('Cần đặt ngay',int(plan['Trạng thái'].str.contains('ĐẶT HÀNG').sum()))
    c3.metric('Nguy cơ PO về trễ',int((plan['Số ngày thiếu trước ETA']>0).sum())); c4.metric('Tổng SL PO đề xuất',f"{plan['PO làm tròn'].sum():,.0f}")
    c5.metric('Hàng đang đặt',f"{plan['Hàng đang đặt'].sum():,.0f}")
    st.subheader('🚦 Danh sách ưu tiên')
    st.dataframe(plan.sort_values(['Số ngày thiếu trước ETA','Ngày còn hàng'],ascending=[False,True]),use_container_width=True,height=520,
        column_config={'Forecast bán/ngày':st.column_config.NumberColumn(format='%.2f'),'Ngày còn hàng':st.column_config.NumberColumn(format='%.1f')})
    st.subheader('Top SKU cần nhập')
    st.bar_chart(plan.nlargest(10,'PO làm tròn').set_index('SKU')[['PO làm tròn']])
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine='openpyxl') as w: plan.to_excel(w,index=False,sheet_name='Ke_hoach_V2')
    st.download_button('⬇️ Xuất kế hoạch V2',buf.getvalue(),'NEFA_Ke_hoach_nhap_hang_V2.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')
    with st.expander('Công thức V2 đang áp dụng'):
        st.markdown('''- **Weighted Forecast:** ưu tiên tốc độ bán của các kỳ gần nhất (tối đa 8 kỳ đã lưu).\n- **Inventory Position:** Tồn hiện tại + PO/hàng chưa nhận.\n- **Reorder Point:** Forecast bán/ngày × Lead time N.\n- **Target Stock:** Forecast bán/ngày × (N + số ngày tồn mục tiêu sau khi hàng về).\n- **Suggested PO:** MAX(Target Stock − Inventory Position, 0).\n- **PO làm tròn:** làm tròn lên theo quy cách đóng gói.\n- **Days of Cover:** Tồn hiện tại ÷ Forecast bán/ngày.\n- ETA được so với ngày dự kiến hết hàng để cảnh báo khoảng thiếu hàng.''')
