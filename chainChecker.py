import os
import sys
import shutil
import json
import base64

args = sys.argv

autoFix = False
image_dir = None
image_layer_name = None
vch_dir = None

for arg in args:
    if '--imageStore-path=' in str(arg):
        image_dir = str(arg).split('--imageStore-path=')[1]
    elif '--image-layer=' in str(arg):
        image_layer_name = str(arg).split('--image-layer=')[1]
    elif '--VCH-path=' in str(arg):
        vch_dir = str(arg).split('--VCH-path=')[1]
    elif '--fix' in str(arg):
        autoFix = True
    elif arg != args[0]:
        print('Error parsing argument:', str(arg))
        exit()

if image_dir is None:
    print('Missing required IMAGE STORE PATH using --imageStore-path=')
    exit()

if (image_layer_name is None and vch_dir is not None) or (image_layer_name is not None and vch_dir is None):
    print('Missing required IMAGE LAYER NAME using --image-layer=')
    print('OR')
    print('Missing required VCH FOLDER PATH using --VCH-path=')
    exit()


# ----------------------------------------------------------

class ImageLayer:

    def __init__(self, id):
        self.id = id
        self.filesStatus = False
        self.files = [self.id + '.vmdk', self.id + '-sesparse.vmdk', 'manifest', '/imageMetadata/metaData']
        self.files = [self.id + '.vmdk', 'manifest', 'imageMetadata/metaData']
        self.metadataVMDK = None
        self.metadataImage = None
        self.childAmount = 0

    def getId(self):
        return self.id

    def getFiles(self):
        return self.files

    def getMetadataVMDK(self):
        return self.metadataVMDK

    def setMetadataVMDK(self, metadataVMDK):
        self.metadataVMDK = metadataVMDK

    def getMetadataImage(self):
        return self.metadataImage

    def setMetadataImage(self, metadataImage):
        self.metadataImage = metadataImage

    def getChildAmount(self):
        return self.childAmount

    def setChildAmount(self, amount):
        self.childAmount = amount


class MetadataImage:

    def __init__(self, id, parent):
        self.id = id
        self.parent = parent

    def getId(self):
        return self.id

    def getParent(self):
        return self.parent


class MetadataVMDK:

    def __init__(self, cID, parentCID, parentPath):
        self.CID = cID
        self.ParentCID = parentCID
        self.ParentPath = parentPath

    def getCID(self):
        return self.CID

    def getParentCID(self):
        return self.ParentCID

    def getParentPath(self):
        return self.ParentPath


# ----------------------------------------------------------

imageLayers = []

if image_layer_name is not None:
    print('-------------------------------')
    print('- CHECKING VCH K/V ACCESS     -')
    print('-------------------------------')

    try:
        apiKV_fullpath = vch_dir + 'kvStores/apiKV.dat'
        # Open file
        json_file = open(apiKV_fullpath, 'r')
    except:
        print('Error opening', vch_dir)
        exit()

print('-------------------------------')
print('- CHECKING FILES STRUCTURE    -')
print('-------------------------------')

# Listing all Image Layer folders from DS folder
for dir in os.listdir(image_dir):
    if os.path.isdir(os.path.join(image_dir, dir)):
        imageLayer = ImageLayer(dir)

        for file in imageLayer.getFiles():
            filePath = image_dir + '/' + imageLayer.getId() + '/'
            if not os.path.exists(filePath + file):
                if 'scratch' in filePath and file == 'imageMetadata/metaData':
                    imageLayer.setMetadataImage(MetadataImage('SCRATCH - NO ID', 'SCRATCH - NO PARENT'))
                else:
                    print('Missing file:', filePath + file)
            else:
                if file == imageLayer.getId() + '.vmdk':
                    cID = None
                    parentCID = None
                    parentPath = None

                    with open(filePath + file, 'rb') as f:
                        lines = f.readlines()

                        for line in lines:
                            if 'parentCID=' in str(line):
                                parentCID = str(line).split('parentCID=')[1]
                                parentCID = parentCID.split('\\n')[0]
                            elif 'CID=' in str(line):
                                cID = str(line).split('CID=')[1]
                                cID = cID.split('\\n')[0]
                            elif 'parentFileNameHint=' in str(line):
                                parentPath = str(line).split('parentFileNameHint="')[1]
                                parentPath = parentPath.split('"\\n')[0]

                    imageLayer.setMetadataVMDK(MetadataVMDK(cID, parentCID, parentPath))
                elif file == 'imageMetadata/metaData':
                    id = None
                    parent = None

                    with open(filePath + file, 'rb') as f:
                        line = f.readline()
                        try:
                            temp = str(line).split('{"id":"')[1]
                            id = temp.split('",')[0]
                        except:
                            pass
                        try:
                            temp = temp.split('"parent":"')[1]
                            parent = temp.split('",')[0]
                        except:
                            pass
                    imageLayer.setMetadataImage(MetadataImage(id, parent))

        imageLayers.append(imageLayer)

print('-------------------------------')
print('- ANALYZING                   -')
print('-------------------------------')

