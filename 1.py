import streamlit as st
import pandas as pd
import io
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 0. PDF 한글 폰트 설정 ---
try:
    font_path = malgun.ttf"
    pdfmetrics.registerFont(TTFont('Malgun', font_path))
    pdf_font = 'Malgun'
except:
    pdf_font = 'Helvetica'

# --- 1. 전체 노무제공자 데이터 베이스 ---
NOMU_RATES_2026 = {
    "보험설계사": {"expense_rate": 0.234, "ind_rate": 0.0056, "code": "51"},
    "골프장캐디": {"expense_rate": 0.238, "ind_rate": 0.0056, "code": "52"},
    "학습지·방문강사": {"expense_rate": 0.234, "ind_rate": 0.0076, "code": "53"},
    "건설기계조종사": {"expense_rate": 0.274, "ind_rate": 0.0346, "code": "54"},
    "택배기사": {"expense_rate": 0.239, "ind_rate": 0.0176, "code": "55"},
    "퀵서비스기사(배달)": {"expense_rate": 0.198, "ind_rate": 0.0176, "code": "56"},
    "대출모집인": {"expense_rate": 0.243, "ind_rate": 0.0056, "code": "57"},
    "신용카드모집인": {"expense_rate": 0.239, "ind_rate": 0.0056, "code": "58"},
    "대리운전기사": {"expense_rate": 0.214, "ind_rate": 0.0186, "code": "59"},
    "방문판매원": {"expense_rate": 0.265, "ind_rate": 0.0086, "code": "60"},
    "대여제품방문점검원": {"expense_rate": 0.265, "ind_rate": 0.0076, "code": "61"},
    "가전제품배송설치기사": {"expense_rate": 0.265, "ind_rate": 0.0076, "code": "62"},
    "방과후학교강사": {"expense_rate": 0.199, "ind_rate": 0.0066, "code": "63"},
    "소프트웨어기술자": {"expense_rate": 0.157, "ind_rate": 0.0056, "code": "64"},
    "화물차주": {"expense_rate": 0.300, "ind_rate": 0.0176, "code": "65"},
    "관광통역안내사": {"expense_rate": 0.157, "ind_rate": 0.0066, "code": "66"},
    "어린이통학버스기사": {"expense_rate": 0.214, "ind_rate": 0.0186, "code": "67"}
}
JOB_LIST = list(NOMU_RATES_2026.keys())

# --- 2. 실지급액 계산 로직 ---
def calculate_net_pay(gross_pay, expense_rate, ind_rate):
    if pd.isna(gross_pay) or gross_pay <= 0: return 0, 0, 0, 0, 0
    insurance_base = gross_pay * (1 - expense_rate)
    emp_insurance = int(insurance_base * 0.008) // 10 * 10
    ind_insurance = int(insurance_base * (ind_rate / 2)) // 10 * 10
    income_tax = int(gross_pay * 0.03) // 10 * 10
    local_tax = int(income_tax * 0.1) // 10 * 10
    net_pay = gross_pay - emp_insurance - ind_insurance - income_tax - local_tax
    return net_pay, emp_insurance, ind_insurance, income_tax, local_tax

# --- 3. PDF 명세서 생성 로직 ---
def generate_pdf(name, rrn, job_type, gross, net, emp, ind, inc, loc):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A5) 
    width, height = A5
    
    c.setFont(pdf_font, 18)
    c.drawCentredString(width/2, height - 50, "노무제공자 실지급액 명세서")
    
    c.setFont(pdf_font, 10)
    c.drawString(40, height - 100, f"성명 : {name}")
    c.drawString(40, height - 120, f"주민등록번호 : {rrn}")
    c.drawString(40, height - 140, f"직종 : {job_type}")
    c.line(40, height - 160, width - 40, height - 160)
    
    c.setFont(pdf_font, 12)
    c.drawString(40, height - 190, "[지급 내역]")
    c.drawString(50, height - 215, f"총 보수액 : {int(gross):,} 원")
    
    c.drawString(40, height - 260, "[공제 내역]")
    c.setFont(pdf_font, 10)
    c.drawString(50, height - 285, f"고용보험료 (근로자분) : {int(emp):,} 원")
    c.drawString(50, height - 305, f"산재보험료 (종사자분) : {int(ind):,} 원")
    c.drawString(50, height - 325, f"사업소득세 (3%) : {int(inc):,} 원")
    c.drawString(50, height - 345, f"지방소득세 (0.3%) : {int(loc):,} 원")
    c.line(40, height - 370, width - 40, height - 370)
    
    c.setFont(pdf_font, 14)
    c.drawString(40, height - 400, f"▶ 차인지급액 (실지급액) : {int(net):,} 원")
    
    c.setFont(pdf_font, 12)
    c.drawCentredString(width/2, 50, "양 주 세 무 회 계")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 4. Streamlit UI 레이아웃 ---
