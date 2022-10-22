# Nén file và tải về local machine
import os
import zipfile
    
def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))

with zipfile.ZipFile('Python.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipdir(path, zipf)

# TODO: Tách được file nén tổng thành các file nén nhỏ hơn 
# TODO: Thiết lập tự động tải file nén về local machine
# Quá chậm so với mong đợi khi tải file đã nén về local machine
