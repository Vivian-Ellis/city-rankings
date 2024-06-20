import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")
import requests
from streamlit_lottie import st_lottie

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Define function to assign points based on brackets
def assign_points(series, num_brackets=50,importance=1):
    sorted_series = np.sort(series)
    thresh = np.median(sorted_series)*2
    # percentile95=np.percentile(sorted_series, 95)
    # top_bracket_value = 2 * percentile95
    
    points = np.zeros_like(series, dtype=float)

    # Define brackets
    bracket_ranges = np.linspace(0, thresh, num_brackets)
    
    for i, value in enumerate(series):
        if value > thresh:
            weighted_points=100*importance
            points[i] = weighted_points
        else:
            for j in range(len(bracket_ranges) - 1):
                if bracket_ranges[j] <= value <= bracket_ranges[j + 1]:
                    points[i] = ((j + 1) * (100 / num_brackets))*importance
                    break
    
    return points

@st.cache_data
def read_data():
    data=pd.read_csv('data.csv',index_col=0)
    return data.sort_values(by='City',ascending=True)

def main():
    st.markdown('<h2 style="text-align: center;">Welcome to City Rankings!</h2>', unsafe_allow_html=True)
    lottie_park = load_lottieurl("https://lottie.host/828ea407-9fae-4fd8-8c62-853aebda2ba7/i8ljAZJJIO.json")
    st_lottie(lottie_park, speed=1, height=150, key="initial")
    st.markdown("Where finding your dream city is as fun as it is easy. Let me know which public amenities matter most to you, and I'll reveal the top cities with them all. Not a fan of specific amenities? No problem, I'll downplay those in your results. You'll get a personalized ranking of the best cities based on your preferences.")
    st.markdown("Want to see how your current city stacks up? Enter its name, and I'll show you all the cities that outshine it. Or, simply enjoy the top 10 list of the best cities tailored to your needs. Happy exploring!")
    st.text("")

    # read in data
    data=read_data()

    with st.container():
        all_amenities=np.sort(data.columns[1:])

        col1, col2, col3 = st.columns(3)
        # parameters
        with col1:
            important_amenities=st.multiselect(label='Important Amenities',options=all_amenities)
        
        with col2:
            unimportant_amenities=st.multiselect(label='Unimportant Amenities',options=np.sort(list(set(all_amenities)-set(important_amenities))))
        
        all_cities=data.City.unique()
        with col3:
            current_city=st.selectbox("What City Do you Currently Live In?",all_cities,index=None)
        st.text("")
        st.text("")

        # Apply the point assignment for each measure
        base_columns=['Walkable Park Access','Park Units','Walk Score','Transit Score','Bike Score']
        for column in base_columns:
            data[column + '_points'] = assign_points(data[column])
        for column in important_amenities:
            data[column + '_points'] = assign_points(data[column],importance=5)
        for column in unimportant_amenities:
            data[column + '_points'] = assign_points(data[column],importance=-1)

        # Calculate total points (out of ?)
        data['total_points'] = data[[col for col in data.columns if col.endswith('_points')]].sum(axis=1)

        # Normalize to a ParkScore rating of up to 100
        data['Ranking'] = (data['total_points'] / data['total_points'].max()) * 100

        if current_city is None:
            data=data.head(10)
        else:
            threshold=data[data['City']==current_city].Ranking.values[0]
            data=data[data['Ranking']>=threshold]

        data=data.sort_values(by='Ranking',ascending=False)

        fig = px.bar(data, x='City', y='Ranking',
                    hover_name='City',
                    hover_data={'Ranking':":.2f",
                                'City':False
                                },
                    color_discrete_sequence=['#779c64'],
                    labels={'variable': ''},
                    template="simple_white"
                    )

        fig.update_xaxes(showgrid=False, title_text='')
        fig.update_yaxes(showgrid=True)

        fig.update_traces(hoverlabel_font_color="white",hoverlabel_bordercolor="white",
                        textfont_family='Arial',textfont_size=16, textangle=0,
                        textposition="outside", cliponaxis=False)

        fig.update_layout(
            autosize=False,
            width=800,
            height=500,
            font_family="Arial",
            font_size=16,
            title_font_family="Arial",
            title_font_size=18,
            title={
                'text': 'Top Cities Based on User-Reported Amenity Importance',
                'x': .5,
                'y': .97,
                'xanchor': 'center',
                'yanchor': 'top'},
            yaxis_tickformat='.2f'
        )

        st.plotly_chart(fig,theme='streamlit', use_container_width=True)
if __name__ == '__main__':
    main()
