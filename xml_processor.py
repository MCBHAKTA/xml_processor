import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO
import zipfile
from datetime import datetime

def parse_building_record_xml(xml_content):
    """Parse a single XML file and extract building records"""
    try:
        root = ET.fromstring(xml_content)
        
        # Extract global details
        global_details = root.find('GlobalDetails')
        sender_code = global_details.find('SenderCode').text if global_details.find('SenderCode') is not None else ''
        local_authority_code = global_details.find('LocalAuthorityCode').text if global_details.find('LocalAuthorityCode') is not None else ''
        submission_date = global_details.find('SubmissionDate').text if global_details.find('SubmissionDate') is not None else ''
        sender_email = global_details.find('SenderResponseEmailAddress').text if global_details.find('SenderResponseEmailAddress') is not None else ''
        sender_phone = global_details.find('SenderResponsePhoneNo').text if global_details.find('SenderResponsePhoneNo') is not None else ''
        
        records = []
        
        # Extract each building record
        for building_record in root.findall('BuildingRecord'):
            record = {}
            
            # Global details (same for all records in file)
            record['sender_code'] = sender_code
            record['local_authority_code'] = local_authority_code
            record['submission_date'] = submission_date
            record['sender_email'] = sender_email
            record['sender_phone'] = sender_phone
            
            # Status details
            status_details = building_record.find('StatusDetails')
            if status_details is not None:
                record['status_type'] = status_details.find('StatusType').text if status_details.find('StatusType') is not None else ''
            
            # Record details
            record_details = building_record.find('RecordDetails')
            if record_details is not None:
                record['record_type'] = record_details.find('RecordType').text if record_details.find('RecordType') is not None else ''
            
            # Work address details
            work_address_details = building_record.find('WorkAddressDetails')
            if work_address_details is not None:
                work_address = work_address_details.find('WorkAddress')
                if work_address is not None:
                    record['number_name'] = work_address.find('NumberName').text if work_address.find('NumberName') is not None else ''
                    record['street'] = work_address.find('Street').text if work_address.find('Street') is not None else ''
                    record['locality'] = work_address.find('Locality').text if work_address.find('Locality') is not None else ''
                    record['town_city'] = work_address.find('TownCity').text if work_address.find('TownCity') is not None else ''
                    county_element = work_address.find('County')
                    record['county'] = county_element.text.title() if county_element is not None and county_element.text else ''
                    record['post_code'] = work_address.find('PostCode').text if work_address.find('PostCode') is not None else ''
                
                uprn_text = work_address_details.find('WorkAddressUprn').text if work_address_details.find('WorkAddressUprn') is not None and work_address_details.find('WorkAddressUprn').text else ''
                record['work_address_uprn'] = int(uprn_text) if uprn_text.isdigit() else None
                record['type_of_property'] = work_address_details.find('TypeOfProperty').text if work_address_details.find('TypeOfProperty') is not None else ''
            
            # Work details
            work_details = building_record.find('WorkDetails')
            if work_details is not None:
                record['sender_unique_record_id'] = work_details.find('SenderUniqueRecordIdentifier').text if work_details.find('SenderUniqueRecordIdentifier') is not None else ''
                record['cp_scheme_certificate_ref'] = work_details.find('CPSchemeCertificateReference').text if work_details.find('CPSchemeCertificateReference') is not None else ''
                record['commissioning_required'] = work_details.find('CommissioningRequired').text if work_details.find('CommissioningRequired') is not None else ''
                record['commissioning_carried_out'] = work_details.find('CommissioningCarriedOut').text if work_details.find('CommissioningCarriedOut') is not None else ''
                record['date_work_completed'] = work_details.find('DateWorkCompleted').text if work_details.find('DateWorkCompleted') is not None else ''
            
            # Work description - combine all work items
            work_description = building_record.find('WorkDescription')
            work_items = []
            if work_description is not None:
                for item in work_description.findall('DescriptionOfWorkItem'):
                    if item.text:
                        work_items.append(item.text)
            record['work_description'] = ' | '.join(work_items)
            
            # Contact information
            contact_info = building_record.find('ContactInformation')
            if contact_info is not None:
                contact_details = contact_info.find('ContactDetails')
                if contact_details is not None:
                    record['contact_type'] = contact_details.find('ContactType').text if contact_details.find('ContactType') is not None else ''
                    record['installer_registered_name'] = contact_details.find('InstallerRegisteredName').text if contact_details.find('InstallerRegisteredName') is not None else ''
                    record['person_registration_id'] = contact_details.find('PersonRegistrationIdentifier').text if contact_details.find('PersonRegistrationIdentifier') is not None else ''
                    record['telephone_no'] = contact_details.find('TelephoneNo').text if contact_details.find('TelephoneNo') is not None else ''
            
            records.append(record)
        
        return records
    
    except ET.ParseError as e:
        st.error(f"XML parsing error: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Error processing XML: {str(e)}")
        return []

