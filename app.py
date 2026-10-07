import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title='NEFA Inventory Planner', page_icon='📦', layout='wide')

st.markdown('''
<style>
.block-container{padding-top:1.4rem;max-width:1500px}
[data-testid="stMetric"]{background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:16px}
.hero{background:linear-gradient(120deg,#0f172a,#1e3a5f);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}
.hero h1{margin:0;font-size:30px}.hero p{margin:6px 0 0;color:#cbd5e1}
.redbox{background:#fee2e2;border-left:5px solid #dc2626;padding:12px;border-radius:8px}.greenbox{background:#dcfce7;border-left:5px solid #16a34a;padding:12px;border-radius:8px}
</style>
''', unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>NEFA Inventory Planner</h1><p>Upload báo cáo XNT → Forecast nhu cầu → Cảnh báo đặt hàng → Đề xuất số lượng nhập</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header('⚙️ Chính sách tồn kho')
    lead_time = st.number_input('Lead time TQ → VN (ngày)', 1, 180, 30)
    extra_safety = st.number_input('Safety stock bổ sung (ngày)', 0, 90, 0)
    report_days = st.number_input('Số ngày thực tế của báo cáo', 1, 31, 7, help='Prototype V1: mặc định 7 ngày. Có thể sửa khi kỳ báo cáo thay đổi.')
    st.caption('V1 dùng tốc độ xuất kho trung bình của kỳ báo cáo. Phiên bản sau có thể tự đọc ngày và dùng lịch sử 7D/30D/60D.')

uploaded = st.file_uploader('📤 Upload file xuất – nhập – tồn (.xlsx)', type=['xlsx'])

def demo_data():
    return pd.DataFrame([
        ['QUẠT THÔNG GIÓ NEFA','QTG.110','Quạt thông gió hút mùi Nefa HF100',0,45,45,0],
        ['QUẠT THÔNG GIÓ NEFA','QTG.125','Quạt thông gió hút mùi Nefa HF125',0,25,25,0],
        ['QUẠT THÔNG GIÓ NEFA','QTG.150','Quạt thông gió hút mùi Nefa HF150',3,282,283,2],
        ['QUẠT THÔNG GIÓ NEFA','QTG.200','Quạt thông gió hút mùi Nefa HF200',0,172,170,2],
        ['QUẠT THÔNG GIÓ NEFA','QTG.250','Quạt thông gió hút mùi Nefa HF250',0,16,16,0],
        ['QUẠT THÔNG GIÓ NEFA','QTG.300','Quạt thông gió hút mùi Nefa HF300',0,13,13,0],
        ['QUẠT INOX VUÔNG NEFA','QUẠT.HV.INOX.FD150','Quạt thông gió - hút mùi vuông Nefa - inox FD150',0,59,59,0],
        ['QUẠT INOX VUÔNG NEFA','QUAT.HV.FD200.INOX','Quạt thông gió - hút mùi vuông Nefa - inox FD200',0,19,19,0],
        ['QUẠT INOX VUÔNG NEFA','QUAT.HV.250.INOX','Quạt thông gió - hút mùi vuông Nefa - inox FD250',0,24,24,0],
        ['QUẠT INOX VUÔNG NEFA','QUAT.HV.FD300.INOX','Quạt thông gió - hút mùi vuông Nefa - inox FD300',0,20,19,1],
    ], columns=['NHÓM HÀNG HÓA','Mã SKU','Tên hàng hóa','Tồn đầu kỳ','Nhập trong kỳ','Xuất trong kỳ','Tồn cuối kỳ'])

def normalize_source(file):
    raw = pd.read_excel(file, header=None)
    # Find header row containing Mã SKU
    header_idx = None
    for i in range(min(len(raw), 30)):
        vals = raw.iloc[i].astype(str).str.strip().tolist()
        if any(v == 'Mã SKU' for v in vals):
            header_idx = i; break
    if header_idx is None:
        raise ValueError('Không tìm thấy dòng tiêu đề "Mã SKU" trong file.')
    df = pd.read_excel(file, header=header_idx)
    # flatten multiindex-like / unnamed columns heuristically
    df.columns = [str(c).strip() for c in df.columns]
    # Source export often has repeated metric labels; V1 attempts positional mapping.
    sku_col = next((c for c in df.columns if 'Mã SKU' in c), None)
    name_col = next((c for c in df.columns if 'Tên hàng hóa' in c), None)
    group_col = next((c for c in df.columns if 'Nhóm hàng hóa' in c), None)
    if not all([sku_col,name_col,group_col]): raise ValueError('Thiếu cột SKU/Tên hàng/Nhóm hàng.')
    # numeric columns after group: pairs of quantity/value. quantity positions 0,2,4,6...
    base = df.columns.get_loc(group_col)+1
    qty_cols = [df.columns[base+i] for i in [0,2,4,6] if base+i < len(df.columns)]
    if len(qty_cols)<4: raise ValueError('Không nhận diện đủ Tồn đầu/Nhập/Xuất/Tồn cuối.')
    out = pd.DataFrame({
        'NHÓM HÀNG HÓA':df[group_col], 'Mã SKU':df[sku_col], 'Tên hàng hóa':df[name_col],
        'Tồn đầu kỳ':pd.to_numeric(df[qty_cols[0]],errors='coerce'),
        'Nhập trong kỳ':pd.to_numeric(df[qty_cols[1]],errors='coerce'),
        'Xuất trong kỳ':pd.to_numeric(df[qty_cols[2]],errors='coerce'),
        'Tồn cuối kỳ':pd.to_numeric(df[qty_cols[3]],errors='coerce')})
    return out.dropna(subset=['Mã SKU'])

if uploaded:
    try:
        base = normalize_source(uploaded)
        st.success(f'Đã đọc {len(base)} SKU từ file {uploaded.name}')
    except Exception as e:
        st.error(f'Prototype chưa đọc được cấu trúc file này: {e}')
        st.info('Đang hiển thị dữ liệu demo để anh xem luồng giao diện.')
        base = demo_data()
else:
    st.info('Chưa upload file. Hệ thống đang chạy **DEMO** bằng dữ liệu NEFA mẫu để anh hình dung.')
    base = demo_data()

# Filter product groups in prototype
allowed=['QUẠT THÔNG GIÓ NEFA','QUẠT INOX VUÔNG NEFA']
base=base[base['NHÓM HÀNG HÓA'].isin(allowed)].copy()
for c in ['Tồn đầu kỳ','Nhập trong kỳ','Xuất trong kỳ','Tồn cuối kỳ']:
    base[c]=pd.to_numeric(base[c],errors='coerce').fillna(0)

base['Tồn kho thực tế']=base['Tồn đầu kỳ']+base['Nhập trong kỳ']-base['Xuất trong kỳ']
base['Bán TB/ngày']=base['Xuất trong kỳ']/report_days
base['Dự kiến bán 30 ngày']=np.ceil(base['Bán TB/ngày']*30).astype(int)
base['Định biên tồn kho an toàn']=np.ceil(base['Bán TB/ngày']*(lead_time+extra_safety)).astype(int)
base['Số ngày tồn còn lại']=np.where(base['Bán TB/ngày']>0,base['Tồn kho thực tế']/base['Bán TB/ngày'],999)
base['SL đề xuất nhập hàng']=np.maximum(0,base['Định biên tồn kho an toàn']-base['Tồn kho thực tế']).astype(int)
base['Cảnh báo']=np.where(base['Tồn kho thực tế']<=base['Định biên tồn kho an toàn'],'🔴 ĐẶT HÀNG NGAY','🟢 ĐỦ TỒN')

c1,c2,c3,c4=st.columns(4)
c1.metric('SKU đang theo dõi',len(base))
c2.metric('SKU cần đặt ngay',int((base['Cảnh báo']=='🔴 ĐẶT HÀNG NGAY').sum()))
c3.metric('Tổng SL đề xuất nhập',f"{base['SL đề xuất nhập hàng'].sum():,.0f}")
c4.metric('Lead time đang áp dụng',f'{lead_time} ngày')

st.subheader('🚦 Cảnh báo mua hàng')
show_cols=['NHÓM HÀNG HÓA','Mã SKU','Tên hàng hóa','Tồn kho thực tế','Bán TB/ngày','Dự kiến bán 30 ngày','Định biên tồn kho an toàn','SL đề xuất nhập hàng','Cảnh báo']

def style_table(df):
    return (df.style
        .format({'Bán TB/ngày':'{:.2f}','Tồn kho thực tế':'{:,.0f}','Dự kiến bán 30 ngày':'{:,.0f}','Định biên tồn kho an toàn':'{:,.0f}','SL đề xuất nhập hàng':'{:,.0f}'})
        .map(lambda x:'background-color:#fecaca;color:#991b1b;font-weight:700' if isinstance(x,str) and 'ĐẶT HÀNG' in x else '', subset=['Cảnh báo'])
        .map(lambda x:'background-color:#fee2e2;color:#991b1b;font-weight:700', subset=['Định biên tồn kho an toàn'])
        .map(lambda x:'background-color:#dcfce7;color:#166534;font-weight:700', subset=['SL đề xuất nhập hàng']))

st.dataframe(style_table(base[show_cols]), use_container_width=True, height=430)

left,right=st.columns([1,1])
with left:
    st.markdown('<div class="redbox"><b>🔴 Định biên tồn kho</b><br>Nhu cầu dự kiến trong toàn bộ thời gian chờ hàng từ NCC. Với chính sách hiện tại = tốc độ bán/ngày × 30 ngày.</div>',unsafe_allow_html=True)
with right:
    st.markdown('<div class="greenbox"><b>🟢 Số lượng đề xuất nhập</b><br>Số lượng cần bổ sung để đưa tồn kho trở lại mức định biên theo chính sách đã chốt.</div>',unsafe_allow_html=True)

st.subheader('📊 SKU cần ưu tiên')
chart=base.nlargest(8,'SL đề xuất nhập hàng').set_index('Mã SKU')[['SL đề xuất nhập hàng']]
st.bar_chart(chart)

# Export management output
buf=BytesIO()
with pd.ExcelWriter(buf,engine='openpyxl') as writer:
    base.to_excel(writer,index=False,sheet_name='Ke_hoach_nhap_hang')
st.download_button('⬇️ Xuất Excel kế hoạch nhập hàng',buf.getvalue(),'NEFA_Ke_hoach_nhap_hang.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')

with st.expander('Xem quy tắc hệ thống đang áp dụng'):
    st.markdown(f'''**1.** Bán TB/ngày = Xuất trong kỳ ÷ **{report_days} ngày thực tế**  
**2.** Dự kiến bán 30 ngày = Bán TB/ngày × 30  
**3.** Lead time NCC = **{lead_time} ngày**  
**4.** Safety stock cộng thêm = **{extra_safety} ngày**  
**5.** Định biên = Bán TB/ngày × ({lead_time} + {extra_safety})  
**6.** SL đề xuất nhập = MAX(Định biên − Tồn thực tế, 0)  
**7.** Tồn ≤ Định biên → **ĐẶT HÀNG NGAY**''')
