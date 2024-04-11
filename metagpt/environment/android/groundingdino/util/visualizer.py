# -*- coding: utf-8 -*-
"""
@File    :   visualizer.py
@Time    :   2022/04/05 11:39:33
@Author  :   Shilong Liu 
@Contact :   slongliu86@gmail.com
"""

import datetime
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import torch
from matplotlib import transforms
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from pycocotools import mask as maskUtils


def renorm(
    img: torch.FloatTensor, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
) -> torch.FloatTensor:
    # img: tensor(3,H,W) or tensor(B,3,H,W)
    # return: same as img
    assert img.dim() == 3 or img.dim() == 4, "img.dim() should be 3 or 4 but %d" % img.dim()
    if img.dim() == 3:
        assert img.size(0) == 3, 'img.size(0) shoule be 3 but "%d". (%s)' % (
            img.size(0),
            str(img.size()),
        )
        img_perm = img.permute(1, 2, 0)
        mean = torch.Tensor(mean)
        std = torch.Tensor(std)
        img_res = img_perm * std + mean
        return img_res.permute(2, 0, 1)
    else:  # img.dim() == 4
        assert img.size(1) == 3, 'img.size(1) shoule be 3 but "%d". (%s)' % (
            img.size(1),
            str(img.size()),
        )
        img_perm = img.permute(0, 2, 3, 1)
        mean = torch.Tensor(mean)
        std = torch.Tensor(std)
        img_res = img_perm * std + mean
        return img_res.permute(0, 3, 1, 2)


class ColorMap:
    def __init__(self, basergb=[255, 255, 0]):
        self.basergb = np.array(basergb)

    def __call__(self, attnmap):
        # attnmap: h, w. np.uint8.
        # return: h, w, 4. np.uint8.
        assert attnmap.dtype == np.uint8
        h, w = attnmap.shape
        res = self.basergb.copy()
        res = res[None][None].repeat(h, 0).repeat(w, 1)  # h, w, 3
        attn1 = attnmap.copy()[..., None]  # h, w, 1
        res = np.concatenate((res, attn1), axis=-1).astype(np.uint8)
        return res


def rainbow_text(x, y, ls, lc, **kw):
    """
    Take a list of strings ``ls`` and colors ``lc`` and place them next to each
    other, with text ls[i] being shown in color lc[i].

    This example shows how to do both vertical and horizontal text, and will
    pass all keyword arguments to plt.text, so you can set the font size,
    family, etc.
    """
    t = plt.gca().transData
    fig = plt.gcf()
    plt.show()

    # horizontal version
    for s, c in zip(ls, lc):
        text = plt.text(x, y, " " + s + " ", color=c, transform=t, **kw)
        text.draw(fig.canvas.get_renderer())
        ex = text.get_window_extent()
        t = transforms.offset_copy(text._transform, x=ex.width, units="dots")

    # #vertical version
    # for s,c in zip(ls,lc):
    #     text = plt.text(x,y," "+s+" ",color=c, transform=t,
    #             rotation=90,va='bottom',ha='center',**kw)
    #     text.draw(fig.canvas.get_renderer())
    #     ex = text.get_window_extent()
    #     t = transforms.offset_copy(text._transform, y=ex.height, units='dots')


