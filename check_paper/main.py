from flask import Flask, request, send_from_directory, jsonify
import os
import re
from pymilvus import Collection
from werkzeug.utils import secure_filename
import datetime
from concurrent.futures import ThreadPoolExecutor

from check_contract import process_file
from milvus_test import connect_to_milvus, COLLECTION_NAME

executor = ThreadPoolExecutor(max_workers=1)

app = Flask(__name__)

# 设置用于存储上传和处理后的文件的目录
UPLOAD_FOLDER = 'uploads/'
PROCESSED_FOLDER = 'processed/'


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['docx']


@app.route('/upload', methods=['POST'])
def upload_file():
    file_objs = request.files.getlist('file')

    if not file_objs:
        return jsonify(error="No file uploaded or selected"), 400

    for file in file_objs:
        if file and allowed_file(file.filename):
            pass
        else:
            return jsonify(error=f"Invalid file format for {file.filename}, only DOCX files are allowed."), 400

    file_data = []
    for file in file_objs:

        filename = file.filename
        print("filename:",filename)
        # 正则表达式匹配文件名

        # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        # unique_filename = f"{timestamp}.{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_data.append({'file_path': file_path, "unique_filename": filename})

    executor.submit(process_file, file_data)

    return jsonify(message="Files uploaded successfully"), 200


@app.route('/static/<filename>')
def static_files(filename):
    return send_from_directory('processed', filename)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)
    app.run(host='0.0.0.0', port=5000, debug=True)