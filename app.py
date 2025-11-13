# # app.py
# import streamlit as st
# from query import get_answer

# st.set_page_config(page_title="NYC Zoning Q&A", layout="centered")
# st.title("Ask the Zoning Handbook (2018)")

# q = st.text_input(
#     "Your question",
#     placeholder="e.g., What are the three zoning district categories?"
# )

# if st.button("Ask") and q:
#     with st.spinner("Thinking..."):
#         answer = get_answer(q)   # ⬅️ call our function that returns a string
#     st.markdown(answer)

# app.py
import streamlit as st
from query import get_answer

st.set_page_config(page_title="NYC Zoning Q&A", layout="centered")
st.title("Ask the Zoning Handbook (2018)")

q = st.text_input(
    "Your question",
    placeholder="e.g., What are the different zoning districts?"
)

if st.button("Ask") and q:
    with st.spinner("Thinking..."):
        answer = get_answer(q)
    st.markdown(answer)
