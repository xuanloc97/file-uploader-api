# -*- coding: utf-8 -*-
import re
import os
import hashlib
import logging

from src import settings
from src.api.exceptions import SignError

logger = logging.getLogger("utils")

def hash_md5(data):
    md5sum = hashlib.md5()
    md5sum.update(str(data).encode('utf-8'))
    return str(md5sum.hexdigest())

def check_file_size_limit(file_object):
    """
    check file limit from file upload. if file > size limit defind will be return -1
    :param fileupload: file object on request post
    :return:
             - : 0 oke
             - : -1 error
    """

    if file_object:

         if len(file_object.read()) <= settings.FILE_SIZE:
            return 0
         else:
             return  -1

    else:
        return -1

def check_file_type(file_name):
    """
    check file type wwith file name
    
    :param fileobject: fileobject
    :return:
             - : 0 oke
             - : -1 error
    """
    if len(file_name.split(".")) == 2:
        get_type_file = re.findall("[a-zA-Z/-/_]*[/.]([a-zA-Z]*)", file_name)
        try:
            typ = get_type_file[len(get_type_file) - 1]
        except:
            typ = get_type_file[0]

    elif len(file_name.split(".")) > 2:
        typ = file_name.split(".")[-1]
    else:
        typ = file_name

    if typ in  [ type for type in settings.FILE_TYPE_ALLOW.keys()]:
        return 0, settings.FILE_TYPE_ALLOW[typ]
    else:
        return -1, "not found"


def check_signature(md5_content_file, sign_of_client):
    """
    check signature cua client goi len. mục đích đảm bảo tính toàn vẹn của data gởi lên, không bị sửa trong quá 
    trình gởi.

    Dữ liệu sẽ được phía client md5(md5(content_file) + SECRET_KEY) gở lên server trong header
    Phía server sẽ nhận file data đông thời generate lại sign rồi compare để đảm bảo dữ liệu là đúng


    :param md5_content_file: 
    :param sign_of_client: 
    :return: 
      - oke : 0
      - fail: -1

    """
    sign = hash_md5(str(md5_content_file + settings.SECRET_KEY))
    logger.info(sign)
    logger.info(sign_of_client)
    if str(sign) == sign_of_client:
        return 0
    else:
        return -1


def handle_upload_file_disk(file_data, sign_client, chunk_size=1024, logger=logger):
        """
        will save file with new name, name is hash md5 content of data
        :param file_object: 
        :param chunk_size: file_data
        :return: 
        
            - oke     :  0, filename_hash_md5
            - not found:  -2, error
        """
        logger.info(f'file : {file_data}')
        # file_data = file_object.read()
        # while True:
        #     data = file_object.read(chunk_size)
        #     logger.info(f'file_data : {file_data}')
        #     if not data:
        #         break
        #     file_data = file_data + data

        # check signature when user upload file
        logger.info(sign_client)

        # check = check_signature(str(hash_md5(file_data)), sign_client)
        # if check == -1:
        #     raise SignError(sign_client)


        try:
            with open(settings.FILE_RESOURCE_UPLOAD + str(hash_md5(file_data)), 'wb+') as destination:
                logger.info(file_data)
                destination.write(file_data)
            destination.close()
            return (0, str(hash_md5(file_data)))

        except Exception as e:
            logger.info(e)
            return (-2, str(e))

def handle_delete_file_disk(file_name):
    """
    remove file on disk
    
    :param dir_file_name: 
    :return: 
             - : 0 oke
             - : -1 file not found
             - : -2 error (permission deny)
    """
    if os.path.exists(settings.FILE_RESOURCE_UPLOAD + file_name) and os.path.isfile(settings.FILE_RESOURCE_UPLOAD + file_name):
        try:
            os.remove(settings.FILE_RESOURCE_UPLOAD + file_name)
            return (0, file_name)
        except OSError as e:
            return (-2, e.message)
    else:
        return (-1, 'file not found')

def handle_read_file_disk(file_name):
    """
    read file on disk

    :param dir_file_name: 
    :return: 
             - : 0 oke
             - : -1 file not found
             - : -2 error (permission deny)
    """
    data = ""
    if os.path.exists(settings.FILE_RESOURCE_UPLOAD + file_name):
        try:
            with open(settings.FILE_RESOURCE_UPLOAD + file_name, 'rb') as fh:
                data = fh.read()
            fh.close()
            return 0, data
        except OSError as e:
            return -2, e
    else:
        return -1, 'file not found'