def process_uploaded_files(uploaded_files):
    """Process all uploaded XML files and return combined dataframe"""
    all_records = []
    
    for uploaded_file in uploaded_files:
        try:
            # Read file content
            if uploaded_file.name.endswith('.zip'):
                # Handle zip files
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    for file_name in zip_ref.namelist():
                        if file_name.endswith('.xml'):
                            with zip_ref.open(file_name) as xml_file:
                                xml_content = xml_file.read().decode('utf-8')
                                records = parse_building_record_xml(xml_content)
                                for record in records:
                                    record['source_file'] = file_name
                                all_records.extend(records)
            else:
                # Handle individual XML files
                xml_content = uploaded_file.read().decode('utf-8')
                records = parse_building_record_xml(xml_content)
                for record in records:
                    record['source_file'] = uploaded_file.name
                all_records.extend(records)
                
        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {str(e)}")
            continue
    
    if all_records:
        df = pd.DataFrame(all_records)
        return df
    else:
        return pd.DataFrame()

def main():
    st.set_page_config(
        page_title="Building Records Processor",
        page_icon="🏗️",
        layout="wide"
    )
    
    st.title("🏗️ Building Records XML Processor")
    st.write("Upload XML files containing Building Record data to convert them to CSV format")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose XML files or ZIP archives",
        type=['xml', 'zip'],
        accept_multiple_files=True,
        help="Upload individual XML files or ZIP archives containing XML files"
    )
    
    if uploaded_files:
        with st.spinner('Processing files...'):
            df = process_uploaded_files(uploaded_files)
        
        if not df.empty:
            st.success(f"Successfully processed {len(df)} building records from {len(uploaded_files)} file(s)")
            
            # Display data preview
            st.subheader("📊 Data Preview")
            st.write(f"Total records: {len(df)}")
            
            # Show summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Unique Senders", df['sender_code'].nunique())
            with col3:
                st.metric("Unique Installers", df['installer_registered_name'].nunique())
            with col4:
                st.metric("Date Range", f"{df['date_work_completed'].min()} to {df['date_work_completed'].max()}" if 'date_work_completed' in df.columns else "N/A")
            
            # Display dataframe
            st.dataframe(df, use_container_width=True)
            
            # Filter options
            st.subheader("🔍 Filter Data")
            
            if 'sender_code' in df.columns:
                sender_filter = st.multiselect(
                    "Filter by Sender Code",
                    options=sorted(df['sender_code'].unique()),
                    default=sorted(df['sender_code'].unique())
                )
            else:
                sender_filter = []
            
            # Apply filters
            filtered_df = df.copy()
            if sender_filter and 'sender_code' in df.columns:
                filtered_df = filtered_df[filtered_df['sender_code'].isin(sender_filter)]
            
            if len(filtered_df) != len(df):
                st.write(f"Filtered to {len(filtered_df)} records")
                st.dataframe(filtered_df, use_container_width=True)
            
            # Download options
            st.subheader("⬇️ Download Data")
            
            # Generate CSV
            csv_buffer = StringIO()
            filtered_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"building_records_{timestamp}.csv"
            
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                help="Download the processed data as a CSV file"
            )
            
            # Show column information
            with st.expander("📋 Column Information"):
                st.write("**Column Descriptions:**")
                column_descriptions = {
                    'sender_code': 'Competent Persons Scheme code (e.g., CERTAS, HETAS, NICEIC, BBA)',
                    'source_file': 'Original XML file name'
                    
                }
                
                for col, desc in column_descriptions.items():
                    if col in filtered_df.columns:
                        st.write(f"• **{col}**: {desc}")
        
        else:
            st.error("No valid building records found in the uploaded files. Please check the XML format.")
    
    else:
        st.info("👆 Upload XML files to get started")

if __name__ == "__main__":
    main()