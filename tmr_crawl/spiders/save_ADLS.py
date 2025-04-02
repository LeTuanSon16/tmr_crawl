from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential
import os
import sys

#Load variables from .env file
load_dotenv()

def upload_to_adls(file_path, container_name, directory_name=None):
   tenant_id = os.environ.get('AZURE_TENANT_ID')
   client_id = os.environ.get('AZURE_CLIENT_ID')
   client_secret = os.environ.get('AZURE_CLIENT_SECRET')
   storage_account = os.environ.get('AZURE_STORAGE_ACCOUNT')
   
   if not all([tenant_id, client_id, client_secret, storage_account]):
       print("Thiếu biến môi trường Azure. Vui lòng kiểm tra file .env")
       return False
   
   try:
       credential = ClientSecretCredential(tenant_id, client_id, client_secret)
       
       # Khởi tạo service client
       service_client = DataLakeServiceClient(
           account_url=f"https://{storage_account}.dfs.core.windows.net",
           credential=credential
       )
       
       file_system_client = service_client.get_file_system_client(container_name)
       
       if directory_name:
           try:
               directory_client = file_system_client.get_directory_client(directory_name)
           except:
               directory_client = file_system_client.create_directory(directory_name)
       else:
           directory_client = file_system_client.get_directory_client("/")
       
       # Tên file trên ADLS
       file_name = os.path.basename(file_path)
       
       # Tạo file trên ADLS
       file_client = directory_client.create_file(file_name)
       
       # Đọc nội dung file local
       with open(file_path, 'rb') as local_file:
           file_contents = local_file.read()
           
           # Upload file lên ADLS
           file_client.append_data(data=file_contents, offset=0, length=len(file_contents))
           file_client.flush_data(len(file_contents))
       
       print(f"Upload thành công {file_name} lên {container_name}/{directory_name or ''}")
       return True
       
   except Exception as e:
       print(f"Lỗi khi upload: {str(e)}")
       return False

if __name__ == "__main__":
   if len(sys.argv) < 3:
       sys.exit(1)
   
   file_path = sys.argv[1]
   container_name = sys.argv[2]
   directory_name = sys.argv[3] if len(sys.argv) > 3 else None
   
   success = upload_to_adls(file_path, container_name, directory_name)
   sys.exit(0 if success else 1)

#  python .\tmr_crawl\spiders\test.py .\tax_company_data.csv upload-files list_tax.csv