# Counting number of childs per layers
for imageLayerParent in imageLayers:
    counterImageLayerChild = 0
    for imageLayerChild in imageLayers:
        if imageLayerChild.getMetadataVMDK().getParentCID() == None:
            print('--- Image Layer Child ParentCID is NULL for {} ---'.format(image_dir + '/' + imageLayerChild.getId()))
        else:
            if imageLayerChild.getMetadataVMDK().getParentCID() == imageLayerParent.getMetadataVMDK().getCID():
                counterImageLayerChild = counterImageLayerChild + 1
    imageLayerParent.setChildAmount(counterImageLayerChild)

# Building Chains, starting from the end
chains = []

for imageLayerChild in imageLayers:
    if imageLayerChild.getChildAmount() == 0:
        chain = [imageLayerChild]
        searchingLayer = imageLayerChild

        while True:
            foundParentLayer = False
            for imageLayerParent in imageLayers:
                if imageLayerChild.getMetadataVMDK().getParentCID() == None:
                    print('--- Image Layer Child ParentCID is NULL for {} ---'.format(image_dir + '/' + imageLayerChild.getId()))
                else:
                    if searchingLayer.getMetadataVMDK().getParentCID() == imageLayerParent.getMetadataVMDK().getCID():
                        chain.append(imageLayerParent)
                        searchingLayer = imageLayerParent
                        foundParentLayer = True
                        break
            if foundParentLayer == False:
                break
        chains.append(chain)

if image_layer_name == None:
    print('--- Checking for Dangling chains ---')
else:
    print('--- Checking for the image layer {} ---'.format(image_layer_name))

scratchLayer = None
for imageLayer in imageLayers:
    if imageLayer.getId() == 'scratch':
        scratchLayer = imageLayer
        break

# Checking chains
for chain in chains:
    # Are we looking for all dangling layers
    if image_layer_name is None:
        if chain[-1].getId() != 'scratch':
            print('*** ERROR: Dangling Layer chain:')
            for layer in chain:
                print(' - layer', layer.getId())
            print('---')
            if autoFix:
                # Fixing dangling layer
                danglingLayer = chain[-1]
                print('FIXING Layer', danglingLayer.getId(), 'to point back to scratch Layer...')
                vmxFilePath = image_dir + '/' + danglingLayer.getId() + '/' + danglingLayer.getId() + '.vmdk'
                with open(vmxFilePath, 'r') as file:
                    fileLines = file.readlines()

                newFileLines = []
                for fileLine in fileLines:
                    if 'parentCID=' in str(fileLine):
                        fileLine = 'parentCID=' + str(scratchLayer.getMetadataVMDK().getCID()) + '\n'
                    elif 'parentFileNameHint=' in str(fileLine):
                        fileLine = 'parentFileNameHint="' + image_dir + '/scratch/scratch.vmdk"\n'
                    newFileLines.append(fileLine)

                print(newFileLines)

                with open(vmxFilePath, 'w') as file:
                    file.writelines(newFileLines)
    # Or we just want to delete one particular container image
    else:
        apiKV_fullpath = vch_dir + 'kvStores/apiKV.dat'
        try:
            # Open file
            json_file = open(apiKV_fullpath, 'r')
        except:
            print('Error opening', vch_dir)
            exit()

        # Convert FileHandler to JSON
        json_file_data = json.load(json_file)

        # Close file
        json_file.close()

        # Extract 'docker.layers' JSON entry, decode BASE64 format, and decode JSON from UTF-8
        json_file_data_docker_images = json_file_data['docker.images']
        json_file_data_docker_layers_decoded = base64.b64decode(json_file_data['docker.layers']).decode('utf8')
        json_file_data_docker_repositories = json_file_data['docker.repositories']

        # Load JSON
        json_docker_layers = json.loads(json_file_data_docker_layers_decoded)

        if chain[0].getId() == image_layer_name:
            print('Found problem container image chain...')
            if autoFix:
                for layer in chain:
                    if layer.getChildAmount() < 2 and layer.getId() != 'scratch':
                        print(' - Deleting layer', layer.getId())
                        image_path_to_delete = image_dir + '/' + layer.getId()
                        shutil.rmtree(image_path_to_delete)
                        json_docker_layers["Layers"].pop(layer.getId())

                # Create output JSON
                json_docker_layers_output = {}

                for apiKV_layer in json_docker_layers["Layers"]:
                    json_docker_layers_output[apiKV_layer] = json_docker_layers["Layers"][apiKV_layer]

                # Recreate JSON Structure
                json_layers_output = {'Layers': json_docker_layers_output}

                # Dump JSON as String
                json_layers_output_dumped = json.dumps(json_layers_output, separators=(',', ':'))

                # Encode JSON to UTF-8, and encode to BASE64
                json_layers_output_dumped_encoded = base64.b64encode(json_layers_output_dumped.encode('utf-8'))

                # Final OUTPUT
                json_output = {'docker.images': json_file_data_docker_images,
                               'docker.layers': json_layers_output_dumped_encoded.decode('utf8'),
                               'docker.repositories': json_file_data_docker_repositories}

                # Dump JSON as String
                dict_output = json.dumps(json_output, separators=(',', ':'))

                # Save file
                output_json_file = open(apiKV_fullpath, 'w')
                output_json_file.write(dict_output)
                output_json_file.close()

            else:
                for layer in chain:
                    print(' - layer', layer.getId(), 'has', layer.getChildAmount(), 'child layer(s)')
                print('---')
