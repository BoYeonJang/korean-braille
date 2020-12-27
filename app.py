from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import os
import boto3
from pygame import mixer

import natsort
import unicode
from PIL import Image
import keras.models

app = Flask(__name__)

b = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ', 'ㄱ', 'ㄴ', 'ㄹ',
     'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅏ', 'ㅑ', 'ㅓ', 'ㅕ', 'ㅗ', 'ㅛ', 'ㅜ', 'ㅠ', 'ㅡ',
     'ㅣ', 'ㅐ', 'ㅔ', 'ㅖ', 'ㅢ', 'ㅚ', 'ㅘ', 'ㅝ', '가', '다', '사', '자', '억', '언', '얼',
     '연', '열', '영']

model = keras.models.load_model('BrailleNet.h5')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/play', methods=['GET', 'POST'])
def play():
    if request.method == 'POST':
        result = request.form['result2']
        mixer.init()
        mixer.music.load('./tts.mp3')
        mixer.music.play()
    return render_template('index.html', rst=result)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files['profile']
        f.save(secure_filename(f.filename))
    img = Image.open('./' + f.filename)

    if f.filename == "jum.png":
        x = [img.crop((0, 0, 60, img.size[1])), img.crop((60, 0, 120, img.size[1])), img.crop((130, 0, 190, img.size[1])),
             img.crop((190, 20, 260, 110)), img.crop((270, 0, 320, img.size[1])), img.crop((330, 25, 390, 110)),
             img.crop((400, 20, 460, 110)), img.crop((470, 20, 520, 110))]
    else:
        x = [img.crop((20, 0, 60, img.size[1])), img.crop((60, 0, 110, img.size[1])), img.crop((110, 0, 150, img.size[1])),
             img.crop((160, 0, 200, img.size[1])), img.crop((200, 0, 250, img.size[1])), img.crop((250, 0, 290, img.size[1])),
             img.crop((290, 0, 340, img.size[1])), img.crop((340, 0, 380, img.size[1])), img.crop((390, 0, 430, img.size[1])),
             img.crop((435, 0, img.size[0], img.size[1]))]

    filepath = './test'
    if os.path.exists(filepath):
        for file in os.scandir(filepath):
            os.remove(file.path)
    for i in range(len(x)):
        x[i].save('./test/' + str((i + 1)) + '.png')
    result = predict_img('./test')

    polly = boto3.Session(
        aws_access_key_id='AKIAZT6EVI2QXM7Z6NVH',
        aws_secret_access_key='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',
        region_name='ap-northeast-2').client('polly')
    # polly = client("polly", region_name="ap-northeast-2")
    response = polly.synthesize_speech(
        Text=result,
        OutputFormat="mp3",
        VoiceId="Seoyeon")

    stream = response.get("AudioStream")

    with open('tts.mp3', 'wb') as f:
        data = stream.read()
        f.write(data)
    return render_template('index.html', rst=result)


def predict_img(path):
    img_list = os.listdir(path)
    img_list = natsort.natsorted(img_list, reverse=False)
    result_list = []
    for img_file in img_list:
        if img_file.endswith('.png'):
            img = cv2.imread(os.path.join(path, img_file), cv2.IMREAD_COLOR)
            new_img = cv2.resize(img, dsize=(36, 36))
            new_img = new_img.reshape(1, 36, 36, 3)
            result = np.argmax(model.predict(new_img), axis=1)
            print(img_file, '-->', result[0] + 1)
            result_list.append(result[0])
    return alpha(result_list)


def alpha(result_list):
    han_list = ''
    print(result_list)
    if 28 <= result_list[0] <= 44:
        han_list += 'ㅇ'
    for i, result in enumerate(result_list):
        if i > 0:
            z = (result_list[i - 1] >= 21)  # 앞에 글자 모음
            b2 = (result_list[i - 1] <= 37)  # 앞에글자 모음

            c = (result_list[i] >= 21)  # 현재글자 모음
            d = (result_list[i] <= 37)  # 현재 글자 모음

            e = (result_list[i - 1] >= 14)  # 앞에 글자 종성
            f = (result_list[i - 1] <= 20)  # 앞에 글자 종성

            # 현재 글자 초성
            g = (result_list[i] >= 1)
            h = (result_list[i] <= 13)
            # 현재 글자 종성
            j = (result_list[i] >= 14)
            k = (result_list[i] <= 20)
            # 앞에 글자 초성
            l = (result_list[i - 1] >= 1)
            m = (result_list[i - 1] <= 13)
            o = (i == (len(result_list) - 1))

            if (z & b2 & c & d) | (c & d & e & f):
                han_list += 'ㅇ'
            elif (j & k & l & m) | (g & h & l & m):
                han_list += 'ㅏ'
            if result == 42:
                han_list = han_list[:-1]
                han_list += '건'
            else:
                han_list += b[result]

            if g & h & o:
                han_list += 'ㅏ'
        elif i == 0:
            han_list += b[result]
    result = unicode.join_jamos(han_list)
    return result


if __name__ == '__main__':
    app.run(host="ec2-52-79-251-207.ap-northeast-2.compute.amazonaws.com", port='5000', debug=True)
