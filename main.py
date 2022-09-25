import time

import cv2 as cv
import vk_api
import urllib
import numpy as np
import sqlite3

VK_API_TOKEN = ''  # Vk token
MAIN_USER_ID = 0  # User whose friends will be checked
DATABASE_NAME = 'posts.db'

con = sqlite3.connect(DATABASE_NAME)
vk_session = vk_api.VkApi(token=VK_API_TOKEN)
vk = vk_session.get_api()
while True:
    friends = vk.friends.get(user_id=MAIN_USER_ID)
    for friend in friends['items']:
        posts = vk.wall.get(owner_id=friend)

        for items in posts['items']:
            post_id = items['id']
            owner_id = items['owner_id']
            cur = con.cursor()
            row = cur.execute(f"SELECT * FROM posts WHERE owner_id = '{friend}' and post_id = '{post_id}'")
            row = row.fetchone()
            if row == None:
                cur = con.cursor()
                cur.execute(f"INSERT INTO posts VALUES ('{post_id}','{owner_id}')")
                con.commit()

                isFounded = False
                if (not isFounded) and ('attachments' in items.keys() or 'copy_history' in items.keys()):
                    if 'attachments' in items.keys():
                        attachments = items['attachments']
                    elif 'attachments' in items['copy_history'][0].keys():
                        attachments = items['copy_history'][0]['attachments']
                    isFoundedCat = False
                    for attachment in attachments:
                        if not isFoundedCat:
                            if attachment['type'] == 'photo':
                                photo = attachment['photo']['sizes'][-1]['url']
                                resp = urllib.request.urlopen(photo)
                                image = np.asarray(bytearray(resp.read()), dtype="uint8")
                                image = cv.imdecode(image, cv.IMREAD_COLOR)
                                net = cv.dnn_DetectionModel('frozen_inference_graph.pb',
                                                            'ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt')
                                net.setInputSize(320, 320)
                                net.setInputScale(1.0 / 127.5)
                                net.setInputMean((127.5, 127.5, 127.5))
                                net.setInputSwapRB(True)

                                classNames = []
                                classFile = 'coco.names'
                                with open(classFile, 'rt') as f:
                                    classNames = f.read().rstrip('\n').split('\n')
                                # frame = cv.imread('5YfAWf4qLAo.jpg')

                                classes = confidences = boxes = None
                                classes, confidences, boxes = net.detect(image, confThreshold=0.5)

                                if classes is not None and len(classes) > 0:
                                    for classId, confidence, box in zip(classes.flatten(), confidences.flatten(),
                                                                        boxes):
                                        if classId == 17:
                                            cv.rectangle(image, box, color=(0, 255, 0))
                                            cv.rectangle(image, box, color=(0, 255, 0), thickness=2)
                                            cv.putText(image, classNames[classId - 2].upper(),
                                                       (box[0] + 10, box[1] + 30),
                                                       cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                                            cv.putText(image, str(round(confidence * 100, 2)),
                                                       (box[0] + 200, box[1] + 30),
                                                       cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                                            vk.wall.createComment(owner_id=int(friend), post_id=post_id,
                                                                  message='Какой красивый котик!')
                                            print('Котик найден', friend, post_id)
                                            isFoundedCat = True
                                            break

con.close()
