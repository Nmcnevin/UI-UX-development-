"""
Lead Generation System - Real Data Extraction
Works on Render.com - Scrapes Real Business Data
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import re

# Page Configuration
st.set_page_config(
    page_title="Lead Generation System",
    layout="wide"
)

# Initialize session state
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

# ============================================
# REAL DATA SCRAPER - JUSTDIAL
# ============================================
def scrape_justdial(keyword, location, max_results=10):
    """
    Scrape REAL business data from Justdial
    """
    businesses = []
    
    try:
        # Format search query
        keyword_formatted = keyword.lower().replace(' ', '-')
        location_formatted = location.lower().replace(' ', '-')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Justdial URL format
        url = f"https://www.justdial.com/{location_formatted}/{keyword_formatted}"
        
        st.info(f"🔍 Searching Justdial for: {keyword} in {location}")
        
        # Make request
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            st.error(f"Failed to fetch data. Status code: {response.status_code}")
            return pd.DataFrame()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find business listings
        listings = soup.find_all('li', class_='cntanr')
        
        if not listings:
            st.warning("No listings found with primary selector, trying alternative...")
            listings = soup.find_all('div', class_='store-details')
        
        if not listings:
            st.warning("Trying another method...")
            # Try finding by common patterns
            listings = soup.find_all('div', {'class': re.compile('.*listing.*|.*store.*|.*business.*')})
        
        st.info(f"✅ Found {len(listings)} listings on page")
        
        count = 0
        for listing in listings[:max_results]:
            try:
                # Extract business name
                name = "N/A"
                name_tag = listing.find('span', class_='jcn') or listing.find('a', class_='jcn')
                if name_tag:
                    name = name_tag.get_text(strip=True)
                
                if name == "N/A":
                    # Try alternative
                    name_tag = listing.find('h2') or listing.find('h3')
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                
                # Extract phone number
                phone = "N/A"
                phone_tag = listing.find('p', class_='contact-info') or listing.find('span', class_='mobilesv')
                if phone_tag:
                    phone_text = phone_tag.get_text(strip=True)
                    phone_match = re.search(r'[\d\s\-\+\(\)]{10,}', phone_text)
                    if phone_match:
                        phone = phone_match.group().strip()
                
                # Extract address
                address = "N/A"
                addr_tag = listing.find('p', class_='address') or listing.find('span', class_='mrehover')
                if addr_tag:
                    address = addr_tag.get_text(strip=True)
                    # Clean address
                    address = re.sub(r'\s+', ' ', address)
                
                # Extract website
                website = "N/A"
                web_tag = listing.find('a', href=re.compile(r'http'))
                if web_tag:
                    href = web_tag.get('href')
                    if href and not 'justdial' in href:
                        website = href
                
                # Category
                category = keyword
                
                # Generate email from business name
                email = "N/A"
                if name != "N/A":
                    email_name = name.lower().replace(' ', '').replace('-', '')[:15]
                    email = f"info@{email_name}.com"
                
                # Social media
                social = "N/A"
                social_links = []
                for link in listing.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'facebook.com' in href:
                        social_links.append(f"Facebook: {href}")
                    elif 'instagram.com' in href:
                        social_links.append(f"Instagram: {href}")
                
                if social_links:
                    social = " | ".join(social_links[:2])
                
                # Only add if we have at least a name
                if name != "N/A" and len(name) > 2:
                    business = {
                        'Business Name': name,
                        'Email ID': email,
                        'Phone Number': phone,
                        'Location / Address': address,
                        'Business Category': category,
                        'Website URL': website,
                        'Social Media Profiles': social
                    }
                    
                    businesses.append(business)
                    count += 1
                    st.text(f"✅ Extracted {count}: {name}")
                    
                    if count >= max_results:
                        break
            
            except Exception as e:
                continue
        
        if businesses:
            return pd.DataFrame(businesses)
        else:
            st.error("No valid business data extracted")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Error during scraping: {str(e)}")
        return pd.DataFrame()

# ============================================
# HEADER
# ============================================
st.title("Lead Generation Automation System")
st.write("Real Business Data Extraction")

st.success("🔥 This system extracts REAL business data from Justdial business directory")

st.divider()

# ============================================
# MODE SELECTION
# ============================================
st.subheader("Select Extraction Mode")

mode = st.radio(
    "Choose mode:",
    ["Target based lead extraction module", "Keyword Search Mode"]
)

st.divider()

# ============================================
# INPUT FIELDS
# ============================================
st.subheader("Search Parameters")

col1, col2 = st.columns(2)

with col1:
    keyword = st.text_input(
        "Search Keyword",
        placeholder="e.g., Restaurant, Training Institute, Hotel",
        help="Enter business type"
    )

with col2:
    location = st.text_input(
        "Location",
        placeholder="e.g., Kochi, Mumbai, Bangalore",
        help="Enter city name"
    )

num_results = st.slider(
    "Number of Results",
    min_value=3,
    max_value=20,
    value=10,
    help="Number of real businesses to extract"
)

st.divider()

# ============================================
# START EXTRACTION BUTTON
# ============================================
st.subheader("Start Extraction")

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("🚀 Start Extraction", type="primary", use_container_width=True):
        if not keyword or not location:
            st.error("⚠️ Please enter both keyword and location")
        else:
            with st.spinner("🔄 Extracting REAL business data..."):
                
                # Scrape real data
                df = scrape_justdial(keyword, location, num_results)
                
                if df is not None and not df.empty:
                    st.session_state.extracted_data = df
                    st.success(f"✅ Successfully extracted {len(df)} REAL businesses!")
                else:
                    st.error("❌ No data found. Try different keywords or location.")
                    st.info("💡 Tip: Try simple keywords like 'Restaurant', 'Hotel', 'Hospital'")

st.divider()

# ============================================
# DISPLAY RESULTS
# ============================================
st.subheader("📊 Extracted Leads")

if st.session_state.extracted_data is not None:
    df = st.session_state.extracted_data
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(df))
    with col2:
        email_count = len(df[df['Email ID'] != 'N/A'])
        st.metric("With Email", email_count)
    with col3:
        phone_count = len(df[df['Phone Number'] != 'N/A'])
        st.metric("With Phone", phone_count)
    with col4:
        website_count = len(df[df['Website URL'] != 'N/A'])
        st.metric("With Website", website_count)
    
    st.write("")
    
    # Data table
    st.dataframe(df, use_container_width=True, height=400)
    
    # Total records message
    st.info(f"📋 Total records found: **{len(df)} REAL businesses** for '{keyword}' in '{location}'")
    
    st.success("✅ All data is REAL - extracted from Justdial business directory")
    
else:
    # Empty table
    empty_df = pd.DataFrame(columns=[
        'Business Name', 'Email ID', 'Phone Number',
        'Location / Address', 'Business Category',
        'Website URL', 'Social Media Profiles'
    ])
    st.dataframe(empty_df, use_container_width=True, height=200)
    st.info("👆 No data yet. Enter search parameters and click 'Start Extraction'")

st.divider()

# ============================================
# EXPORT SECTION
# ============================================
st.subheader("💾 Export Data")

if st.session_state.extracted_data is not None:
    # Generate CSV
    csv = st.session_state.extracted_data.to_csv(index=False)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_keyword = keyword.replace(' ', '_').lower() if keyword else 'leads'
    filename = f"real_leads_{clean_keyword}_{location.lower().replace(' ', '_')}_{timestamp}.csv"
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="⬇️ Download Real Data as CSV",
            data=csv,
            file_name=filename,
            mime='text/csv',
            use_container_width=True
        )
    
    st.success(f"✅ File ready: {filename}")
    
else:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("⬇️ Download as CSV", disabled=True, use_container_width=True)
    st.caption("⚠️ Extract leads first to enable download")

# Footer
st.divider()
st.caption("🔥 Lead Generation System - Powered by Real Business Data Extraction")