st.set_page_config(page_title="양주세무회계 노무제공자 통합 관리", layout="wide")

st.title("📊 양주세무회계 - 노무제공자 통합 관리 시스템")
st.markdown("입력된 명단을 바탕으로 **실지급액 명세서(PDF) 발급**과 **사무대행기관 신고용 엑셀 추출**을 동시에 지원합니다.")

today = datetime.date.today()

# 데이터프레임 초기화 (통합 입력창)
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(
        columns=['사업장관리번호', '성명', '주민등록번호', '업종', '입사일(취득일)', '퇴사일(상실일)', '총보수액'],
        data=[['123-45-67890-0', '홍길동', '800101-1234567', '건설기계조종사', today, None, 3000000]] 
    )

st.subheader("1. 공통 데이터 입력 (엑셀 복사/붙여넣기)")
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    column_config={
        "사업장관리번호": st.column_config.TextColumn("사업장관리번호 (공단신고용)"),
        "업종": st.column_config.SelectboxColumn("업종", options=JOB_LIST, required=True),
        "입사일(취득일)": st.column_config.DateColumn("입사일(취득일)", format="YYYY-MM-DD"),
        "퇴사일(상실일)": st.column_config.DateColumn("퇴사일(상실일)", format="YYYY-MM-DD"),
        "총보수액": st.column_config.NumberColumn("월총보수액", min_value=0, step=10000, format="%d")
    },
    use_container_width=True
)

st.divider()

# --- 핵심: 탭(Tab) 분리를 통한 두 가지 작업 전환 ---
tab1, tab2 = st.tabs(["🧾 실지급액 명세서 (PDF) 보기", "📝 대행기관 일괄신고 (엑셀) 추출"])

# --- [탭 1] 개별 명세서 PDF 생성 ---
with tab1:
    st.markdown("#### 👤 대상자별 실지급액 계산 및 명세서 발급")
    
    if st.button("🚀 급여 계산 및 명세서(PDF) 전체 생성", type="primary"):
        pdf_cols = st.columns(3) 
        
        for idx, row in edited_df.iterrows():
            name = row.get('성명', '')
            rrn = row.get('주민등록번호', '')
            job = row.get('업종', '')
            gross = row.get('총보수액', 0)
            
            if pd.isna(job) or job == '' or pd.isna(gross) or gross <= 0:
                continue
                
            exp_rate = NOMU_RATES_2026[job]["expense_rate"]
            ind_rate = NOMU_RATES_2026[job]["ind_rate"]
            
            # 계산 및 PDF 생성
            net, emp, ind, inc, loc = calculate_net_pay(gross, exp_rate, ind_rate)
            pdf_file = generate_pdf(name, rrn, job, gross, net, emp, ind, inc, loc)
            
            # 3단 카드 형태로 출력
            with pdf_cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**{name}** ({job})")
                    st.write(f"실지급액: **<span style='color:blue'>{int(net):,}</span>** 원", unsafe_allow_html=True)
                    st.download_button(
                        label=f"📄 PDF 다운로드",
                        data=pdf_file,
                        file_name=f"명세서_{name}_{job}.pdf",
                        mime="application/pdf",
                        key=f"btn_pdf_{idx}"
                    )

# --- [탭 2] 공단 신고용 엑셀 다운로드 ---
with tab2:
    st.markdown("#### 🏢 근로복지공단 토탈서비스 업로드용 데이터")
    st.info("입력된 명단을 공단 일괄업로드 양식 순서로 자동 변환합니다.")
    
    output = io.BytesIO()
    
    # 공단 엑셀 양식 구조로 데이터 재배열
    edi_df = pd.DataFrame({
        '사업장관리번호': edited_df['사업장관리번호'],
        '주민등록번호': edited_df['주민등록번호'],
        '성명': edited_df['성명'],
        '직종부호': edited_df['업종'].map(lambda x: NOMU_RATES_2026.get(x, {}).get('code', '') if pd.notna(x) else ''),
        '취득일자(계약일)': edited_df['입사일(취득일)'].astype(str),
        '월평균보수액': edited_df['총보수액']
    })
    
    # 변환된 데이터 미리보기 제공
    st.dataframe(edi_df, use_container_width=True)
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edi_df.to_excel(writer, index=False, sheet_name='Sheet1')
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 토탈서비스 업로드 엑셀 다운로드",
        data=excel_data,
        file_name=f"일괄신고_{today.strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
