import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from datetime import datetime, timedelta
import yaml
import sys

try:
    if len(sys.argv) < 4:
        raise ValueError("Insufficient arguments. Please provide at least two HTML files and the container name.")

    
    resources = sys.argv[4]
    with open(resources) as f:
        data_dict = yaml.safe_load(f)

    az_storage_blob_account_url = data_dict['azure_storage_blob_account']['url']
    az_storage_blob_account_name = data_dict['azure_storage_blob_account']['name']
    connect_str = data_dict['azure_storage_blob_account']['connected_string']
    container_name = sys.argv[3]

    
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    
    container_client = blob_service_client.get_container_client(container_name)

    
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y_%H-%M-%S_snyk_report")
    folder_name = "snyk_report"
    timestamp_folder = f"{folder_name}/{dt_string}/"

    uploaded_file_urls = []  

    
    for file_path in sys.argv[1:3]:
        if not os.path.exists(file_path):
            print(f"File '{file_path}' does not exist. Skipping...")
            continue

        
        upload_file_name = os.path.basename(file_path)

        
        blob_name = f"{timestamp_folder}{upload_file_name}"

       
        with open(file_path, mode="rb") as data:
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type='text/html'))  # Specify content type as HTML

        print(f"Uploaded '{upload_file_name}' successfully.")

        
        expiry_time = datetime.utcnow() + timedelta(weeks=1)
        sas_token = generate_blob_sas(
            blob_client.account_name,
            container_client.container_name,
            blob_client.blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
        )

        
        blob_url = f"{blob_client.url}?{sas_token}"

        
        uploaded_file_urls.append(blob_url)

    
    test_report_url = uploaded_file_urls[0] if uploaded_file_urls else None
    code_report_url = uploaded_file_urls[1] if len(uploaded_file_urls) > 1 else None

    print(f"Test Report URL: {test_report_url}")
    print(f"Code Report URL: {code_report_url}")

except Exception as ex:
    print('Exception:')
    print(ex)
