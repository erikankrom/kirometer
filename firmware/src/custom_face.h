#pragma once
#include <ArduinoJson.h>
#include <cstring>
// A deliberately finite, data-only protocol. No expressions, assets or callbacks.
inline bool faceAscii(JsonVariantConst v,size_t lo,size_t hi){if(!v.is<const char*>())return false;JsonString text=v.as<JsonString>();const char* s=text.c_str();size_t n=text.size();if(n<lo||n>hi)return false;for(size_t i=0;i<n;i++)if(s[i]<32||s[i]>126)return false;return true;}
inline bool faceOneOf(const char* value,const char* list){if(!value)return false;char copy[160];strncpy(copy,list,sizeof(copy));copy[159]=0;for(char* s=strtok(copy,"|");s;s=strtok(nullptr,"|"))if(!strcmp(value,s))return true;return false;}
inline bool validateCustomFace(JsonVariantConst face){
 if(!face.is<JsonObjectConst>()||face.as<JsonObjectConst>().size()!=3||!face["version"].is<int>()||face["version"].as<int>()!=1||!faceAscii(face["name"],1,28)||measureJson(face)>2000)return false;
 if(!face["elements"].is<JsonArrayConst>())return false;auto elements=face["elements"].as<JsonArrayConst>();if(elements.size()<1||elements.size()>12)return false;
 for(JsonVariantConst e:elements){
  if(!e.is<JsonObjectConst>()||e.as<JsonObjectConst>().size()!=8)return false;
  if(!faceAscii(e["kind"],1,8)||!faceAscii(e["color"],1,8)||!faceOneOf(e["kind"],"text|metric|bar|panel|ghost")||!faceOneOf(e["color"],"white|muted|purple|green|red|panel")||!faceAscii(e["value"],0,40))return false;
  for(const char* k:{"x","y","w","h","size"})if(!e[k].is<int>())return false;
  int x=e["x"],y=e["y"],w=e["w"],h=e["h"],s=e["size"];
  if(x<12||x>=468||y<52||y>=424||w<1||w>456||h<1||h>372||x+w>468||y+h>424||s<1||s>4)return false;
  const char* kind=e["kind"];const char* value=e["value"];
  if(!strcmp(kind,"metric")&&!faceOneOf(value,"used|limit|remaining|overage|percent|plan|reset|activity|battery|sessions|messages|tools"))return false;
  if(!strcmp(kind,"bar")&&strcmp(value,"percent"))return false;
  if((!strcmp(kind,"panel")||!strcmp(kind,"ghost"))&&strlen(value))return false;
 }
 return true;
}
