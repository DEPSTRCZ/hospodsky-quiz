import streamlit as st
import pandas as pd
import base64
from io import StringIO



st.title("Hospodský Quiz")
st.divider()
EMPTY_DATA = pd.DataFrame(index=pd.Index([], name="Název týmu"), columns=["Celkem"]).astype({"Celkem": float})

def SaveToQueryParams(data):
    print(data.to_json(orient="index", force_ascii=False))
    st.query_params["data"] = base64.b64encode(data.to_json(orient="index", force_ascii=False).encode('utf-8')).decode()

def GetDataFromQueryParams():
    if "data" in st.query_params:
        decoded = base64.b64decode(st.query_params["data"]).decode()
        loaded = pd.read_json(StringIO(decoded), orient="index")
        return loaded
    else:
        return EMPTY_DATA



def SetupPage():
    st.title("Nastavení nové hry")

    edited_data = st.data_editor(
        EMPTY_DATA,
        num_rows="dynamic",
        key="data_editor_setup",
        hide_index=False,
        column_config={
            "Celkem": st.column_config.NumberColumn(
                default=0,
                disabled=True,
                width="small"
            ),
            0: st.column_config.TextColumn(
                label="Název týmu",
                required=True,
                width="large"
            )
        }
    )
    
    edited_data = edited_data.fillna(0)

    if st.button("Začít hru"):
        if edited_data.equals(EMPTY_DATA):
            st.error("Nelze uložit prázdná data. Přidejte alespoň jeden tým.")
        else:
            SaveToQueryParams(edited_data)
            st.query_params["round"] = "1"
            st.rerun()

def RoundPage(round_number):
    st.title(f"Kolo {round_number}")
    st.write("Tady bude obsah kola")
    new_data = GetDataFromQueryParams()

    if "Žolík" not in new_data.columns:
        new_data["Žolík"] = -1
        SaveToQueryParams(new_data)
        st.rerun()

    if f"Kolo {round_number}" not in new_data.columns:
        new_data[f"Kolo {round_number}"] = 0.0
        SaveToQueryParams(new_data)
        st.rerun()

    # Cast all existing round columns to float to ensure Streamlit accepts decimals
    for i in range(1, round_number + 1):
        col = f"Kolo {i}"
        if col in new_data.columns:
            new_data[col] = new_data[col].astype(float)

    def FormatujŽolíkaxD(option):
        return f"🃏 V kole {option}"
    
    sort = st.toggle("Seřadit podle celkového skóre", key="sort_toggle")

    if sort:
        new_data = new_data.sort_values("Celkem", ascending=False)

    round_data_editor = st.data_editor(
        new_data, 
        num_rows="fixed",
        key=f"round_data_editor_{st.session_state.get('editor_version', 0)}",
        hide_index=False,
        column_config={
            "Žolík": st.column_config.SelectboxColumn(
                options=range(1, round_number + 1),
                required=False,
                format_func=FormatujŽolíkaxD
            ),
            "Celkem": st.column_config.NumberColumn(
                disabled=True,
                width="small",
                format="%.2f"
            ),
            0: st.column_config.TextColumn(
                label="Název týmu",
                width=None
            ),
            **{f"Kolo {i}": st.column_config.NumberColumn(
                width="small",
                step=0.01,
                format="%.2f"
            ) for i in range(1, round_number + 1)}
        }
    )

    round_columns = [col for col in round_data_editor.columns if col.startswith("Kolo") and col not in ["Celkem", "Žolík"]]
    
    # Normalize dtypes before comparing to avoid false positive loop
    for col in round_columns:
        round_data_editor[col] = round_data_editor[col].astype(float)

    round_data_editor["Celkem"] = round_data_editor[round_columns].sum(axis=1).round(2)
    
    new_data["Celkem"] = new_data["Celkem"].astype(float)
    new_data["Žolík"] = new_data["Žolík"].astype("int64")

    print("=== DTYPE COMPARISON ===")
    print("new_data dtypes:\n", new_data.dtypes)
    print("round_data_editor dtypes:\n", round_data_editor.dtypes)

    print("=== VALUE COMPARISON ===")
    for col in new_data.columns:
        for idx in new_data.index:
            v1 = new_data.at[idx, col]
            v2 = round_data_editor.at[idx, col]
            if v1 != v2 or type(v1) != type(v2):
                print(f"DIFF at [{idx}][{col}]: new_data={v1!r} ({type(v1).__name__}) vs editor={v2!r} ({type(v2).__name__})")

    print("=== INDEX COMPARISON ===")
    print("new_data index:", new_data.index.tolist(), "name:", new_data.index.name)
    print("editor index:", round_data_editor.index.tolist(), "name:", round_data_editor.index.name)


    if not round_data_editor.equals(new_data):
        print("Data changed, saving to query params")
        SaveToQueryParams(round_data_editor)
        st.session_state.editor_version = st.session_state.get("editor_version", 0) + 1
        st.rerun()

    col1, col2 = st.columns(2)
    with col2:
        if st.button("Přejít na další kolo", type="secondary"):
            st.query_params["round"] = str(round_number + 1)
            st.rerun()
    with col1:
        if st.button("Ukončit a zobrazit výsledky", type="primary"):
            st.query_params.pop("round", None)
            st.query_params["state"] = "finished"
            st.rerun()


def ResultsPage():
    st.title("Konec hry 🏆")

    data = GetDataFromQueryParams().sort_values("Celkem", ascending=True)

    if "revealed_count" not in st.session_state:
        st.session_state.revealed_count = 0

    total_teams = len(data)
    revealed = st.session_state.revealed_count

    if revealed > 0:
        result_df = data.head(revealed).iloc[::-1].copy()
        result_df = result_df.round(2)
        for col in result_df.select_dtypes(include='number').columns:
            # if column is "žolík", skip formatting
            if col == "Žolík":
                continue
            result_df[col] = result_df[col].apply(lambda x: f"{x:.2f}")
        #result_df.insert(0, "Místo", range(total_teams, total_teams - revealed, -1))

        if "Žolík" in result_df.columns:
            result_df["Žolík"] = result_df["Žolík"].apply(
                lambda x: f"🃏 V kole {int(x)}" if pd.notna(x) and x != -1 else "Nevyžolíkováno"
            )

        st.table(result_df, border="horizontal")
    else:
        st.info("Stiskněte tlačítko pro odhalení výsledků.")

    if revealed < total_teams:
        if st.button("Odhalit další tým ▶"):
            st.session_state.revealed_count += 1
            st.rerun()
    else:
        st.success("🥇 Gratulujeme všem týmům!")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Začít znovu"):
                st.session_state.revealed_count = 0
                st.rerun()
        with col2:
            if st.button("Stáhnout výsledky"):
                csv = data.to_csv().encode('utf-8')
                b64 = base64.b64encode(csv).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="vysledky.csv">Stáhnout CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
        with col3:
            if st.button("Resetovat hru"):
                st.session_state.clear()
                st.query_params.clear()
                st.rerun()
            
        
# Main logic
if "data" not in st.query_params:
    SetupPage()
    print("No data in query params, showing setup page")
elif "round" in st.query_params:
    RoundPage(int(st.query_params["round"]))
    print(f"Round {st.query_params['round']} in query params, showing round page")

if st.query_params.get("state", [None]) == "finished":
    ResultsPage()
    print("State is finished, showing results page")


st.caption("Vytvořil Jiří Edelmann s mentální podporou Vojtěcha Hotaře. Legendy z pokoje 321 :P")