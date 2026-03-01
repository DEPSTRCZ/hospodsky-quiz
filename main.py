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
        #if "Žolík" in loaded.columns:
        #    loaded["Žolík"] = loaded["Žolík"].astype("boolean").fillna(False)
        #else:
        #    loaded["Žolík"] = False
        return loaded
    else:
        return EMPTY_DATA



def SetupPage():
    st.title("Nastavení nové hry")
    # reset st session state

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
    
    # Fill NaN values with 0
    edited_data = edited_data.fillna(0)

    
    if st.button("Začít hru"):
        # check if the data equals empty if so do not allow saving and show an error message
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
        new_data["Žolík"] = None
        SaveToQueryParams(new_data)
        st.rerun()
    # If there is not a column for the current round, add it
    if f"Kolo {round_number}" not in new_data.columns:
        new_data[f"Kolo {round_number}"] = 0
        SaveToQueryParams(new_data)
        st.rerun()

    def FormatujŽolíkaxD(option):
        return f"🃏 V kole {option}"
    
    sort = st.toggle("Seřadit podle celkového skóre", key="sort_toggle")

    if sort:
        new_data = new_data.sort_values("Celkem", ascending=False)  # ← add this


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
                width="small"
            ),
            0: st.column_config.TextColumn(
                label="Název týmu",
                width=None
            )
        }
    )

    # COunt the sum of all rounds for each team and update the "Celkem" column
    round_columns = [col for col in round_data_editor.columns if col.startswith("Kolo") and col not in ["Celkem", "Žolík",]]
    round_data_editor["Celkem"] = round_data_editor[round_columns].sum(axis=1)
    
    # Save the edited data
    if not round_data_editor.equals(new_data):
        print("Data changed, saving to query params")
        SaveToQueryParams(round_data_editor)
        st.session_state.editor_version = st.session_state.get("editor_version", 0) + 1
        st.rerun()


    col1, col2 = st.columns(2)
    with col2:
        if st.button("Přejít na další kolo",type="secondary"):
            st.query_params["round"] = str(round_number + 1)
            st.rerun()
    with col1:
        if st.button("Ukončit a zobrazit výsledky",type="primary"):
            st.query_params.pop("round", None)
            st.query_params["state"] = "finished"
            st.rerun()


def ResultsPage():
    st.title("Konec hry 🏆")

    data = GetDataFromQueryParams().sort_values("Celkem", ascending=True)
    # iloc[0] = lowest score (last place), iloc[-1] = highest score (1st place)

    if "revealed_count" not in st.session_state:
        st.session_state.revealed_count = 0

    total_teams = len(data)
    revealed = st.session_state.revealed_count

    if revealed > 0:
        # Take first `revealed` rows (worst teams first), reverse so newest is on top
        result_df = data.head(revealed).iloc[::-1].copy()
        result_df.insert(0, "Místo", range(1, revealed + 1))

        # Format Žolík column if it exists
        if "Žolík" in result_df.columns:
            result_df["Žolík"] = result_df["Žolík"].apply(
                lambda x: f"🃏 V kole {int(x)}" if pd.notna(x) else ""
            )

        st.table(result_df,border="horizontal")
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