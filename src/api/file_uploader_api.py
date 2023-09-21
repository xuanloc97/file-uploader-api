import os
import logging
from datetime import datetime

from flask import Blueprint, Response, request
from flask.views import MethodView
from dataclasses import asdict

from src.api.exceptions import (
                                FileDoesNotExist,
                                DoesNotExist,
                                FileTypeNotAllow,
                                ServerError,
                                FileSizeLimit,
                                FileNotSync
                            )

from src.api.utils import (
    check_file_size_limit,
    check_file_type,
    handle_delete_file_disk,
    handle_read_file_disk,
    handle_upload_file_disk
)

from src.helpers import respone_status
from src.helpers.response import ResponseAPI
from src.helpers.authentication import token_required

from . import db
from .models import Files

file_uploader_api = Blueprint('file_uploader_api', __name__)

console = logging.StreamHandler()
logger = logging.getLogger("file_upload_API")
logger.addHandler(console)

logging.basicConfig(
    format='%(module)s : %(lineno)s : %(levelname)-8s - message: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


@file_uploader_api.route('/viewfile', methods=['GET'])
@token_required
def get():
    file_name = request.args['file_name']
    status , content_type = check_file_type(file_name)

    # validate file type
    if status == 0:
        # file type allow

        # check file in database
        file_db = Files.query.filter_by(name=file_name).first()
        if file_db is None:
            logger.info(f'{file_name}: File not found')
            return ResponseAPI(
                respone_code=respone_status.FILE_DOES_NOT_EXIST.code,
                response_message=respone_status.FILE_DOES_NOT_EXIST.message).resp

        # check file on disk
        status, file_content = handle_read_file_disk(file_db.name)

        # file okie
        if status == 0:
            response = Response(file_content, content_type=str(content_type))
            return response

        # file not found
        elif status == -1:
            return ResponseAPI(
                respone_code=respone_status.FILE_DOES_NOT_SYNC.code,
                response_message=respone_status.FILE_DOES_NOT_SYNC.message).resp

        # file error
        elif status == -2:
            return ResponseAPI(
                respone_code=respone_status.SERVER_ERROR.code,
                response_message=respone_status.SERVER_ERROR.message).resp

    else:
        # file type not allow
        return ResponseAPI(
            respone_code=respone_status.FILE_TYPE_NOT_ALLOW.code,
            response_message=respone_status.FILE_TYPE_NOT_ALLOW.message).resp


@file_uploader_api.route('/uploadfile', methods=['POST'])
@token_required
def post():

    if 'file' not in request.files:
        print('No file part')
        return 200
    # files = request.files.getlist("file")
    file = request.files['file']
    # data = file.read()
    # data1 = files[0].read()
    # logger.info(f'data file ---:  {data} ++ {data1} , {type(file)} {type(files[0])}')

    # status, content_type = check_file_type(file.filename)
    status = 0
    # validate file type
    if status == 0:
        # file type allow


        # check file size
        # size_limit = check_file_size_limit(file)
        size_limit = 0
        # file size in limit
        if size_limit == 0:

            # TODO: force save new file with name is hash of content so if content the new file is same od file is will be same name .
            try:
                sign_client = request.environ['HTTP_SIGN_CLIENT']

            except:
                sign_client = ""
            file_data = file.read()
            logger.info(f'file ob type : {file_data}  {type(file)}')
            status, message = handle_upload_file_disk(file_data, sign_client, logger=logger)

            if status == 0:

                # check file name native have exits
                try:
                    # if record have in database
                    file_db = Files.query.filter_by(name=str(file.filename)).first()

                    if file_db is None:
                        # if name native record not exits and database
                        new_file_db_row = Files(name=str(file.filename), hash=str(message), time_modify=datetime.utcnow())
                        db.session.add(new_file_db_row)
                        db.session.commit()
                        logger.info(str(new_file_db_row.hash) + ":" + str(new_file_db_row.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                        return ResponseAPI(
                            respone_code=respone_status.SUCCESS.code,
                            response_message=respone_status.SUCCESS.message,
                            response_data=new_file_db_row.to_dict()).resp
                    else:
                        logger.error(str(file_db.name) + " exist", extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                        return ResponseAPI(
                            respone_code=respone_status.FILE_EXIST.code,
                            response_message=respone_status.FILE_EXIST.message,
                            response_data=file_db.to_dict()).resp

                except Exception as err:
                    db.session.rollback()
                    logger.info(f'Server Error when save file on DB reason: {err}')
                    return ResponseAPI(
                        respone_code=respone_status.SERVER_ERROR.code,
                        response_message=respone_status.SERVER_ERROR.message).resp

            elif status == -1:
                raise FileDoesNotExist(message)
            else:
                logger.info(f'Server Error when posting file')
                return ResponseAPI(
                    respone_code=respone_status.SERVER_ERROR.code,
                    response_message=respone_status.SERVER_ERROR.message,
                    response_data="Server Error when posting file").resp

        else:
            # file size > limit
            logger.info(f'File size max limit')
            return ResponseAPI(
                respone_code=respone_status.FILE_SIZE_LIMIT.code,
                response_message=respone_status.FILE_SIZE_LIMIT.message,
                response_data="File size max limit").resp

    # file type not allow
    else:
        return ResponseAPI(
            respone_code=respone_status.FILE_TYPE_NOT_ALLOW.code,
            response_message=respone_status.FILE_TYPE_NOT_ALLOW.message).resp


@file_uploader_api.route('/uploadfile', methods=['DELETE'])
@token_required
def delete():
    total_same_hashs = 0
    file_name = request.args['file_name']
    # validate file type
    status, _ = check_file_type(file_name)

    # file type allow
    if status == 0:
        try:
            # check file in database
            file_db = Files.query.filter_by(name=str(file_name)).first()

            if file_db:
                # Find all files contain same hash
                total_same_hashs = Files.query.filter_by(hash=file_db.hash).count()

                if total_same_hashs == 1:
                    # check file on disk
                    file_status, file_name = handle_delete_file_disk(file_db.hash)
                    # delete on DB
                    db.session.delete(file_db)
                    db.session.commit()
                    # file had deleted
                    if file_status == 0:
                        logger.info(f'{file_db.hash} + ":" + {file_db.name} has already deleted')
                        return ResponseAPI(
                            respone_code=respone_status.SUCCESS.code,
                            response_message=respone_status.SUCCESS.message,
                            response_data="Removed file " + file_name).resp
                    # file not found on disk
                    elif file_status == -1:
                        logger.info(f'{file_db.name}: File not found on Disk')
                        return ResponseAPI(
                            respone_code=respone_status.FILE_DOES_NOT_EXIST.code,
                            response_message=respone_status.FILE_DOES_NOT_EXIST.message,
                            response_data=file_db.to_dict()).resp

                    # file error
                    elif file_status == -2:
                        logger.info(f'Server Error when deleting file')
                        return ResponseAPI(
                            respone_code=respone_status.SERVER_ERROR.code,
                            response_message=respone_status.SERVER_ERROR.message,
                            response_data=file_db.to_dict()).resp

                elif total_same_hashs > 1:
                    # delete on DB
                    db.session.delete(file_db)
                    db.session.commit()
                    logger.info(f'{file_db.name} is deleted on DB')
                    return ResponseAPI(
                        respone_code=respone_status.SUCCESS.code,
                        response_message=respone_status.SUCCESS.message,
                        response_data=file_name + ": Only remove file on DB ").resp
            else:
                return ResponseAPI(
                    respone_code=respone_status.FILE_DOES_NOT_EXIST.code,
                    response_message=respone_status.FILE_DOES_NOT_EXIST.message).resp

        except Exception as e:
            # Need to rollback transactions uncompleted
            db.session.rollback()
            return ResponseAPI(
                respone_code=respone_status.SERVER_ERROR.code,
                response_message=respone_status.SERVER_ERROR.message).resp

    else:
        # file type not allow
        return ResponseAPI(
            respone_code=respone_status.FILE_TYPE_NOT_ALLOW.code,
            response_message=respone_status.FILE_TYPE_NOT_ALLOW.message).resp
