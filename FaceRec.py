from imutils import paths
import face_recognition
import pickle
import cv2
import os

def clearFile(fileName):
    f = open(fileName, "wb+")
    f.seek(0)
    f.close()

class FaceRec:

    def __init__(self, app_root):
        self.APP_ROOT = app_root

    def countFaces(self):
        imagePaths = list(paths.list_images(self.APP_ROOT + 'static/faces'))
        knownEncodings = []
        knownId = []
        for (i, imagePath) in enumerate(imagePaths):
            id = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownId.append(id)
        data = {"encodings": knownEncodings, "names": knownId}
        clearFile(self.APP_ROOT + 'face_enc')
        f = open(self.APP_ROOT + 'face_enc', "wb")
        f.write(pickle.dumps(data))
        f.close()

    def recogniteTheFace(self, img):
        data = pickle.loads(open(self.APP_ROOT + 'face_enc', "rb").read())
        rgb = img
        faces = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb)
        flist = {}
        for (encoding, s_faceLoc) in zip(encodings, faces):
            matches = face_recognition.compare_faces(data["encodings"], encoding)
            name = "Unknown"
            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                    name = max(counts, key=counts.get)
                x1, y1, x2, y2 = s_faceLoc[3], s_faceLoc[0], s_faceLoc[1], s_faceLoc[2]
                flist[name] = [x1, y1, x2, y2]
        id = self.getGoodFace(flist, rgb)
        return id

    def getGoodFace(self, faceList, img):
        height, width = img.shape[:2]
        x0, y0 = height / 2, width / 2
        mn = height ** 2 + width ** 2
        k = -1
        for key in faceList:
            x1, y1, x2, y2 = faceList[key]
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            dist = (x - x0) ** 2 + (y - y0) ** 2
            if mn > dist:
                mn = dist
                k = key
        return k