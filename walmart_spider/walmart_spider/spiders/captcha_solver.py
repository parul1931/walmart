#!/usr/bin/python
try:
    import numpy as np
    import cv2
except Exception as e:
    print '!!!!!!!!Captcha breaker is not available due to: %s' % e
    class CaptchaBreakerWrapper(object):
        @staticmethod
        def solve_captcha(url):
            msg("CaptchaBreaker in not available for url: %s" % url,
                level=WARNING)
            return None

import sys
import os
import re

import urllib


class CaptchaBreaker:

    HEIGHT = 50
    WIDTH = 50

    ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    

    knn = None

    def __init__(self, train_data, output_train_data_file=None, from_dir=False):
        if from_dir:
            self.knn = self.train_from_dir(train_data, output_train_data_file)
        else:
            self.knn = self.train_from_file(train_data)

    def letter_to_number(self, letter):
        return self.ALPHABET.index(letter)

    def number_to_letter(self, number):
        return self.ALPHABET[number]

    def clean_image(self, image, trim=False):

        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,1,11,2)
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
        eroded = cv2.erode(thresh,kernel,iterations = 1)
        contours,hierarchy = cv2.findContours(eroded,cv2.RETR_EXTERNAL,
                                              cv2.CHAIN_APPROX_NONE)
        [x,y,w,h] = cv2.boundingRect(contours[0])
        roi = thresh[y:y+h,x:x+w]
        if trim:
            ret = self.add_borders(roi)
        else:
            ret = self.add_borders(thresh)
        return ret

    def add_borders(self, image):
        height, width = image.shape
        width_pad = (self.WIDTH - width) / 2.0
        left_pad = int(width_pad)
        if (left_pad != width_pad):
            right_pad = left_pad+1
        else:
            right_pad = left_pad

        height_pad = (self.HEIGHT - height) / 2.0
        top_pad = int(height_pad)
        if (top_pad!=height_pad):
            bottom_pad = top_pad+1
        else:
            bottom_pad = top_pad

        if height_pad > 0 and width_pad > 0:
            dst = cv2.copyMakeBorder(image, top_pad, bottom_pad, left_pad,
                                     right_pad, cv2.BORDER_CONSTANT, value=0)
        else:    
            dst = cv2.resize(image,(self.HEIGHT,self.WIDTH))
            sys.stderr.write("Could not add borders, shape " + str(height)
                             + "," + str(width) + "\n")
        return dst

    def segment(self, im):

        gray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,1,11,2)
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
        thresh = cv2.erode(thresh,kernel,iterations = 1)
        contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,
                                              cv2.CHAIN_APPROX_NONE)
        rois = []
        im2 = np.copy(im)
        for cnt in contours:
            [x,y,w,h] = cv2.boundingRect(cnt)
            if (h<5) or (w<5):
                continue
            cv2.rectangle(im2,(x,y),(x+w,y+h),(0,0,255),2)
            roi = gray[y:y+h,x:x+w]
            rois.append((roi, x))
        ret = map(lambda x: x[0],sorted(rois, key=lambda x: x[1]))
        return ret

    def get_images_from_dir(self, directory):
        train_images_names = os.listdir(directory)
        train_images = []
        train_labels = []
        for filename in train_images_names:
            train_images.append(cv2.imread(directory+"/"+filename))
            m = re.match("(.*)\..*", filename)
            if m:
                base = m.group(1)
                letter = base[0]
                train_labels.append(self.letter_to_number(letter))

        for i in range(len(train_images)):
            train_images[i] = self.clean_image(train_images[i])

        train_arrays = []
        for image in train_images:
            train_arrays.append(np.array(image))

        train_data = np.array(train_arrays)

        images = train_data.reshape(-1,
                                    self.HEIGHT*self.WIDTH).astype(np.float32)
        labels = np.array(train_labels)

        return (images, labels)

    def get_images_from_captcha(self, filename):
        images = self.segment(cv2.imread(filename))

        for i in range(len(images)):
            images[i] = cv2.adaptiveThreshold(
                images[i],255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,1,11,2)
            images[i] = self.add_borders(images[i])

        image_arrays = []
        for image in images:
            image_arrays.append(np.array(image))

        data = np.array(image_arrays)

        ret_images = data.reshape(-1,self.HEIGHT*self.WIDTH).astype(np.float32)
        return ret_images

    def train_from_dir(self, train_dir, datafile=None):
        (train, train_labels) = self.get_images_from_dir(train_dir)
        knn = cv2.KNearest()
        knn.train(train,train_labels)
        if datafile:
            np.save(datafile + "_images", train)
            np.save(datafile + "_labels", train_labels)

        return knn

    def train_from_file(self, train_data_file):
        train = np.load(train_data_file + "/train_captchas_data_images.npy")
        train_labels = np.load(train_data_file +
                               "/train_captchas_data_labels.npy")
        knn = cv2.KNearest()
        knn.train(train,train_labels)

        return knn

    def test_captcha(self, captchafile):
        test = self.get_images_from_captcha(captchafile)
        ret,result,neighbours,dist = self.knn.find_nearest(test,k=1)
        result_labels = []
        for label in result:
            result_labels.append(self.number_to_letter(int(label[0])))
        return "".join(result_labels)

    def test_dir(self, test_dir):
        (test, test_labels) = self.get_images_from_dir(test_dir)
        ret,result,neighbours,dist = self.knn.find_nearest(test,k=2)
        test_letter_labels = []
        for label in test_labels:
            test_letter_labels.append(number_to_letter(label))
        print test_letter_labels
        result_labels = []
        for label in result:
            result_labels.append(number_to_letter(int(label[0])))
        print 'result:\n', result_labels

        l1 = np.array(result_labels)
        l2 = np.array(test_letter_labels)
        matches = l1==l2
        correct = np.count_nonzero(matches)
        accuracy = correct*100.0/result.size
        print accuracy


