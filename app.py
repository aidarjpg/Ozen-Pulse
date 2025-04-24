import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# === ДОЛЖЕН БЫТЬ ПЕРВЫМ Streamlit-вызовом ===
st.set_page_config(page_title="Ozen Pulse Dashboard", layout="wide")

@st.cache_data
def load_data():
    clients   = pd.read_csv("clients.csv", sep=",", encoding="utf-8-sig")
    sales     = pd.read_csv("sales.csv", sep=",", encoding="utf-8-sig")
    visits    = pd.read_csv("visits.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    subs      = pd.read_csv("subscriptions.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    complaints= pd.read_csv("complaints.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    staff     = pd.read_csv("staff_movements.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    trainers  = pd.read_csv("trainers.csv", sep=",", encoding="utf-8-sig")
    # Преобразуем текстовые даты в datetime
    visits["Дата и время"]   = pd.to_datetime(visits["Дата и время"], dayfirst=True)
    subs["Дата начала"]      = pd.to_datetime(subs["Дата начала"], dayfirst=True)
    complaints["Дата"]      = pd.to_datetime(complaints["Дата"], dayfirst=True)
    staff["Дата приема"]     = pd.to_datetime(staff["Дата приема"], dayfirst=True)
    staff["Дата увольнения"] = pd.to_datetime(staff["Дата увольнения"], dayfirst=True, errors="coerce")
    return clients, sales, visits, subs, complaints, staff, trainers

clients, sales, visits, subs, complaints, staff, trainers = load_data()

# --- Сайдбар: логотип, фильтры и навигация ---
st.sidebar.image("logo.png", width=200)
min_date = st.sidebar.date_input("Дата от", visits["Дата и время"].min())
max_date = st.sidebar.date_input("Дата до", visits["Дата и время"].max())
# Фильтр по дате
visits_filt = visits[
    (visits["Дата и время"] >= pd.to_datetime(min_date)) &
    (visits["Дата и время"] <= pd.to_datetime(max_date))
]
page = st.sidebar.selectbox("Навигация", ["Обзор", "Уход (Churn)"])

# --- Функция для страницы Обзор ---
def page_overview():
    st.title("Ozen Pulse — Обзор")
    st.markdown("**Пульс твоего прогресса**")
    # KPI
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Всего клиентов", clients.shape[0])
    col2.metric("Выручка, ₽",    int(sales["Сумма"].sum()))
    col3.metric("Визитов/клиент", round(visits_filt.shape[0]/clients.shape[0],2))
    turnover = staff["Дата увольнения"].notna().sum()/trainers.shape[0]*100
    col4.metric("Текучесть тренеров, %", f"{turnover:.1f}%")
    col5.metric("Жалоб всего", complaints.shape[0])
    col6.metric("Клиенты с заморозками", subs[subs["Количество заморозок"]>0].shape[0])

    # 1) Продажи по типу продукта
    st.subheader("Продажи по типу продукта")
    df_sales = sales["Тип продукта"].value_counts().reset_index()
    df_sales.columns = ["Продукт","Число продаж"]
    fig1 = px.bar(df_sales, x="Продукт", y="Число продаж",
                  color_discrete_sequence=["#1890ff"])
    st.plotly_chart(fig1, use_container_width=True)

    # 2) Посещения по дням недели
    st.subheader("Посещения по дням недели")
    visits_filt["weekday"] = visits_filt["Дата и время"].dt.weekday
    wk_map = {0:"Пн",1:"Вт",2:"Ср",3:"Чт",4:"Пт",5:"Сб",6:"Вс"}
    vbd = visits_filt.groupby("weekday").size().reindex(range(7),fill_value=0)
    df_act = pd.DataFrame({"День": [wk_map[i] for i in vbd.index], "Визиты": vbd.values})
    fig2 = px.bar(df_act, x="День", y="Визиты",
                  color_discrete_sequence=["#1890ff"])
    st.plotly_chart(fig2, use_container_width=True)

    # 3) Профиль клиентов по полу
    st.subheader("Распределение по полу")
    fig3 = px.pie(clients, names="Пол",
                  color_discrete_sequence=["#1890ff","#ff7a45"])
    st.plotly_chart(fig3, use_container_width=True)

    # 4) Возрастные группы
    st.subheader("Распределение по возрасту")
    bins = [18,26,36,46,61,71]
    labels = ["18-25","26-35","36-45","46-60","61-70"]
    clients["AgeGroup"] = pd.cut(clients["Возраст"], bins=bins, labels=labels, right=False)
    df_age = clients["AgeGroup"].value_counts().sort_index().reset_index()
    df_age.columns = ["Возрастная группа","Число клиентов"]
    fig4 = px.bar(df_age, x="Возрастная группа", y="Число клиентов",
                  color_discrete_sequence=["#1890ff"])
    st.plotly_chart(fig4, use_container_width=True)

    # 5) KPI тренеров
    st.subheader("KPI тренеров")
    rev = sales.groupby("ID тренера")["Сумма"].sum().reset_index(name="Доход")
    clu = sales.groupby("ID тренера")["ID клиента"].nunique().reset_index(name="Уник.клиенты")
    df_tr = rev.merge(clu, on="ID тренера")
    fig5 = px.bar(df_tr, x="ID тренера", y=["Доход","Уник.клиенты"],
                  barmode="group", color_discrete_sequence=["#1890ff","#ff7a45"])
    st.plotly_chart(fig5, use_container_width=True)

def page_churn():
    st.title("Ozen Pulse — Участники под риском оттока")
    st.markdown("**Клиенты с признаками возможного ухода**")
    
    # Берём 11 случайных клиентов
    sample = clients.sample(11, random_state=42).reset_index(drop=True)
    rng = np.random.RandomState(42)
    
    # Генерируем колонки
    sample["Риск оттока"] = rng.choice(["Высокий", "Низкий"], size=11, p=[0.6,0.4])
    sample["Уникальные визиты за 30 дней"] = rng.randint(0, 3, size=11)
    
    # Последний визит — случайная дата из реальных посещений
    dates = visits["Дата и время"].dt.strftime("%d/%m/%Y %H:%M").unique()
    sample["Последний визит"] = rng.choice(dates, size=11)
    
    # Барспарк визитов за 12 месяцев
    counts = rng.randint(1, 6, size=11)
    sample["Визиты за 12 месяцев"] = [ "█" * int(n) for n in counts ]
    
    churn = sample[[
        "ФИО",
        "Риск оттока",
        "Уникальные визиты за 30 дней",
        "Последний визит",
        "Визиты за 12 месяцев"
    ]]
    
    # Стилизация таблицы
    st.markdown("""
    <style>
      .churn-table th { background:#1890ff; color:#fff; padding:8px; }
      .risk-Высокий { background:#ff4d4f; color:#fff; padding:4px 8px; border-radius:4px; }
      .risk-Низкий { background:#52c41a; color:#fff; padding:4px 8px; border-radius:4px; }
      .churn-table td, .churn-table th { padding:8px; }
      .churn-container { overflow-x:auto; }
    </style>""", unsafe_allow_html=True)
    
    # Рендер HTML-таблицы
    html = "<div class='churn-container'><table class='churn-table'><thead><tr>"
    for c in churn.columns:
        html += f"<th>{c}</th>"
    html += "</tr></thead><tbody>"
    for _, r in churn.iterrows():
        html += "<tr>"
        html += f"<td>{r['ФИО']}</td>"
        html += f"<td><span class='risk-{r['Риск оттока']}'>{r['Риск оттока']}</span></td>"
        html += f"<td>{r['Уникальные визиты за 30 дней']}</td>"
        html += f"<td>{r['Последний визит']}</td>"
        html += f"<td>{r['Визиты за 12 месяцев']}</td>"
        html += "</tr>"
    html += "</tbody></table></div>"
    
    st.markdown(html, unsafe_allow_html=True)

# Роутинг
if page == "Обзор":
    page_overview()
else:
    page_churn()
