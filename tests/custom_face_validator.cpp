#include <iostream>
#include <string>
#include "../firmware/src/custom_face.h"
int main(){std::string line;while(std::getline(std::cin,line)){JsonDocument doc;auto err=deserializeJson(doc,line);std::cout<<(!err && validateCustomFace(doc.as<JsonVariantConst>())?"yes":"no")<<std::endl;}}
