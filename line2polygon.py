import os
import json
import datetime


import numpy as np

from matplotlib import pyplot
from shapely.geometry import LineString
from descartes import PolygonPatch
from functools import reduce


from math import sqrt
# from figures import BLUE, GRAY, set_limits, plot_line
# from shapely.figures import BLUE

import pycocotools.mask as _mask
frPyObjects = _mask.frPyObjects

GM = (sqrt(5)-1.0)/2.0
W = 8.0
H = W*GM

def set_limits(ax, x0, xN, y0, yN):
    ax.set_xlim(x0, xN)
    ax.set_xticks(range(x0, xN+1))
    ax.set_ylim(y0, yN)
    ax.set_yticks(range(y0, yN+1))
    ax.set_aspect("equal")

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class line2segment:
    def __init__(self):
        self.path = input('annotations: ')

        self.item_dict = dict(
            item =[]
        )
        self.polyline = dict(
            info=dict(
                description=None,
                url=None,
                version=None,
                year=datetime.datetime.now().year,
                contributor=None,
                date_created=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            ),
            licenses=[dict(url=None, id=1, name=None, )],
            images=[
                # license, url, file_name, height, width, date_captured, id
            ],
            type="instances",
            annotations=[
                # segmentation, area, iscrowd, image_id, bbox, category_id, id
            ],
            categories=[
                # supercategory, id, name
                {
                    'supercategory': None,
                    'id': 1,
                    'name': '도로균열'

                }
            ],
        )

        self.polygon_obj =[]
        self.getJson_f(self.path)

    #경로 안 json 파일 읽기
    def getJson_f(self, path):
        file_list = os.listdir(path)
        for file_ in file_list:
            file_ = os.path.join(path, file_)
            if os.path.isdir(file_):
                self.getJson_f(file_)
            else:
                if '.json' in file_:
                    print(file_)
                    self.readJson(file_)
        self.writeDict()
        self.writeJson()

    def readJson(self, j_file):
        area =_mask.area
        with open(j_file, 'r', encoding='UTF8') as f:
            json_data = json.load(f)
        items = [i for i in json_data['items']]
        for i in items:
            for j in i['annotations']:
                if j['type'] == 'polyline':
                    point = self.getPolygon(j['points'])
                    if type(point) == list:
                        for multi in point:
                            coord = list(reduce(lambda x, y: x + y, multi))
                            rs = frPyObjects(np.array([coord]), 1080, 1920)
                            self.item_dict['item'].append(
                                dict(
                                    id =i['id'],
                                    segment = coord,
                                    bbox = self.getBbox(coord),
                                    area = area(rs)
                                )
                            )
                    else:
                        coord = list(reduce(lambda x, y: x + y, list(point.exterior.coords)))
                        rs = frPyObjects(np.array([coord]), 1080, 1920)
                        self.item_dict['item'].append(
                            dict(
                                id =i['id'],
                                segment = coord,
                                bbox = self.getBbox(coord),
                                # area = np.float(area(rs))
                                area = area(rs)
                            )
                        )

    def getPolygon(self, coordinates):
        #polyline 좌표값 (x,y)로 변환
        coor = []
        length = [i*2 for i in range(len(coordinates)//2)]
        for i in length:
            coor.append((coordinates[i],coordinates[i+1]))
        line = LineString(coor)
        dilated = line.buffer(10.0,  cap_style=2)
        if dilated.type == 'MultiPolygon':
            self.polygon_obj = [x.exterior.coords for x in dilated.geoms]
        else:
            self.polygon_obj = dilated
        return self.polygon_obj

    #line to polygon 좌표 구하기
    def getSegment(self, list_):
        ori_list = []
        new_list = []
        plus_list = []
        minus_list = []
        for i in range(len(list_)):
            if i % 2 ==1:
                plus = list_[i] + 10
                minus = list_[i] - 10
                if len(new_list) !=0 and new_list[len(new_list)-2] != list_[i-1]:
                    # new_list.extend([list_[i-1], minus, list_[i-1], plus])
                    new_list.extend([list_[i-1], minus])
                    plus_list.append([list_[i-1], plus])
                else:
                    new_list.extend([list_[i-1], plus, list_[i-1], minus])

        plus_list.reverse()
        for i in plus_list:
            new_list.extend(i)
        ori_list.extend(new_list)

        return ori_list

    #bbox 값
    def getBbox(self, list_):
        x = [i for i in list_ if list_.index(i) % 2 == 0]
        y = [i for i in list_ if list_.index(i) % 2 == 1]
        return [min(x), min(y), max(x) - min(x), max(y) - min(y)]

    def writeDict(self):
        img_dict ={}
        img = [i['id'] for i in self.item_dict['item']]
        img = list(set(img))
        for i in img:
            img_dict[i] = img.index(i)+1
            self.polyline['images'].append(
                dict(
                    license=0,
                    url=None,
                    file_name=i+'.jpg',
                    height=1080,
                    width=1920,
                    date_captured=None,
                    id=len(self.polyline['images']) + 1
                    # id=img.index(i)+1
                )
            )
        for i in self.item_dict['item']:
            self.polyline["annotations"].append(
                dict(
                    id=len(self.polyline["annotations"]) + 1,
                    image_id=img_dict[i['id']],
                    category_id= 1,
                    segmentation=[i['segment']],
                    area=i['area'],
                    bbox=i['bbox'],
                    iscrowd=0,
                )
            )

    def writeJson(self):
        file_name = 'C:\\Users\\KST2106-10\\Desktop\\새 폴더 (2)\\annotations.json'
        print('write file: ' + file_name)
        with open(file_name, "w", encoding='UTF8') as f:
            json.dump(self.polyline, f, ensure_ascii=False, cls=NumpyEncoder)



if __name__ == "__main__":
    line2segment()


