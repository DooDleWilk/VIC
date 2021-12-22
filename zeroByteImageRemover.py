import os
import sys
import subprocess

args = sys.argv

autoFix = False
projectName = None
isHarborRunning = True
dataPath = '/storage/data/harbor/registry/docker/registry/'
dataRepositoriesPath = dataPath + 'v2/repositories/'
dataBlobsPath = dataPath + 'v2/blobs/sha256/'

for arg in args:
    if '--project=' in str(arg):
        projectName = str(arg).split('--project=')[1]
    elif '--fix' in str(arg):
        autoFix = True
        if 'harbor' not in subprocess.check_output('docker ps', shell=True):
            isHarborRunning = False
    elif arg != args[0]:
        print('Error parsing argument:', str(arg))
        exit()

# ----------------------------------------------------------

class Project:

    def __init__(self, name):
        self.name = name
        self.images = []

    def getName(self):
        return self.name

    def getImages(self):
        return self.images

    def addImage(self, image):
        self.images.append(image)



class Image:

    def __init__(self, name):
        self.name = name
        self.tag = None
        self.currentLinkFilePath = None
        self.digest = None
        self.blobFileExists = False

    def getName(self):
        return self.name

    def getTag(self):
        return self.tag

    def setTag(self, tag):
        self.tag = tag

    def getCurrentLinkFilePath(self):
        return self.currentLinkFilePath

    def setCurrentLinkFilePath(self, path):
        self.currentLinkFilePath = path

    def getDigest(self):
        return self.digest

    def setDigest(self, digest):
        self.digest = digest

    def getBlobFileExists(self):
        return self.blobFileExists

    def setBlobFileExists(self, flag):
        self.blobFileExists = flag

# ----------------------------------------------------------

projects=[]

print('-------------------------------')
print('- CHECKING PROJECTS STRUCTURE -')
print('-------------------------------')

# Listing all PROJECTS folders
for dir in os.listdir(dataRepositoriesPath):
    if os.path.isdir(os.path.join(dataRepositoriesPath, dir)):
        project = Project(dir)

        # List all IMAGES in that PROJECT
        for imageDir in os.listdir(dataRepositoriesPath + dir):
            if os.path.isdir(os.path.join(dataRepositoriesPath + dir, imageDir)):
                imagePath = dataRepositoriesPath + dir + '/' + imageDir

                # List all TAGS per IMAGE in that PROJECT
                for imageTagDir in os.listdir(imagePath + '/_manifests/tags/'):
                    if os.path.isdir(os.path.join(imagePath + '/_manifests/tags/', imageTagDir)):
                        imageTagPath = imagePath + '/_manifests/tags/' + imageTagDir
                        image = Image(imageDir)

                        image.setTag(imageTagDir)

                        # Check that the /current/link file exists
                        if os.path.exists(imageTagPath + '/current/link'):
                            image.setCurrentLinkFilePath(imageTagPath + '/current/link')

                            with open(image.getCurrentLinkFilePath(), 'rb') as f:
                                lines = f.readlines()
                                digest = lines[0].replace('sha256:', '', 1)
                                digest = digest.replace('\n', '', 1)
                                image.setDigest(digest)

                            # Check that the BLOB file /data exists
                            if os.path.exists(dataBlobsPath + image.getDigest()[0:2] + '/' + image.getDigest() + '/data'):
                                image.setBlobFileExists(True)

                        project.addImage(image)

        projects.append(project)

print('-------------------------------')
print('- ANALYZING                   -')
print('-------------------------------')

print('Image(s) to delete...')

for project in projects:
    if projectName is None or project.getName() == projectName:
        print('- Project: ' + project.getName())

        for projectImage in project.getImages():
            if projectImage.getCurrentLinkFilePath() == None or projectImage.getBlobFileExists() == False:
                print('--- Image: ' + projectImage.getName() + ':' + projectImage.getTag())
                if projectImage.getCurrentLinkFilePath() == None:
                    print('    Missing /current/link file...')
                elif projectImage.getBlobFileExists() == False:
                    print('    Missing BLOB data...')

                if autoFix == True:
                    if isHarborRunning == False:
                        folderToDelete = dataRepositoriesPath + project.getName() + '/' + projectImage.getName() + '/_manifests/tags/' + projectImage.getTag()
                        print('Deleting Folder: ' + folderToDelete)
                        for root, dirs, files in os.walk(folderToDelete, topdown=False):
                            for name in files:
                                os.remove(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(os.path.join(root, folderToDelete))
                        print(projectImage.getName() + ':' + projectImage.getTag() + ' deleted!')
                    elif isHarborRunning == True:
                        print('Harbor containers still running, not deleting...')
                        print('You must stop Harbor containers with "systemctl stop harbor" first!')

        # If checking just one project, we break to exit the FOR loop
        if project.getName() == projectName:
            break
