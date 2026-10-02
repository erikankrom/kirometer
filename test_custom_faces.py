import asyncio
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('custom_faces',ROOT/'crew-app/backend/custom_faces.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def example():
 return {'version':1,'name':'Test','elements':[{'kind':'metric','x':12,'y':52,'w':456,'h':100,'size':4,'color':'purple','value':'remaining'}]}
class ValidationTests(unittest.TestCase):
 def test_valid_and_unknown_commands(self):
  self.assertEqual(f.validate(example()),example())
  for change in ({'firmware':'erase'},{'version':2},{'version':True},{'name':'bad\nname'},{'elements':[]},{'elements':example()['elements']*13}):
   with self.assertRaises(ValueError):f.validate(dict(example(),**change))
 def test_reject_bounds_scripts_assets_and_invented_data(self):
  for change in ({'x':-1},{'y':0},{'w':457},{'h':400},{'x':True},{'kind':'script'},{'color':'url(http://evil)'},{'value':'eval(1)'},{'src':'http://evil'},{'size':9}):
   face=example();face['elements'][0].update(change)
   with self.assertRaises(ValueError):f.validate(face)
 def test_response_strictness(self):
  raw=json.dumps(example())
  self.assertEqual(f.parse_output('banner\n```json\n'+raw+'\n```'),example())
  for value in ('{}',raw+raw,json.dumps(dict(example(),code='danger'))):
   with self.assertRaises(ValueError):f.parse_output(value)
 def test_transport_budget(self):
  face=example();face['elements']*=12
  if len(json.dumps(face,separators=(',',':')))>2000:
   with self.assertRaises(ValueError):f.validate(face)
  wire={'type':'kirometer.usage','protocol':1,'token':'x'*48,'controls':{'seq':1,'custom_face':example()},'credits':[{'used':1,'limit':1000}]}
  self.assertLess(len(json.dumps(wire,separators=(',',':'))),4096)
class FirmwareParityTests(unittest.TestCase):
 def test_same_validation_on_device(self):
  import subprocess
  with tempfile.TemporaryDirectory() as tmp:
   binary=str(Path(tmp)/'validator')
   subprocess.run(['c++','-std=c++17','-I'+str(ROOT/'firmware/.pio/libdeps/waveshare_amoled_216/ArduinoJson/src'),str(ROOT/'tests/custom_face_validator.cpp'),'-o',binary],check=True)
   cases=[example()]
   for key in ('x','y','w','h','size'):
    for value in (True,False,None,-2147483648,-1,0,1,12,51,52,424,456,468,480,2147483647,1.5,'1'):
     face=example();face['elements'][0][key]=value;cases.append(face)
   for key in ('version','name','elements'):
    for value in (None,False,True,1,{},[], 'bad\nname'):
     face=example();face[key]=value;cases.append(face)
   for key in ('kind','color','value'):
    for value in (None,{},[],1,'shell','purple','activity','--','\n','metric\x00evil','purple\x00evil'):
     face=example();face['elements'][0][key]=value;cases.append(face)
   expected=[]
   for face in cases:
    try:f.validate(face);expected.append('yes')
    except (ValueError,TypeError):expected.append('no')
   actual=subprocess.check_output([binary],input='\n'.join(json.dumps(c) for c in cases)+'\n',text=True).splitlines()
   self.assertEqual(actual,expected)
class RouteTests(unittest.IsolatedAsyncioTestCase):
 async def test_save_list_delete_and_rejection(self):
  class Request:
   content_length=0
   def __init__(self,method,path,data=None):self.method=method;self.path=path;self.data=data
   async def json(self):return self.data
  with tempfile.TemporaryDirectory() as tmp:
   ctx=SimpleNamespace(data_dir=tmp)
   response=await f.route(Request('POST','/faces/save',{'face':example()}),ctx)
   self.assertEqual(response.status,200)
   saved=json.loads((Path(tmp)/'custom-faces.json').read_text())
   self.assertEqual(len(saved),1)
   response=await f.route(Request('GET','/faces'),ctx)
   self.assertEqual(len(json.loads(response.text)['faces']),1)
   response=await f.route(Request('POST','/faces/save',{'face':{'code':'bad'}}),ctx)
   self.assertEqual(response.status,400)
   await f.route(Request('POST','/faces/delete',{'id':saved[0]['id']}),ctx)
   self.assertEqual(f.read_faces(ctx),[])
if __name__=='__main__':unittest.main()
