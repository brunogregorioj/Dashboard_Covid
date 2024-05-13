# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import altair as alt


@st.cache(allow_output_mutation=True)
def get_df(type, by="global"):
    path = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{type}_{by}.csv'
    df = pd.read_csv(path)
    return get_country_df(df, type)


def get_country_df(df, type):
    cols = ["Lat", "Long", "Province/State"]
    df = df.drop(columns=cols).rename(columns={"Country/Region": "country"})

    if "date" not in df.columns:
        raise KeyError("Column 'date' not found in DataFrame.")

    df["country"] = df["country"].replace({"US": "United States", "Korea, South": "South Korea"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby(["country", "date"]).sum().reset_index()
    df[f"daily_{type}"] = df.groupby("country")[f"total_{type}"].diff().fillna(0).clip(lower=0)
    return df


def days_since(df, col, num=100, groupby="Paises"):
    df["days_since"] = df.assign(t=df[col] >= num).groupby(groupby)["t"].cumsum()
    return df[df["days_since"] > 0]


def chart(df, y, title, color="country"):
    return (
        alt.Chart(df, width=750, height=500)
        .mark_line(point=True)
        .encode(
            x=alt.X('days_since', axis=alt.Axis(format='', title='Dias desde')),
            y=alt.Y(y, axis=alt.Axis(format='', title=title)),
            color=color,
            tooltip=[alt.Tooltip(color), alt.Tooltip(y, format=",")],
        )
        .interactive()
    )


def main():
    by ='country'
    confirmed_df = get_df("confirmed", "global")
    deaths_df = get_df("deaths", "global")

    escolha = {"Cumulativo": "Cumulative", "Diário": "Daily"}
    chart_type = st.radio("Escolha o tipo de gráfico:", ["Cumulativo", "Diário"])
    chart_type = escolha[chart_type]

    num_confirmed = st.text_input("Número de Confirmados:", 100)
    confirmed_since_df = days_since(
        confirmed_df, "total_confirmed", num=int(num_confirmed), groupby=by
    )

    top_5 = (
        confirmed_since_df.groupby(by)["total_confirmed"]
        .max()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    top_10 = (
        confirmed_since_df.groupby(by)["total_confirmed"]
        .max()
        .sort_values(ascending=False)
        .head(10)
        .index.tolist()
    )

    multi = st.multiselect("", top_10, default=top_5)
    confirmed_since_df = confirmed_since_df[confirmed_since_df[by].isin(multi)]

    st.markdown(f"## Casos confirmados por dias desde {num_confirmed} confirmados 😷")
    if chart_type == "Cumulativo":
        st.altair_chart(chart(confirmed_since_df, "total_confirmed",'Total Confirmados', color=by))
    else:
        st.altair_chart(chart(confirmed_since_df, "daily_confirmed","confirmações Diárias", color=by))

    num_deaths = st.text_input("Número de Mortes:", 50)
    deaths_since_df = days_since(deaths_df, "total_deaths", num=int(num_deaths), groupby=by)
    deaths_since_df = deaths_since_df[deaths_since_df[by].isin(multi)]

    st.markdown(f"## Mortes por dia des de {num_deaths} Mortes")
    if chart_type == "Cumulative":
        st.altair_chart(chart(deaths_since_df, "total_deaths",'Total de Mortes', color=by))
    else:
        st.altair_chart(chart(deaths_since_df, "daily_deaths",'Mortes Diárias', color=by))

    st.markdown("## Total")
    df = (
        pd.concat(
            [
                confirmed_df.groupby(by)["total_confirmed"].max(),
                deaths_df.groupby(by)["total_deaths"].max(),
            ],
            axis=1,
        )
        .sort_values("total_deaths", ascending=False)
        .style.format("{:,}")
    )

    st.dataframe(df)


if __name__ == "__main__":
    st.title("COVID-19 🦠")
    main()