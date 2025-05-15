import sys
import os
from datetime import datetime
import requests
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data import DataSet
from utils.cwlogin import CWLogin

configurations = DataSet.get_schema('otherConfigurations.json')

class CWSchemaBuilder():
    def __init__(self):
        self._connection_params = configurations.get('ServerURL')
        self._housesGroups = configurations.get('housesGroups')
        self._units = []
        self._unitsAndTags = {}

    def _getChildren(self):
        self._login()
        response = requests.get(self._connection_params.get("CWhierarchy"), headers=self._header)

        if response.status_code == 200:
            responsejson = response.json()
            children = responsejson[0]["Children"]
            
            for child in children:
                if child.get('Name') in self._housesGroups.keys():
                    housesSubGroups = self._housesGroups.get(child.get('Name'))
                    if not housesSubGroups:
                        self._units.extend(child.get('Children'))
                    else:
                        children2 = child.get('Children')
                        for child2 in children2:
                            if child2.get('Name') in housesSubGroups:
                                self._units.extend(child2.get('Children'))

                   
    def _getTags(self):
        for unit in self._units:
            unitName = unit.get('Name')
            self._unitsAndTags[unitName] = []
            devices = unit.get('Children')
            for device in devices:
                tags = device.get('Tags')
                if tags:
                    for tag in tags:
                        self._unitsAndTags[unitName].append(tag.get('Id'))


    def _processTagsInfo(self):
        for unit in self._unitsAndTags.keys():
            tags = self._unitsAndTags.get(unit)
            self._unitsAndTags[unit] = {
                "site": "living lab",
                "devices": []
            }
            for tag in tags:
                tagInfo = self._getTagInfo(tag)
                if 'label' in tagInfo:
                    self._unitsAndTags[unit]["devices"].append(tagInfo)
        
        self._unitsAndTags['provider'] = 'Cleanwatts'
        print(json.dumps(self._unitsAndTags, indent=4))

        with open('CWData.json', 'w') as json_file:
            json.dump(self._unitsAndTags, json_file, indent=4)


    def _getTagInfo(self, tagId):
        tagInfo = {}
        self._login()
        tagType = requests.get(f'{self._connection_params.get("TagInfo")}{tagId}?include=[TagType]', headers=self._header).json().get('TagType')
        tagInfo['id'] = str(tagId)
        tagInfo['type'] = tagType.get('Description')
        mu = requests.get(f'{self._connection_params.get("MeasurementUnit")}', headers=self._header).json()
        for unit in mu:
            if unit.get('Id') == tagType.get('MeasurementUnit'):
                tagInfo['measurementUnit'] = unit.get('Name')

        label = configurations.get('labelsMap').get(tagInfo.get('type'))
        if label:
            tagInfo['label'] = label
            
        return tagInfo

    def run(self):
        self._getChildren()
        self._getTags()
        self._processTagsInfo()

    def _login(self):
        token = CWLogin.login() 
        self._header = {'Authorization': f"CW {token}"}
        self._session_time = datetime.now().timestamp()


def main():
    schemaBuilder = CWSchemaBuilder()
    schemaBuilder.run()

  
if __name__ == "__main__":
    main()