class CaptchaBreakerWrapper():

    CB = None
    # CAPTCHAS_DIR = "captchas"
    # SOLVED_CAPTCHAS_DIR = "solved_captchas"
    # TRAIN_DATA_PATH = "tra         in_captchas_data"
    CAPTCHAS_DIR = "/tmp/captchas"
    SOLVED_CAPTCHAS_DIR = "/tmp/solved_captchas"
    directory = os.path.dirname(os.path.abspath(__file__))
    TRAIN_DATA_PATH = os.path.join(directory, '..', 'train_captchas_data')

    def solve_captcha(self, image_URL, debug_info=True):

        if not os.path.exists(self.CAPTCHAS_DIR):
            os.makedirs(self.CAPTCHAS_DIR)
        if not os.path.exists(self.SOLVED_CAPTCHAS_DIR):
            os.makedirs(self.SOLVED_CAPTCHAS_DIR)

        m = re.match(".*/(Captcha_.*)",image_URL)
        if not m:
            if debug_info:
                sys.stderr.write("Couldn't extract captcha image name "
                                 "from URL " + image_URL)
            return None

        else:
            image_name = m.group(1)
            urllib.urlretrieve(image_URL, self.CAPTCHAS_DIR + "/" + image_name)
            captcha_text = None

            try:
                if not self.CB:
                    self.CB = CaptchaBreaker(self.TRAIN_DATA_PATH)
                    if debug_info:
                        sys.stderr.write("Training captcha classifier...\n")

                captcha_text = self.CB.test_captcha(self.CAPTCHAS_DIR + "/"
                                                    + image_name)

                urllib.urlretrieve(image_URL, self.SOLVED_CAPTCHAS_DIR + "/"
                                   + captcha_text + ".jpg")
                if debug_info:
                    sys.stderr.write("Solving captcha: " + image_URL +
                                     " with result " + captcha_text + "\n")

            except Exception, e:
                sys.stderr.write("Exception on solving captcha, for captcha "
                                 + self.CAPTCHAS_DIR + "/" + image_name +
                                 "\nException message: " + str(e) + "\n")

            return captcha_text


if __name__=="__main__":
    CW = CaptchaBreakerWrapper()
    # CW.solve_captcha("http://ecx.images-amazon.com/captcha/bfhuzdtn/Captcha_distpnvhaw.jpg", False)
    # CW.solve_captcha("http://ecx.images-amazon.com/captcha/bfhuzdtn/Captcha_distpnvhaw.jpg")
    # CW.solve_captcha("http://ecx.images-amazon.com/captcha/bfhuzdtn/Captcha_distpnvhaw.jpg")
    CW.solve_captcha("https://ipv4.google.com/sorry/image?id=7585877133141730835&hl=ru")