import os, logging
from datetime import datetime

from flask import Flask, request


from flask import Response
from flask.views import MethodView

from exceptions import (
    FileDoesNotExist,
    DoesNotExist,
    FileTypeNotAllow,
    ServerError,
    FileSizeLimit,
    FileNotSync)

from utils import (
    check_file_size_limit,
    check_file_type,
    handle_delete_file_disk,
    handle_read_file_disk,
    handle_upload_file_disk
)

import respone_status
from base import ResponseAPI
from authentication import check_auth_basic

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# from files import Files
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm.exc import NoResultFound

db = SQLAlchemy(app)

# from files import db  # <-- this needs to be placed after app is created
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

console = logging.StreamHandler()
logger = logging.getLogger("file_upload_API")
logger.addHandler(console)

logging.basicConfig(
    format='%(module)s : %(lineno)s : %(levelname)-8s - message: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# fs_mixin = FlaskSerialize(db)
from sqlalchemy.sql import func
class Files(db.Model, SerializerMixin):

    name = db.Column(db.String(100), nullable=False, primary_key=True)
    hash = db.Column(db.String(32), nullable=False)
    time_upload = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_modify = db.Column(db.DateTime(timezone=True), nullable=True)

from sqlalchemy import inspect
def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

@app.route('/')
def hello():
    return '<h1>Hello, World!</h1>'


@check_auth_basic
@app.route('/viewfile', methods=['GET'])
def get():
    file_name = request.args['file_name']
    status , content_type = check_file_type(file_name)

    # validate file type
    if status == 0:
        # file type allow

        # check file in database
        try:
            file_db = Files.query.filter_by(name=file_name).first()
            print(file_db.hash)
        except Exception as e:
            return {"Status": 200, "Message": "File not found" }

        # check file on disk
        status, file_content = handle_read_file_disk(file_db.name)

        #file okie
        if status == 0:
            print(f'{file_db.name} "client_ip" : {request.environ["REMOTE_ADDR"]}')
            response = Response(file_content, content_type=str(content_type))
            # response['Content-Disposition'] = 'inline; filename=' + file_db.name
            return response

        # file not found
        elif status == -1:
            raise FileNotSync(logger = logging.getLogger("data"))

        # file error
        elif status == -2:
            raise ServerError(logger = logging.getLogger("data"))

    else:
        # file type not allow
        raise FileTypeNotAllow(logger = logging.getLogger("data"))


@check_auth_basic
@app.route('/uploadfile', methods=['POST'])
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
                    # file_serializer = FileSerializer(file_db)files
                    if file_db is None:
                        # if name native record not exits and database
                        file_db = Files(name=str(file.filename), hash=str(message), time_modify=datetime.now())
                        db.session.add(file_db)
                        db.session.commit()
                        # file_serializer = FileSerializer(file_db)
                        logger.info(str(file_db.hash) + ":" + str(file_db.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                        return ResponseAPI(
                            respone_code=respone_status.SUCCESS.code,
                            response_message="create " + respone_status.SUCCESS.message,
                            response_data=file_db.to_dict()).resp  
                    else:                      
                        logger.error(str(file_db.name) + " exist", extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                        return ResponseAPI(
                            respone_code=respone_status.FILE_EXIST.code,
                            response_message=respone_status.FILE_EXIST.message,
                            response_data=file_db.to_dict()).resp

                except Exception as e:
                    db.session.rollback()
                    raise ServerError(str(e))

            elif status == -1:
                raise FileDoesNotExist(message)
            else:
                raise ServerError(message)

        else:
            # file size > limit
            raise FileSizeLimit(str(file.filename))

    # file type not allow
    else:
        raise FileTypeNotAllow(str(file.filename))


@check_auth_basic
@app.route('/uploadfile', methods=['DELETE'])
def delete():

    file_name = request.args['file_name']
    # validate file type
    status, _ = check_file_type(file_name)

    # file type allow    
    if status == 0:
        # check file in database

        file_db = Files.query.filter_by(name=str(file_name)).first()

        if file_db:
            # check file on disk and delete on DB
            file_status, file_name = handle_delete_file_disk(file_db.hash)

            # file had deleted
            if file_status == 0:
                logger.info(f'{file_db.hash} + ":" + {file_db.name} has already deleted')

            # file not found
            elif file_status == -1:
                return {"Status": 200, "Message": "File not found" }

            # file error
            elif file_status == -2:
                raise ServerError(file_name)


            try:
                file_db = Files.query.filter_by(name=str(file_name)).first()
                db.session.delete(file_db)
                db.session.commit()           
                logger.info(f'{file_db.name} is deleted on DB')
                return ResponseAPI(
                    respone_code=respone_status.SUCCESS.code,
                    response_message=respone_status.SUCCESS.message,
                    response_data="remove file " + file_name).resp
            except Exception as e:
                db.session.rollback()
                raise ServerError(e)

    else:
        # file type not allow
        raise FileTypeNotAllow(file_name)
    

class FileViewSet(MethodView):

    # logger = logging.getLogger("data")

    @check_auth_basic
    def get(self, request, name):


        status , content_type = check_file_type(name)

        # validate file type
        if status == 0:
            # file type allow

            # check file in database
            try:
                file_db = Files.objects.get(name=name)
            except Files.DoesNotExist as e:
                raise DoesNotExist(name)

            # check file on disk
            status, file_content = handle_read_file_disk(file_db.hash)

            #file okie
            if status == 0:
                self.logger.info(str(file_db.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                response = Response(file_content, content_type=str(content_type))
                response['Content-Disposition'] = 'inline; filename=' + file_db.name
                return response

            # file not found
            elif status == -1:
                raise FileNotSync(name)

            # file error
            elif status == -2:
                raise ServerError(name)

        else:
            # file type not allow
            raise FileTypeNotAllow(name)

    @check_auth_basic
    def delete(self, request, name):

        status, content_type = check_file_type(name)

        # validate file type
        if status == 0:
            # file type allow


            # check file in database
            record_link_file = 0
            try:
                file_db = Files.objects.get(name=name)
                record_link_file = Files.objects.filter(hash=file_db.hash).count()
            except Files.DoesNotExist:
                raise DoesNotExist(name)

            if record_link_file == 1:

                file_db = Files.objects.get(name=name)

                # check file on disk
                status, file_name = handle_delete_file_disk(file_db.hash)

                file_db.delete()

                # file had deleted
                if status == 0:
                    self.logger.info(str(file_db.hash) + ":" + str(file_db.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                    return ResponseAPI(
                        respone_code=respone_status.SUCCESS.code,
                        response_message=respone_status.SUCCESS.message,
                        response_data="remove file " + name).resp

                # file not found
                elif status == -1:
                    raise FileNotSync(name)

                # file error
                elif status == -2:
                    raise ServerError(name)

            elif record_link_file > 1:
                try:
                    Files.objects.get(name=name).delete()
                    self.logger.info("None" + ":" + str(file_db.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                    return ResponseAPI(
                        respone_code=respone_status.SUCCESS.code,
                        response_message=respone_status.SUCCESS.message,
                        response_data="remove file " + name).resp
                except Exception as e:
                    raise ServerError(e.message)
            else:
                raise ServerError(name)

        else:
            # file type not allow
            raise FileTypeNotAllow(name)

class FileUploadViewSet(MethodView):

    logger = logging.getLogger("data")

    @check_auth_basic
    def put(self, request):

        # just get file first (can extend with upload multiple file)
        list_file_object = [obj for obj in request.FILES.values()]

        status, content_type = check_file_type(list_file_object[0].name)

        # validate file type
        if status == 0:
            # file type allow


            # check file size
            size_limit = check_file_size_limit(list_file_object[0])
            if size_limit == 0:
                # file size in limit
                try:
                    sign_client = request.environ['HTTP_SIGN_CLIENT']
                except:
                    sign_client = ""
                status, message = handle_upload_file_disk(list_file_object[0], sign_client)

                if status == 0:
                    # check file name native have exits
                    try:
                        # if record have in database

                        file_db = Files.objects.get(name=str(list_file_object[0].name))
                        file_db.hash = message
                        file_db.save()
                        # file_serializer = FileSerializer(file_db)

                        self.logger.info(str(file_db.hash) + ":" + str(file_db.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})

                        return ResponseAPI(
                            respone_code=respone_status.SUCCESS.code,
                            response_message="update " + respone_status.SUCCESS.message,
                            response_data=file_db.to_dic()).resp


                    except Files.DoesNotExist as e:

                        # if name native record not exits and database
                        raise DoesNotExist(str(list_file_object[0].name))

                    except Exception as e:
                        raise ServerError(str(e.message))

                elif status == -1:
                    raise FileDoesNotExist(message)
                else:
                    raise ServerError(message)

            else:
                # file size > limit
                raise FileSizeLimit(str(list_file_object[0].name))

        else:
            # file type not allow
            raise FileTypeNotAllow(str(list_file_object[0].name))

    @check_auth_basic
    def post(self, request):

        # just get file first (can extend with upload multiple file)
        list_file_object = [obj for obj in request.FILES.values()]

        status, content_type = check_file_type(list_file_object[0].name)

        # validate file type
        if status == 0:
            # file type allow


            # check file size
            size_limit = check_file_size_limit(list_file_object[0])

            # file size in limit
            if size_limit == 0:

                # TODO: force save new file with name is hash of content so if content the new file is same od file is will be same name .
                try:
                    sign_client = request.environ['HTTP_SIGN_CLIENT']
                except:
                    sign_client = ""

                status, message = handle_upload_file_disk(list_file_object[0], sign_client)

                if status == 0:

                    # check file name native have exits
                    try:
                        # if record have in database

                        file_db = Files.objects.get(name=str(list_file_object[0].name))
                        # file_serializer = FileSerializer(file_db)

                        self.logger.error(str(file_db.name) + " exist", extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                        return ResponseAPI(
                            respone_code=respone_status.FILE_EXIST.code,
                            response_message=respone_status.FILE_EXIST.message,
                            response_data=file_db.to_dic()).resp

                    except Files.DoesNotExist as e:

                        # if name native record not exits and database
                        file_db = Files(name=str(list_file_object[0].name), hash=str(message))
                        file_db.save()
                        # file_serializer = FileSerializer(file_db)
                        self.logger.info(str(file_db.hash) + ":" + str(file_db.name), extra={"client_ip": request.environ['REMOTE_ADDR'], "user": None})
                        return ResponseAPI(
                            respone_code=respone_status.SUCCESS.code,
                            response_message="create " + respone_status.SUCCESS.message,
                            response_data=file_db.to_dic()).resp

                    except Exception as e:
                        raise ServerError(str(e.message))

                elif status == -1:
                    raise FileDoesNotExist(message)
                else:
                    raise ServerError(message)

            else:
                # file size > limit
                raise FileSizeLimit(str(list_file_object[0].name))

        # file type not allow
        else:
            raise FileTypeNotAllow(str(list_file_object[0].name))


app.add_url_rule('/view/', view_func=FileViewSet.as_view(name="view"))
app.add_url_rule('/upload/', view_func=FileUploadViewSet.as_view(name="upload"))

if __name__ == '__main__':
    manager.run()