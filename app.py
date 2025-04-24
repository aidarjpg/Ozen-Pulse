import streamlit as st
import pandas as pd
import plotly.express as px

# === ОБЯЗАТЕЛЬНО ПЕРВОЕ ===
st.set_page_config(page_title="Ozen Pulse Dashboard", layout="wide")

@st.cache_data
def load_data():
    clients = pd.read_csv("clients.csv", sep=",", encoding="utf-8-sig")
    sales = pd.read_csv("sales.csv", sep=",", encoding="utf-8-sig")
    visits = pd.read_csv("visits.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    subs = pd.read_csv("subscriptions.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    complaints = pd.read_csv("complaints.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    staff = pd.read_csv("staff_movements.csv", sep=",", encoding="utf-8-sig", dayfirst=True)
    trainers = pd.read_csv("trainers.csv", sep=",", encoding="utf-8-sig")
    visits["Дата и время"] = pd.to_datetime(visits["Дата и время"], dayfirst=True)
    subs["Дата начала"]     = pd.to_datetime(subs["Дата начала"], dayfirst=True)
    complaints["Дата"]     = pd.to_datetime(complaints["Дата"], dayfirst=True)
    staff["Дата приема"]    = pd.to_datetime(staff["Дата приема"], dayfirst=True)
    staff["Дата увольнения"]= pd.to_datetime(staff["Дата увольнения"], dayfirst=True, errors="coerce")
    return clients, sales, visits, subs, complaints, staff, trainers

clients, sales, visits, subs, complaints, staff, trainers = load_data()

# --- Логотип в сайдбаре ---
st.sidebar.image("___1.svg", width=200)

# Заголовок
st.title("Ozen Pulse")
st.markdown("**Пульс твоего прогресса**")

# Фильтр по дате посещений
min_date = st.sidebar.date_input("Дата от", visits["Дата и время"].min())
max_date = st.sidebar.date_input("Дата до", visits["Дата и время"].max())
visits_filt = visits[
    (visits["Дата и время"] >= pd.to_datetime(min_date)) &
    (visits["Дата и время"] <= pd.to_datetime(max_date))
]

# KPI
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Всего клиентов", clients.shape[0])
col2.metric("Общая выручка, ₽", int(sales["Сумма"].sum()))
col3.metric("Визитов/клиент", round(visits_filt.shape[0] / clients.shape[0], 2))
turnover = staff["Дата увольнения"].notna().sum() / trainers.shape[0] * 100
col4.metric("Текучесть тренеров, %", f"{turnover:.1f}%")
col5.metric("Жалоб всего", complaints.shape[0])
col6.metric("Клиенты с заморозками", subs[subs["Количество заморозок"] > 0].shape[0])

# 1. Продажи
st.subheader("Продажи по типу продукта")
df_sales = sales["Тип продукта"].value_counts().reset_index()
df_sales.columns = ["Продукт", "Число продаж"]
fig1 = px.bar(df_sales, x="Продукт", y="Число продаж",
              color_discrete_sequence=["#1890ff"])
st.plotly_chart(fig1, use_container_width=True)

# 2. Посещения по дням недели (исправлено)
st.subheader("Посещения по дням недели")
# Группируем по номеру дня [0=Пн … 6=Вс]
visits_filt["weekday"] = visits_filt["Дата и время"].dt.weekday
weekday_map = {0:"Пн",1:"Вт",2:"Ср",3:"Чт",4:"Пт",5:"Сб",6:"Вс"}
visits_by_day = visits_filt.groupby("weekday").size().reindex(range(7), fill_value=0)
df_act = pd.DataFrame({
    "День недели": [weekday_map[i] for i in visits_by_day.index],
    "Визиты": visits_by_day.values
})
fig2 = px.bar(df_act, x="День недели", y="Визиты",
              color_discrete_sequence=["#1890ff"])
st.plotly_chart(fig2, use_container_width=True)

# 3. Пол клиентов
st.subheader("Распределение клиентов по полу")
fig3 = px.pie(clients, names="Пол",
              color_discrete_sequence=["#1890ff","#ff7a45"])
st.plotly_chart(fig3, use_container_width=True)

# 4. Возраст
st.subheader("Распределение по возрастным группам")
bins = [18,26,36,46,61,71]
labels = ["18-25","26-35","36-45","46-60","61-70"]
clients["AgeGroup"] = pd.cut(clients["Возраст"], bins=bins, labels=labels, right=False)
df_age = clients["AgeGroup"].value_counts().sort_index().reset_index()
df_age.columns = ["Возрастная группа","Число клиентов"]
fig4 = px.bar(df_age, x="Возрастная группа", y="Число клиентов",
              color_discrete_sequence=["#1890ff"])
st.plotly_chart(fig4, use_container_width=True)

# 5. KPI тренеров
st.subheader("KPI тренеров")
rev = sales.groupby("ID тренера")["Сумма"].sum().reset_index(name="Доход")
clu = sales.groupby("ID тренера")["ID клиента"].nunique().reset_index(name="Уник. клиентов")
df_tr = rev.merge(clu, on="ID тренера")
fig5 = px.bar(df_tr, x="ID тренера", y=["Доход","Уник. клиентов"], 
              barmode="group", color_discrete_sequence=["#1890ff","#ff7a45"])
st.plotly_chart(fig5, use_container_width=True)

# 6. Заморозки
st.subheader("Заморозки абонементов по месяцам")
subs["Месяц"] = subs["Дата начала"].dt.to_period("M").astype(str)
df_sub = subs.groupby("Месяц")["Количество заморозок"].sum().reset_index()
fig6 = px.bar(df_sub, x="Месяц", y="Количество заморозок",
              color_discrete_sequence=["#ff7a45"])
st.plotly_chart(fig6, use_container_width=True)