class COCOVisualizer:
    def __init__(self, coco=None, tokenlizer=None) -> None:
        self.coco = coco

    def visualize(self, img, tgt, caption=None, dpi=180, savedir="vis"):
        """
        img: tensor(3, H, W)
        tgt: make sure they are all on cpu.
            must have items: 'image_id', 'boxes', 'size'
        """
        plt.figure(dpi=dpi)
        plt.rcParams["font.size"] = "5"
        ax = plt.gca()
        img = renorm(img).permute(1, 2, 0)
        # if os.environ.get('IPDB_SHILONG_DEBUG', None) == 'INFO':
        #     import ipdb; ipdb.set_trace()
        ax.imshow(img)

        self.addtgt(tgt)

        if tgt is None:
            image_id = 0
        elif "image_id" not in tgt:
            image_id = 0
        else:
            image_id = tgt["image_id"]

        if caption is None:
            savename = "{}/{}-{}.png".format(
                savedir, int(image_id), str(datetime.datetime.now()).replace(" ", "-")
            )
        else:
            savename = "{}/{}-{}-{}.png".format(
                savedir, caption, int(image_id), str(datetime.datetime.now()).replace(" ", "-")
            )
        print("savename: {}".format(savename))
        os.makedirs(os.path.dirname(savename), exist_ok=True)
        plt.savefig(savename)
        plt.close()

    def addtgt(self, tgt):
        """ """
        if tgt is None or not "boxes" in tgt:
            ax = plt.gca()

            if "caption" in tgt:
                ax.set_title(tgt["caption"], wrap=True)

            ax.set_axis_off()
            return

        ax = plt.gca()
        H, W = tgt["size"]
        numbox = tgt["boxes"].shape[0]

        color = []
        polygons = []
        boxes = []
        for box in tgt["boxes"].cpu():
            unnormbbox = box * torch.Tensor([W, H, W, H])
            unnormbbox[:2] -= unnormbbox[2:] / 2
            [bbox_x, bbox_y, bbox_w, bbox_h] = unnormbbox.tolist()
            boxes.append([bbox_x, bbox_y, bbox_w, bbox_h])
            poly = [
                [bbox_x, bbox_y],
                [bbox_x, bbox_y + bbox_h],
                [bbox_x + bbox_w, bbox_y + bbox_h],
                [bbox_x + bbox_w, bbox_y],
            ]
            np_poly = np.array(poly).reshape((4, 2))
            polygons.append(Polygon(np_poly))
            c = (np.random.random((1, 3)) * 0.6 + 0.4).tolist()[0]
            color.append(c)

        p = PatchCollection(polygons, facecolor=color, linewidths=0, alpha=0.1)
        ax.add_collection(p)
        p = PatchCollection(polygons, facecolor="none", edgecolors=color, linewidths=2)
        ax.add_collection(p)

        if "strings_positive" in tgt and len(tgt["strings_positive"]) > 0:
            assert (
                len(tgt["strings_positive"]) == numbox
            ), f"{len(tgt['strings_positive'])} = {numbox}, "
            for idx, strlist in enumerate(tgt["strings_positive"]):
                cate_id = int(tgt["labels"][idx])
                _string = str(cate_id) + ":" + " ".join(strlist)
                bbox_x, bbox_y, bbox_w, bbox_h = boxes[idx]
                # ax.text(bbox_x, bbox_y, _string, color='black', bbox={'facecolor': 'yellow', 'alpha': 1.0, 'pad': 1})
                ax.text(
                    bbox_x,
                    bbox_y,
                    _string,
                    color="black",
                    bbox={"facecolor": color[idx], "alpha": 0.6, "pad": 1},
                )

        if "box_label" in tgt:
            assert len(tgt["box_label"]) == numbox, f"{len(tgt['box_label'])} = {numbox}, "
            for idx, bl in enumerate(tgt["box_label"]):
                _string = str(bl)
                bbox_x, bbox_y, bbox_w, bbox_h = boxes[idx]
                # ax.text(bbox_x, bbox_y, _string, color='black', bbox={'facecolor': 'yellow', 'alpha': 1.0, 'pad': 1})
                ax.text(
                    bbox_x,
                    bbox_y,
                    _string,
                    color="black",
                    bbox={"facecolor": color[idx], "alpha": 0.6, "pad": 1},
                )

        if "caption" in tgt:
            ax.set_title(tgt["caption"], wrap=True)
            # plt.figure()
            # rainbow_text(0.0,0.0,"all unicorns poop rainbows ! ! !".split(),
            #         ['red', 'orange', 'brown', 'green', 'blue', 'purple', 'black'])

        if "attn" in tgt:
            # if os.environ.get('IPDB_SHILONG_DEBUG', None) == 'INFO':
            #     import ipdb; ipdb.set_trace()
            if isinstance(tgt["attn"], tuple):
                tgt["attn"] = [tgt["attn"]]
            for item in tgt["attn"]:
                attn_map, basergb = item
                attn_map = (attn_map - attn_map.min()) / (attn_map.max() - attn_map.min() + 1e-3)
                attn_map = (attn_map * 255).astype(np.uint8)
                cm = ColorMap(basergb)
                heatmap = cm(attn_map)
                ax.imshow(heatmap)
        ax.set_axis_off()

    def showAnns(self, anns, draw_bbox=False):
        """
        Display the specified annotations.
        :param anns (array of object): annotations to display
        :return: None
        """
        if len(anns) == 0:
            return 0
        if "segmentation" in anns[0] or "keypoints" in anns[0]:
            datasetType = "instances"
        elif "caption" in anns[0]:
            datasetType = "captions"
        else:
            raise Exception("datasetType not supported")
        if datasetType == "instances":
            ax = plt.gca()
            ax.set_autoscale_on(False)
            polygons = []
            color = []
            for ann in anns:
                c = (np.random.random((1, 3)) * 0.6 + 0.4).tolist()[0]
                if "segmentation" in ann:
                    if type(ann["segmentation"]) == list:
                        # polygon
                        for seg in ann["segmentation"]:
                            poly = np.array(seg).reshape((int(len(seg) / 2), 2))
                            polygons.append(Polygon(poly))
                            color.append(c)
                    else:
                        # mask
                        t = self.imgs[ann["image_id"]]
                        if type(ann["segmentation"]["counts"]) == list:
                            rle = maskUtils.frPyObjects(
                                [ann["segmentation"]], t["height"], t["width"]
                            )
                        else:
                            rle = [ann["segmentation"]]
                        m = maskUtils.decode(rle)
                        img = np.ones((m.shape[0], m.shape[1], 3))
                        if ann["iscrowd"] == 1:
                            color_mask = np.array([2.0, 166.0, 101.0]) / 255
                        if ann["iscrowd"] == 0:
                            color_mask = np.random.random((1, 3)).tolist()[0]
                        for i in range(3):
                            img[:, :, i] = color_mask[i]
                        ax.imshow(np.dstack((img, m * 0.5)))
                if "keypoints" in ann and type(ann["keypoints"]) == list:
                    # turn skeleton into zero-based index
                    sks = np.array(self.loadCats(ann["category_id"])[0]["skeleton"]) - 1
                    kp = np.array(ann["keypoints"])
                    x = kp[0::3]
                    y = kp[1::3]
                    v = kp[2::3]
                    for sk in sks:
                        if np.all(v[sk] > 0):
                            plt.plot(x[sk], y[sk], linewidth=3, color=c)
                    plt.plot(
                        x[v > 0],
                        y[v > 0],
                        "o",
                        markersize=8,
                        markerfacecolor=c,
                        markeredgecolor="k",
                        markeredgewidth=2,
                    )
                    plt.plot(
                        x[v > 1],
                        y[v > 1],
                        "o",
                        markersize=8,
                        markerfacecolor=c,
                        markeredgecolor=c,
                        markeredgewidth=2,
                    )

                if draw_bbox:
                    [bbox_x, bbox_y, bbox_w, bbox_h] = ann["bbox"]
                    poly = [
                        [bbox_x, bbox_y],
                        [bbox_x, bbox_y + bbox_h],
                        [bbox_x + bbox_w, bbox_y + bbox_h],
                        [bbox_x + bbox_w, bbox_y],
                    ]
                    np_poly = np.array(poly).reshape((4, 2))
                    polygons.append(Polygon(np_poly))
                    color.append(c)

            # p = PatchCollection(polygons, facecolor=color, linewidths=0, alpha=0.4)
            # ax.add_collection(p)
            p = PatchCollection(polygons, facecolor="none", edgecolors=color, linewidths=2)
            ax.add_collection(p)
        elif datasetType == "captions":
            for ann in anns:
                print(ann["caption"])
