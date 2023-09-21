import hashlib, sys
def hash_md5(data):
    md5sum = hashlib.md5()
    md5sum.update(str(data))
    return str(md5sum.hexdigest())

def handle_upload_file_disk(file_object, chunk_size=1024):
        """
        will save file with new name, name is hash md5 content of data
        :param file_object: 
        :param chunk_size: 
        :return: 
        
            - okie     :  0, filename_hash_md5
            - not found:  -2, error
        """
        file_data = ""
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            file_data = file_data + data


        try:
            with open(sys.argv[1] + str(hash_md5(file_data)), 'wb+') as destination:
                destination.write(file_data)
            destination.close()
            return (0, str(hash_md5(file_data)))
        except Exception as e:
            return (-2, e.message)